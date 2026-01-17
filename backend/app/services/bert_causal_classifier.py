# backend/app/services/bert_causal_classifier.py
"""
BERT-based Causal Classifier - Week 124

Full BERT integration for causality detection in requirements.

Based on:
- Paper: arXiv:2101.10766 - REFSQ 2021
- Repository: github.com/fischJan/CiRA

Features:
- BERT model loading from HuggingFace
- Fine-tuning on project-specific data
- Confidence calibration (temperature scaling)
- Optional POS tag features
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

logger = logging.getLogger(__name__)


# ============== DATA CLASSES ==============

@dataclass
class ClassificationResult:
    """Result of causality classification."""
    sentence: str
    is_causal: bool
    confidence: float
    probability_causal: float
    probability_non_causal: float
    markers: List[str] = field(default_factory=list)
    pos_features: Optional[Dict[str, Any]] = None
    logits: Optional[List[float]] = None


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""
    model_name: str
    base_model: str
    trained_on: str
    num_training_samples: int
    accuracy: float
    f1_score: float
    created_at: str
    config: Dict[str, Any]


# ============== CUSTOM DATASET ==============

class CausalityDataset(Dataset):
    """Dataset for causality classification."""

    def __init__(self, sentences: List[str], labels: Optional[List[int]] = None,
                 tokenizer=None, max_length: int = 128):
        self.sentences = sentences
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.sentences)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sentence = self.sentences[idx]

        encoding = self.tokenizer(
            sentence,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
        }

        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)

        return item


# ============== BERT CLASSIFIER MODEL ==============

class BERTCausalityModel(nn.Module):
    """
    BERT model for causality classification.

    Architecture:
    - BERT encoder (bert-base-cased or fine-tuned)
    - Dropout layer
    - Linear classifier (2 classes: causal/non-causal)
    """

    def __init__(self, model_name: str = "bert-base-cased", num_labels: int = 2,
                 dropout_rate: float = 0.3):
        super().__init__()

        from transformers import BertModel

        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)
        self.num_labels = num_labels

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor,
                labels: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)

        # Use [CLS] token representation
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits.view(-1, self.num_labels), labels.view(-1))

        return {
            "loss": loss,
            "logits": logits,
            "hidden_states": outputs.last_hidden_state,
        }


# ============== MAIN CLASSIFIER ==============

class BERTCausalClassifier:
    """
    Complete BERT-based causality classifier.

    Provides:
    - Model loading (pre-trained or fine-tuned)
    - Batch inference
    - Fine-tuning on custom data
    - Confidence calibration
    - Model saving/loading
    """

    def __init__(
        self,
        model_name: str = "bert-base-cased",
        model_path: Optional[str] = None,
        device: str = "auto",
        max_length: int = 128,
        batch_size: int = 16,
        temperature: float = 1.0
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.max_length = max_length
        self.batch_size = batch_size
        self.temperature = temperature

        # Determine device
        if device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        self.model: Optional[BERTCausalityModel] = None
        self.tokenizer = None
        self.is_loaded = False
        self.metadata: Optional[ModelMetadata] = None

        # Causal markers for rule-based fallback
        self.causal_markers = [
            "if", "when", "because", "since", "therefore", "hence", "given",
            "where", "whose", "in order to", "in the case of", "due to",
            "needed", "require", "required", "during", "in case of", "while",
            "thus", "as", "except", "forced by", "only for", "within", "after",
            "whenever", "which", "before", "allows", "allow", "unless",
            "prior to", "as long as", "depending on", "depends on", "result in",
            "increases", "lead to", "thereby", "cause", "in the event", "once",
            "in such cases", "throughout", "improve", "to that end", "to this end",
            "so that", "provided that", "on condition that"
        ]

        logger.info(f"BERTCausalClassifier initialized (device={self.device})")

    async def load_model(self) -> bool:
        """
        Load the BERT model for causality classification.

        Loads from:
        1. Fine-tuned model path (if specified)
        2. Pre-trained BERT from HuggingFace
        """
        try:
            from transformers import BertTokenizer

            logger.info(f"Loading BERT model: {self.model_name}")

            # Load tokenizer
            self.tokenizer = BertTokenizer.from_pretrained(self.model_name)

            # Load model
            if self.model_path and os.path.exists(self.model_path):
                # Load fine-tuned model
                logger.info(f"Loading fine-tuned model from: {self.model_path}")
                self.model = BERTCausalityModel(model_name=self.model_name)
                state_dict = torch.load(
                    os.path.join(self.model_path, "model.pt"),
                    map_location=self.device
                )
                self.model.load_state_dict(state_dict)

                # Load metadata if exists
                metadata_path = os.path.join(self.model_path, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        meta_dict = json.load(f)
                        self.metadata = ModelMetadata(**meta_dict)
            else:
                # Load pre-trained model
                logger.info(f"Loading pre-trained BERT from HuggingFace")
                self.model = BERTCausalityModel(model_name=self.model_name)

            self.model = self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True

            logger.info(f"BERT model loaded successfully on {self.device}")
            return True

        except ImportError as e:
            logger.warning(f"Transformers library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            return False

    async def predict(self, sentences: List[str]) -> List[ClassificationResult]:
        """
        Predict causality for a list of sentences.

        Uses BERT if loaded, otherwise falls back to rule-based.
        """
        if not self.is_loaded or self.model is None:
            logger.warning("BERT model not loaded, using rule-based fallback")
            return await self._rule_based_predict(sentences)

        try:
            return await self._bert_predict(sentences)
        except Exception as e:
            logger.error(f"BERT prediction failed: {e}, using rule-based fallback")
            return await self._rule_based_predict(sentences)

    async def _bert_predict(self, sentences: List[str]) -> List[ClassificationResult]:
        """Run BERT inference on sentences."""
        results = []

        # Create dataset and dataloader
        dataset = CausalityDataset(
            sentences=sentences,
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        self.model.eval()
        all_logits = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]

                # Apply temperature scaling for calibration
                if self.temperature != 1.0:
                    logits = logits / self.temperature

                all_logits.append(logits.cpu())

        # Concatenate all logits
        all_logits = torch.cat(all_logits, dim=0)

        # Convert to probabilities
        probabilities = F.softmax(all_logits, dim=-1)

        # Create results
        for i, sentence in enumerate(sentences):
            probs = probabilities[i].numpy()
            is_causal = probs[1] > probs[0]  # Class 1 = causal
            confidence = float(max(probs))

            # Detect markers for additional context
            markers = self._detect_markers(sentence)

            results.append(ClassificationResult(
                sentence=sentence,
                is_causal=bool(is_causal),
                confidence=confidence,
                probability_causal=float(probs[1]),
                probability_non_causal=float(probs[0]),
                markers=markers,
                logits=all_logits[i].tolist()
            ))

        return results

    async def _rule_based_predict(self, sentences: List[str]) -> List[ClassificationResult]:
        """
        Rule-based causality detection as fallback.

        Uses causal markers to detect causality patterns.
        """
        results = []

        for sentence in sentences:
            markers = self._detect_markers(sentence)
            is_causal = len(markers) > 0

            # Calculate confidence based on marker count and type
            if is_causal:
                strong_markers = ["if", "when", "because", "therefore", "causes", "leads to"]
                strong_count = sum(1 for m in markers if m in strong_markers)
                confidence = min(0.5 + (strong_count * 0.15) + (len(markers) * 0.05), 0.85)
            else:
                confidence = 0.6

            results.append(ClassificationResult(
                sentence=sentence,
                is_causal=is_causal,
                confidence=confidence,
                probability_causal=confidence if is_causal else 1 - confidence,
                probability_non_causal=1 - confidence if is_causal else confidence,
                markers=markers
            ))

        return results

    def _detect_markers(self, sentence: str) -> List[str]:
        """Detect causal markers in a sentence."""
        sentence_lower = sentence.lower()
        found_markers = []

        for marker in self.causal_markers:
            # Check for whole word match
            import re
            pattern = r'\b' + re.escape(marker) + r'\b'
            if re.search(pattern, sentence_lower):
                found_markers.append(marker)

        return found_markers

    # ============== FINE-TUNING ==============

    async def fine_tune(
        self,
        train_sentences: List[str],
        train_labels: List[int],
        val_sentences: Optional[List[str]] = None,
        val_labels: Optional[List[int]] = None,
        epochs: int = 3,
        learning_rate: float = 2e-5,
        warmup_steps: int = 0,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune the model on project-specific data.

        Args:
            train_sentences: Training sentences
            train_labels: Labels (0=non-causal, 1=causal)
            val_sentences: Validation sentences
            val_labels: Validation labels
            epochs: Number of training epochs
            learning_rate: Learning rate
            warmup_steps: Warmup steps for scheduler
            save_path: Path to save fine-tuned model

        Returns:
            Training results including accuracy and loss
        """
        if not self.is_loaded:
            await self.load_model()

        from torch.optim import AdamW
        from transformers import get_linear_schedule_with_warmup

        logger.info(f"Starting fine-tuning with {len(train_sentences)} samples")

        # Create datasets
        train_dataset = CausalityDataset(
            sentences=train_sentences,
            labels=train_labels,
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

        val_loader = None
        if val_sentences and val_labels:
            val_dataset = CausalityDataset(
                sentences=val_sentences,
                labels=val_labels,
                tokenizer=self.tokenizer,
                max_length=self.max_length
            )
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        # Setup optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        # Training loop
        training_history = []
        best_val_accuracy = 0.0

        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            correct = 0
            total = 0

            for batch in train_loader:
                optimizer.zero_grad()

                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                loss = outputs["loss"]
                logits = outputs["logits"]

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

                total_loss += loss.item()
                predictions = torch.argmax(logits, dim=-1)
                correct += (predictions == labels).sum().item()
                total += labels.size(0)

            train_accuracy = correct / total
            avg_loss = total_loss / len(train_loader)

            # Validation
            val_accuracy = 0.0
            if val_loader:
                val_accuracy = await self._evaluate(val_loader)

                if val_accuracy > best_val_accuracy:
                    best_val_accuracy = val_accuracy
                    if save_path:
                        await self.save_model(save_path)

            epoch_results = {
                "epoch": epoch + 1,
                "train_loss": avg_loss,
                "train_accuracy": train_accuracy,
                "val_accuracy": val_accuracy,
            }
            training_history.append(epoch_results)

            logger.info(
                f"Epoch {epoch + 1}/{epochs}: "
                f"loss={avg_loss:.4f}, train_acc={train_accuracy:.4f}, val_acc={val_accuracy:.4f}"
            )

        # Final save if no validation
        if save_path and not val_loader:
            await self.save_model(save_path)

        # Calculate F1 score on validation
        f1_score = 0.0
        if val_loader:
            f1_score = await self._calculate_f1(val_loader)

        results = {
            "epochs": epochs,
            "final_train_accuracy": training_history[-1]["train_accuracy"],
            "final_val_accuracy": training_history[-1]["val_accuracy"],
            "best_val_accuracy": best_val_accuracy,
            "f1_score": f1_score,
            "training_history": training_history,
            "saved_to": save_path,
        }

        logger.info(f"Fine-tuning complete. Best val accuracy: {best_val_accuracy:.4f}")
        return results

    async def _evaluate(self, dataloader: DataLoader) -> float:
        """Evaluate model on a dataloader."""
        self.model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                predictions = torch.argmax(outputs["logits"], dim=-1)

                correct += (predictions == labels).sum().item()
                total += labels.size(0)

        return correct / total if total > 0 else 0.0

    async def _calculate_f1(self, dataloader: DataLoader) -> float:
        """Calculate F1 score on a dataloader."""
        self.model.eval()
        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                predictions = torch.argmax(outputs["logits"], dim=-1)

                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # Calculate F1
        from sklearn.metrics import f1_score
        return f1_score(all_labels, all_predictions, average="macro")

    # ============== MODEL PERSISTENCE ==============

    async def save_model(self, path: str) -> None:
        """Save the model and metadata to disk."""
        os.makedirs(path, exist_ok=True)

        # Save model state
        model_path = os.path.join(path, "model.pt")
        torch.save(self.model.state_dict(), model_path)

        # Save tokenizer
        self.tokenizer.save_pretrained(path)

        # Save metadata
        metadata = {
            "model_name": self.model_name,
            "base_model": self.model_name,
            "trained_on": datetime.now(timezone.utc).isoformat(),
            "num_training_samples": 0,  # Updated during fine-tuning
            "accuracy": 0.0,
            "f1_score": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": {
                "max_length": self.max_length,
                "temperature": self.temperature,
            }
        }

        metadata_path = os.path.join(path, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to: {path}")

    # ============== CONFIDENCE CALIBRATION ==============

    async def calibrate_temperature(
        self,
        val_sentences: List[str],
        val_labels: List[int]
    ) -> float:
        """
        Calibrate confidence using temperature scaling.

        Finds optimal temperature to make probabilities match
        actual correctness frequencies.

        Returns the optimal temperature.
        """
        if not self.is_loaded:
            await self.load_model()

        logger.info("Calibrating confidence temperature...")

        # Get logits for validation set
        dataset = CausalityDataset(
            sentences=val_sentences,
            labels=val_labels,
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        all_logits = []
        all_labels = []

        self.model.eval()
        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"]

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                all_logits.append(outputs["logits"].cpu())
                all_labels.append(labels)

        logits = torch.cat(all_logits, dim=0)
        labels = torch.cat(all_labels, dim=0)

        # Find optimal temperature using grid search
        best_temp = 1.0
        best_nll = float("inf")

        for temp in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
            scaled_logits = logits / temp
            probs = F.softmax(scaled_logits, dim=-1)

            # Calculate negative log likelihood
            nll = F.nll_loss(probs.log(), labels)

            if nll < best_nll:
                best_nll = nll
                best_temp = temp

        self.temperature = best_temp
        logger.info(f"Optimal temperature found: {best_temp}")

        return best_temp


# ============== POS TAGGER INTEGRATION ==============

class POSTagger:
    """
    Optional POS (Part-of-Speech) tagger for enhanced features.

    Uses spaCy for POS tagging when available.
    """

    def __init__(self):
        self.nlp = None
        self.is_loaded = False

    async def load(self) -> bool:
        """Load spaCy model for POS tagging."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.is_loaded = True
            logger.info("spaCy POS tagger loaded")
            return True
        except ImportError:
            logger.warning("spaCy not installed, POS features disabled")
            return False
        except OSError:
            logger.warning("spaCy model not found, run: python -m spacy download en_core_web_sm")
            return False

    async def get_pos_features(self, sentence: str) -> Dict[str, Any]:
        """Extract POS tag features from a sentence."""
        if not self.is_loaded:
            return {}

        doc = self.nlp(sentence)

        # Extract features
        pos_counts = {}
        dep_patterns = []

        for token in doc:
            pos = token.pos_
            pos_counts[pos] = pos_counts.get(pos, 0) + 1

            # Look for causal dependency patterns
            if token.dep_ in ["mark", "advcl", "ccomp"]:
                dep_patterns.append({
                    "text": token.text,
                    "dep": token.dep_,
                    "head": token.head.text,
                })

        return {
            "pos_counts": pos_counts,
            "dep_patterns": dep_patterns,
            "has_subordinate_clause": any(t.dep_ == "advcl" for t in doc),
            "has_conditional_marker": any(t.text.lower() in ["if", "when", "unless"] for t in doc),
        }

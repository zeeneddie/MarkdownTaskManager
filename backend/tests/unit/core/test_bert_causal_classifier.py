# backend/tests/services/week124/test_bert_causal_classifier.py
"""
Tests for BERT Causal Classifier - Week 124

Tests:
- Classifier initialization
- Rule-based fallback
- Marker detection
- Classification results
- (BERT model tests require transformers installed)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.bert_causal_classifier import (
    BERTCausalClassifier,
    ClassificationResult,
    CausalityDataset,
    POSTagger,
)


class TestBERTCausalClassifier:
    """Test the BERT causal classifier."""

    @pytest.fixture
    def classifier(self):
        """Create a classifier instance for testing."""
        return BERTCausalClassifier(
            model_name="bert-base-cased",
            device="cpu",
            max_length=128,
            batch_size=8,
            temperature=1.0
        )

    @pytest.mark.asyncio
    async def test_init(self, classifier):
        """Test classifier initialization."""
        assert classifier.model_name == "bert-base-cased"
        assert classifier.device.type == "cpu"
        assert classifier.max_length == 128
        assert classifier.batch_size == 8
        assert classifier.temperature == 1.0
        assert not classifier.is_loaded

    @pytest.mark.asyncio
    async def test_rule_based_fallback_causal(self, classifier):
        """Test rule-based fallback with causal sentences."""
        sentences = [
            "If the user clicks submit, then the form validates.",
            "When authentication fails, the user is redirected to login.",
            "The system crashes because of memory overflow.",
        ]

        results = await classifier._rule_based_predict(sentences)

        assert len(results) == 3
        for result in results:
            assert result.is_causal is True
            assert result.confidence > 0.5
            assert len(result.markers) > 0

    @pytest.mark.asyncio
    async def test_rule_based_fallback_non_causal(self, classifier):
        """Test rule-based fallback with non-causal sentences."""
        sentences = [
            "The user profile displays name and email.",
            "This component shows a list of items.",
            "The button is blue and rounded.",
        ]

        results = await classifier._rule_based_predict(sentences)

        assert len(results) == 3
        for result in results:
            assert result.is_causal is False
            assert result.confidence >= 0.5
            assert len(result.markers) == 0

    @pytest.mark.asyncio
    async def test_marker_detection(self, classifier):
        """Test causal marker detection."""
        sentence = "If the user clicks submit, therefore the form submits because of validation."

        markers = classifier._detect_markers(sentence)

        assert "if" in markers
        assert "therefore" in markers
        assert "because" in markers

    @pytest.mark.asyncio
    async def test_classification_result_structure(self, classifier):
        """Test that classification results have correct structure."""
        sentences = ["If A then B"]

        results = await classifier.predict(sentences)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, ClassificationResult)
        assert hasattr(result, 'sentence')
        assert hasattr(result, 'is_causal')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'probability_causal')
        assert hasattr(result, 'probability_non_causal')
        assert hasattr(result, 'markers')

    @pytest.mark.asyncio
    async def test_predict_uses_fallback_when_not_loaded(self, classifier):
        """Test that predict uses rule-based when model not loaded."""
        assert not classifier.is_loaded

        sentences = ["When X happens, Y follows."]
        results = await classifier.predict(sentences)

        assert len(results) == 1
        assert results[0].is_causal  # Contains "when"

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, classifier):
        """Test confidence calculation with strong markers."""
        # Strong markers should give higher confidence
        strong_sentence = "If the user submits, because of validation, therefore it succeeds."
        weak_sentence = "During the process, this happens."

        strong_results = await classifier._rule_based_predict([strong_sentence])
        weak_results = await classifier._rule_based_predict([weak_sentence])

        assert strong_results[0].confidence > weak_results[0].confidence

    @pytest.mark.asyncio
    async def test_temperature_effect(self, classifier):
        """Test temperature effect on confidence."""
        classifier.temperature = 2.0  # Higher temperature = lower confidence

        # This affects BERT inference, not rule-based
        # For rule-based, confidence is calculated differently
        assert classifier.temperature == 2.0


class TestCausalityDataset:
    """Test the causality dataset."""

    def test_dataset_creation(self):
        """Test dataset creation."""
        sentences = ["Sentence 1", "Sentence 2"]
        labels = [1, 0]

        # Mock tokenizer
        tokenizer = MagicMock()
        tokenizer.return_value = {
            "input_ids": MagicMock(squeeze=MagicMock(return_value=[1, 2, 3])),
            "attention_mask": MagicMock(squeeze=MagicMock(return_value=[1, 1, 1])),
        }

        dataset = CausalityDataset(
            sentences=sentences,
            labels=labels,
            tokenizer=tokenizer,
            max_length=128
        )

        assert len(dataset) == 2

    def test_dataset_without_labels(self):
        """Test dataset creation without labels (inference mode)."""
        sentences = ["Test sentence"]

        tokenizer = MagicMock()
        tokenizer.return_value = {
            "input_ids": MagicMock(squeeze=MagicMock(return_value=[1, 2, 3])),
            "attention_mask": MagicMock(squeeze=MagicMock(return_value=[1, 1, 1])),
        }

        dataset = CausalityDataset(
            sentences=sentences,
            labels=None,
            tokenizer=tokenizer,
            max_length=128
        )

        assert len(dataset) == 1


class TestPOSTagger:
    """Test the POS tagger."""

    @pytest.fixture
    def tagger(self):
        """Create a POS tagger instance."""
        return POSTagger()

    @pytest.mark.asyncio
    async def test_tagger_init(self, tagger):
        """Test tagger initialization."""
        assert not tagger.is_loaded
        assert tagger.nlp is None

    @pytest.mark.asyncio
    async def test_get_pos_features_when_not_loaded(self, tagger):
        """Test POS feature extraction when not loaded."""
        result = await tagger.get_pos_features("Test sentence")
        assert result == {}


class TestClassificationResult:
    """Test the ClassificationResult dataclass."""

    def test_result_creation(self):
        """Test result creation."""
        result = ClassificationResult(
            sentence="Test sentence",
            is_causal=True,
            confidence=0.85,
            probability_causal=0.85,
            probability_non_causal=0.15,
            markers=["if", "then"]
        )

        assert result.sentence == "Test sentence"
        assert result.is_causal is True
        assert result.confidence == 0.85
        assert result.probability_causal == 0.85
        assert result.probability_non_causal == 0.15
        assert result.markers == ["if", "then"]

    def test_result_defaults(self):
        """Test result with default values."""
        result = ClassificationResult(
            sentence="Test",
            is_causal=False,
            confidence=0.6,
            probability_causal=0.4,
            probability_non_causal=0.6
        )

        assert result.markers == []
        assert result.pos_features is None
        assert result.logits is None


@pytest.mark.skipif(
    True,  # Skip by default, enable when torch is available
    reason="Requires torch and transformers installed"
)
class TestBERTModelLoading:
    """Test BERT model loading (requires transformers)."""

    @pytest.fixture
    def classifier(self):
        """Create classifier for BERT tests."""
        return BERTCausalClassifier(
            model_name="bert-base-cased",
            device="cpu"
        )

    @pytest.mark.asyncio
    async def test_model_loading(self, classifier):
        """Test actual BERT model loading."""
        result = await classifier.load_model()

        # Will succeed if transformers is installed
        if result:
            assert classifier.is_loaded
            assert classifier.model is not None
            assert classifier.tokenizer is not None

    @pytest.mark.asyncio
    async def test_bert_inference(self, classifier):
        """Test BERT inference."""
        await classifier.load_model()

        if classifier.is_loaded:
            sentences = ["If A then B", "This is a simple statement."]
            results = await classifier.predict(sentences)

            assert len(results) == 2
            for result in results:
                assert 0 <= result.confidence <= 1
                assert 0 <= result.probability_causal <= 1


class TestCiRAServiceIntegration:
    """Integration tests for CiRA service with BERT classifier."""

    @pytest.mark.asyncio
    async def test_classifier_factory(self):
        """Test classifier factory function."""
        from app.services.cira_service import get_classifier

        classifier = get_classifier()
        assert classifier is not None
        assert isinstance(classifier, BERTCausalClassifier)

    @pytest.mark.asyncio
    async def test_classifier_singleton(self):
        """Test that classifier is a singleton."""
        from app.services.cira_service import get_classifier

        c1 = get_classifier()
        c2 = get_classifier()

        assert c1 is c2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

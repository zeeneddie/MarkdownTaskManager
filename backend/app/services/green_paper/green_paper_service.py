"""
Green-Paper Workflow Service

Handles business logic for MarQed green-paper sessions:
- Session creation and management
- Answer submission and validation
- Constitution generation (via Peter agent)
- Specification generation (via Felix agent)
- Progressive validation checkpoints
"""

from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Type alias for flexible project ID
ProjectId = Union[str, int, UUID]

# TODO: Import models when created
# from app.models.green_paper import GreenPaperSession, Constitution, Specification
# from app.models.project import Project
from app.services.agent_service import AgentService
from app.services.chroma_service import ChromaService


class GreenPaperService:
    """Service for managing MarQed green-paper workflow."""

    def __init__(
        self,
        db: AsyncSession,
        agent_service: AgentService,
        chroma_service: ChromaService
    ):
        self.db = db
        self.agent_service = agent_service
        self.chroma_service = chroma_service

    # ========== Session Management ==========

    async def start_session(
        self,
        project_id: ProjectId,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new MarQed green-paper session.

        Args:
            project_id: The project ID (string, int, or UUID)
            metadata: Optional session metadata

        Returns:
            Session data with 6 questions

        Raises:
            ValueError: If project not found or invalid status
            ConflictError: If active session already exists
        """
        from app.models.green_paper import GreenPaperSession, SessionStatus

        # Check for existing active session
        result = await self.db.execute(
            select(GreenPaperSession).where(
                GreenPaperSession.project_id == str(project_id),
                GreenPaperSession.status == SessionStatus.IN_PROGRESS
            )
        )
        existing_session = result.scalar_one_or_none()

        if existing_session:
            raise ValueError(f"Active green-paper session already exists for project {project_id}")

        # Create new session
        session = GreenPaperSession(
            project_id=str(project_id),
            session_type="green-paper",
            status=SessionStatus.IN_PROGRESS,
            current_question=1,
            total_questions=6,
            progress_percentage=0,
            generation_metadata=metadata or {}
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return {
            "session_id": session.id,
            "project_id": session.project_id,
            "status": session.status,
            "current_question": session.current_question,
            "progress_percentage": session.progress_percentage,
            "created_at": session.created_at.isoformat(),
            "questions": await self.get_questions()
        }

    async def get_session(
        self,
        session_id: UUID,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Retrieve session status and answers.

        Args:
            session_id: The session UUID
            project_id: Optional project UUID (for additional validation)

        Returns:
            Session data with current progress

        Raises:
            NotFoundError: If session not found
        """
        from app.models.green_paper import GreenPaperSession, Answer

        # Get session - project_id is optional for flexibility
        if project_id:
            result = await self.db.execute(
                select(GreenPaperSession).where(
                    GreenPaperSession.id == session_id,
                    GreenPaperSession.project_id == str(project_id)
                )
            )
        else:
            result = await self.db.execute(
                select(GreenPaperSession).where(
                    GreenPaperSession.id == session_id
                )
            )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get all answers
        answers_result = await self.db.execute(
            select(Answer).where(
                Answer.session_id == session_id
            ).order_by(Answer.question_number)
        )
        answers = answers_result.scalars().all()

        # Format answers
        answers_data = [
            {
                "question_number": a.question_number,
                "answer": a.answer,
                "is_required": bool(a.is_required),
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat()
            }
            for a in answers
        ]

        # Calculate progress
        progress = await self.calculate_progress(session_id)

        return {
            "session_id": session.id,
            "project_id": session.project_id,
            "status": session.status,
            "current_question": session.current_question,
            "progress_percentage": session.progress_percentage,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "answers": answers_data,
            "progress": progress,
            "questions": await self.get_questions()
        }

    async def get_questions(self) -> List[Dict[str, Any]]:
        """
        Get the 6 MarQed green-paper questions.

        Returns:
            List of question dictionaries
        """
        return [
            {
                "question_number": 1,
                "question_text": "What problem does this project solve?",
                "question_type": "text",
                "required": True,
                "max_length": 500,
                "guidance": "Describe the current pain point or opportunity. Quantify the impact if possible."
            },
            {
                "question_number": 2,
                "question_text": "Who are the primary users/stakeholders?",
                "question_type": "text",
                "required": True,
                "max_length": 300,
                "guidance": "List 2-4 primary user groups and their roles."
            },
            {
                "question_number": 3,
                "question_text": "What are the core functionalities?",
                "question_type": "multiline",
                "required": True,
                "max_length": 1000,
                "guidance": "List 3-7 MUST-HAVE features. Focus on what makes this project viable."
            },
            {
                "question_number": 4,
                "question_text": "What are the success criteria?",
                "question_type": "multiline",
                "required": True,
                "max_length": 500,
                "guidance": "Specify 3-5 MEASURABLE criteria using SMART format."
            },
            {
                "question_number": 5,
                "question_text": "What are the technical constraints?",
                "question_type": "multiline",
                "required": False,
                "max_length": 500,
                "guidance": "List hard technical requirements. This question is optional."
            },
            {
                "question_number": 6,
                "question_text": "What is the expected timeline?",
                "question_type": "text",
                "required": False,
                "max_length": 200,
                "guidance": "Provide rough timeframe (weeks/months). This question is optional."
            }
        ]

    # ========== Answer Management ==========

    async def submit_answer(
        self,
        session_id: UUID,
        question_number: int,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Submit or update an answer to a MarQed question.

        Args:
            session_id: The session UUID
            question_number: Question number (1-6)
            answer: The answer text
            metadata: Optional metadata (time_spent, revision_count)
            project_id: Optional project UUID (for additional validation)

        Returns:
            Answer submission result with progress

        Raises:
            NotFoundError: If session not found
            ValidationError: If answer invalid (length, format)
        """
        from app.models.green_paper import GreenPaperSession, Answer, SessionStatus

        # 1. Validate session exists (project_id is optional for validation)
        if project_id:
            result = await self.db.execute(
                select(GreenPaperSession).where(
                    GreenPaperSession.id == session_id,
                    GreenPaperSession.project_id == str(project_id)
                )
            )
        else:
            result = await self.db.execute(
                select(GreenPaperSession).where(
                    GreenPaperSession.id == session_id
                )
            )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"Session {session_id} is not in progress (status: {session.status})")

        # 2. Validate question_number (1-6)
        if question_number < 1 or question_number > 6:
            raise ValueError(f"Invalid question number: {question_number}. Must be 1-6.")

        # 3. Validate answer using existing validation method
        await self.validate_answer(question_number, answer)

        # Get question metadata
        questions = await self.get_questions()
        question = next(
            (q for q in questions if q["question_number"] == question_number),
            None
        )

        # 4 & 5. Check if answer exists, then update or create
        answer_result = await self.db.execute(
            select(Answer).where(
                Answer.session_id == session_id,
                Answer.question_number == question_number
            )
        )
        existing_answer = answer_result.scalar_one_or_none()

        if existing_answer:
            # Update existing answer
            existing_answer.answer = answer
            existing_answer.updated_at = datetime.now(timezone.utc)
            if metadata:
                existing_answer.metadata = {
                    **(existing_answer.metadata or {}),
                    **metadata,
                    "revision_count": (existing_answer.metadata or {}).get("revision_count", 0) + 1
                }
            answer_obj = existing_answer
        else:
            # Create new answer
            answer_obj = Answer(
                session_id=session_id,
                question_number=question_number,
                question_text=question["question_text"],
                answer=answer,
                is_required=1 if question["required"] else 0,
                max_length=question["max_length"],
                metadata=metadata or {}
            )
            self.db.add(answer_obj)

        # 6. Update session progress
        progress = await self.calculate_progress(session_id)
        session.progress_percentage = progress["percentage"]
        session.current_question = min(question_number + 1, 6)
        session.updated_at = datetime.now(timezone.utc)

        # 7. Check if session completed
        if await self.check_session_complete(session_id):
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(answer_obj)

        # 8. Return progress
        return {
            "answer_id": answer_obj.id,
            "question_number": answer_obj.question_number,
            "answer": answer_obj.answer,
            "created_at": answer_obj.created_at.isoformat(),
            "updated_at": answer_obj.updated_at.isoformat(),
            "session_status": session.status,
            "progress": {
                "answered": progress["answered"],
                "remaining": progress["remaining"],
                "percentage": progress["percentage"],
                "required_remaining": progress["required_remaining"]
            },
            "session_complete": session.status == SessionStatus.COMPLETED
        }

    async def validate_answer(
        self,
        question_number: int,
        answer: str
    ) -> Dict[str, Any]:
        """
        Validate an answer against question constraints.

        Args:
            question_number: Question number (1-6)
            answer: The answer text

        Returns:
            Validation result

        Raises:
            ValidationError: If answer invalid
        """
        questions = await self.get_questions()
        question = next(
            (q for q in questions if q["question_number"] == question_number),
            None
        )

        if not question:
            raise ValueError(f"Invalid question number: {question_number}")

        # Check required
        if question["required"] and not answer.strip():
            raise ValueError(f"Question {question_number} is required")

        # Check length
        if len(answer) > question["max_length"]:
            raise ValueError(
                f"Answer exceeds max length {question['max_length']} "
                f"(actual: {len(answer)})"
            )

        # Minimum length for required questions
        if question["required"] and len(answer.strip()) < 50:
            raise ValueError(
                f"Answer too short. Minimum 50 characters for required questions."
            )

        return {
            "is_valid": True,
            "word_count": len(answer.split()),
            "character_count": len(answer)
        }

    # ========== Constitution Generation ==========

    async def generate_constitution(
        self,
        project_id: UUID,
        session_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger Peter agent to generate project constitution.

        Args:
            project_id: The project UUID
            session_id: The session UUID
            options: Generation options

        Returns:
            Task info with workflow_id

        Raises:
            IncompleteSessionError: If required questions not answered
            ValidationError: If session invalid
        """
        from app.models.green_paper import GreenPaperSession, Answer, Constitution, ConstitutionStatus
        import json

        # 1. Verify all required questions answered (1-4)
        if not await self.check_session_complete(session_id):
            raise IncompleteSessionError(
                f"Session {session_id} is incomplete. All required questions (1-4) must be answered."
            )

        # Verify session belongs to project
        session_result = await self.db.execute(
            select(GreenPaperSession).where(
                GreenPaperSession.id == session_id,
                GreenPaperSession.project_id == str(project_id)
            )
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found for project {project_id}")

        # 2. Retrieve all answers
        answers_result = await self.db.execute(
            select(Answer).where(
                Answer.session_id == session_id
            ).order_by(Answer.question_number)
        )
        answers = answers_result.scalars().all()

        # Format answers for processing
        answers_data = [
            {
                "question_number": a.question_number,
                "question_text": a.question_text,
                "answer": a.answer
            }
            for a in answers
        ]

        # 3. Format answers for Peter
        peter_prompt = await self._format_answers_for_peter(answers_data)

        # 4. Trigger Peter agent workflow (using AgentService)
        # Note: This will be a call to the agent service to trigger Peter
        workflow_request = {
            "agent_name": "Peter",
            "workflow_type": "NEW_FEATURE",
            "task_description": "Generate project constitution from MarQed answers",
            "prompt": peter_prompt,
            "model": "deepseek-r1:latest",
            "project_id": str(project_id),
            "session_id": str(session_id),
            "options": options or {}
        }

        # Call agent service (this will be async workflow execution)
        # For now, we'll create a placeholder constitution record
        # In production, this would trigger the actual agent workflow

        # 5. Call Ollama API directly for constitution generation
        import httpx
        import json as json_module

        ollama_response = None
        constitution_json = None
        constitution_markdown = None
        word_count = 0
        generation_status = ConstitutionStatus.DRAFT

        try:
            # Call Ollama API (deepseek-r1 for reasoning)
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for CPU inference
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "deepseek-r1:latest",
                        "prompt": peter_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 4000
                        }
                    }
                )

                if response.status_code == 200:
                    ollama_response = response.json()
                    raw_response = ollama_response.get("response", "")

                    # Try to parse JSON from response
                    try:
                        # Find JSON in response (may be wrapped in markdown code blocks)
                        json_start = raw_response.find('{')
                        json_end = raw_response.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = raw_response[json_start:json_end]
                            constitution_json = json_module.loads(json_str)
                            generation_status = ConstitutionStatus.DRAFT  # Ready for review

                            # Generate markdown from JSON
                            constitution_markdown = self._json_to_markdown(constitution_json)
                            word_count = len(constitution_markdown.split())
                        else:
                            # No JSON found, use raw response as markdown
                            constitution_markdown = raw_response
                            constitution_json = {"raw_response": raw_response}
                            word_count = len(raw_response.split())
                    except json_module.JSONDecodeError:
                        constitution_markdown = raw_response
                        constitution_json = {"raw_response": raw_response, "parse_error": True}
                        word_count = len(raw_response.split())
                else:
                    constitution_json = {"error": f"Ollama returned status {response.status_code}"}
                    constitution_markdown = f"# Generation Error\n\nOllama returned status {response.status_code}"

        except httpx.TimeoutException:
            constitution_json = {"error": "Ollama request timed out (5 minutes)"}
            constitution_markdown = "# Generation Timeout\n\nThe LLM request timed out. CPU inference can be slow - try again."
        except Exception as e:
            constitution_json = {"error": str(e), "workflow_request": workflow_request}
            constitution_markdown = f"# Generation Error\n\n{str(e)}\n\nPeter agent prompt was prepared but LLM call failed."

        # 6. Create constitution record
        constitution = Constitution(
            session_id=session_id,
            project_id=str(project_id),
            status=generation_status,
            content_json=constitution_json or {"status": "generation_failed"},
            content_markdown=constitution_markdown or "# Constitution Generation Failed",
            word_count=word_count,
            generated_by="Peter",
            generation_attempt=1,
            metadata={
                "workflow_triggered_at": datetime.now(timezone.utc).isoformat(),
                "model": "deepseek-r1:latest",
                "answers_provided": len(answers_data),
                "ollama_response_meta": {
                    "total_duration": ollama_response.get("total_duration") if ollama_response else None,
                    "eval_count": ollama_response.get("eval_count") if ollama_response else None
                }
            }
        )

        self.db.add(constitution)
        await self.db.commit()
        await self.db.refresh(constitution)

        # 7. Return task_id and workflow info
        return {
            "constitution_id": constitution.id,
            "project_id": str(project_id),
            "session_id": str(session_id),
            "status": str(constitution.status),
            "workflow_id": f"workflow_{constitution.id}",
            "agent": "Peter",
            "model": "deepseek-r1:latest",
            "word_count": word_count,
            "message": "Constitution generated by Peter agent." if word_count > 0 else "Constitution generation encountered issues.",
            "next_steps": [
                "Review the generated constitution",
                "Approve or request changes",
                "Generate specification with Felix agent"
            ]
        }

    def _json_to_markdown(self, constitution_json: Dict[str, Any]) -> str:
        """Convert constitution JSON to readable markdown."""
        md = ["# Project Constitution\n"]

        if "problem_statement" in constitution_json:
            md.append("## 1. Problem Statement\n")
            md.append(f"{constitution_json['problem_statement']}\n")

        if "stakeholders" in constitution_json:
            md.append("\n## 2. Stakeholders\n")
            for s in constitution_json.get("stakeholders", []):
                md.append(f"### {s.get('role', 'Unknown')}\n")
                md.append(f"- **Priority**: {s.get('priority', 'N/A')}\n")
                md.append(f"- **Description**: {s.get('description', '')}\n")
                if s.get('needs'):
                    md.append(f"- **Needs**: {', '.join(s['needs'])}\n")
                md.append(f"- **Success**: {s.get('success_definition', '')}\n")

        if "core_functionalities" in constitution_json:
            md.append("\n## 3. Core Functionalities\n")
            for f in constitution_json.get("core_functionalities", []):
                md.append(f"### {f.get('name', 'Feature')}\n")
                md.append(f"- **Priority**: {f.get('priority', 'N/A')}\n")
                md.append(f"- **Description**: {f.get('description', '')}\n")
                md.append(f"- **Stakeholder**: {f.get('stakeholder', '')}\n")

        if "success_criteria" in constitution_json:
            md.append("\n## 4. Success Criteria\n")
            md.append("| Metric | Target | Measurement | Timeframe |\n")
            md.append("|--------|--------|-------------|------------|\n")
            for c in constitution_json.get("success_criteria", []):
                md.append(f"| {c.get('metric', '')} | {c.get('target', '')} | {c.get('measurement', '')} | {c.get('timeframe', '')} |\n")

        if "technical_constraints" in constitution_json:
            md.append("\n## 5. Technical Constraints\n")
            for c in constitution_json.get("technical_constraints", []):
                md.append(f"- **{c.get('constraint', '')}**: {c.get('reason', '')} (Impact: {c.get('impact', 'N/A')})\n")

        if "timeline" in constitution_json:
            md.append("\n## 6. Timeline\n")
            timeline = constitution_json["timeline"]
            if "phases" in timeline:
                md.append("### Phases\n")
                for p in timeline.get("phases", []):
                    md.append(f"- **{p.get('name', 'Phase')}**: {p.get('duration_weeks', '?')} weeks\n")
            md.append(f"\n**Total Duration**: {timeline.get('total_duration_weeks', '?')} weeks\n")

        if "risks_and_assumptions" in constitution_json:
            md.append("\n## 7. Risks & Assumptions\n")
            ra = constitution_json["risks_and_assumptions"]
            if "risks" in ra:
                md.append("### Risks\n")
                for r in ra.get("risks", []):
                    md.append(f"- **{r.get('risk', '')}** - Likelihood: {r.get('likelihood', '?')}, Impact: {r.get('impact', '?')}\n")
                    md.append(f"  - Mitigation: {r.get('mitigation', '')}\n")
            if "assumptions" in ra:
                md.append("### Assumptions\n")
                for a in ra.get("assumptions", []):
                    md.append(f"- {a}\n")

        return "\n".join(md)

    async def _format_answers_for_peter(
        self,
        answers: List[Dict[str, Any]]
    ) -> str:
        """Format MarQed answers into Peter's prompt."""
        # Create answer lookup by question number
        answer_map = {a["question_number"]: a["answer"] for a in answers}

        # Format the prompt using the template from green_paper_template.md
        prompt = f"""You are Peter, the Product Owner agent using deepseek-r1:latest model.

You have received a completed MarQed Green-Paper session for a new greenfield project.
Your task is to analyze these 6 answers and generate a comprehensive PROJECT CONSTITUTION.

## Input: MarQed Answers

**Q1 - Problem Statement**: {answer_map.get(1, "Not provided")}

**Q2 - Users & Stakeholders**: {answer_map.get(2, "Not provided")}

**Q3 - Core Functionalities**: {answer_map.get(3, "Not provided")}

**Q4 - Success Criteria**: {answer_map.get(4, "Not provided")}

**Q5 - Technical Constraints**: {answer_map.get(5, "None specified")}

**Q6 - Expected Timeline**: {answer_map.get(6, "Flexible")}

## Your Task

Generate a PROJECT CONSTITUTION with the following structure:

### 1. Problem Statement (150-250 words)
- Expand on Q1 answer
- Add context about WHY this problem matters
- Quantify impact if possible
- Identify root causes

### 2. Stakeholders Analysis (100-200 words)
- Parse Q2 answer into structured stakeholder list
- For EACH stakeholder group:
  * Role/Title
  * Primary needs
  * Priority level (Primary/Secondary/Tertiary)
  * Success definition from their perspective

### 3. Core Functionalities Breakdown (200-400 words)
- Parse Q3 answer into structured functionality list
- For EACH functionality:
  * Name (concise, 2-4 words)
  * Description (what it does)
  * Priority (Must-have / Should-have / Could-have)
  * Related stakeholder (who needs this most)
- Identify dependencies between functionalities

### 4. Success Criteria (150-250 words)
- Parse Q4 answer into structured criteria list
- For EACH criterion:
  * Metric name
  * Target value (with number)
  * Measurement method (how to track)
  * Timeframe (when to measure)
- Ensure SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)

### 5. Technical Constraints (100-150 words)
- Parse Q5 answer (or note "None specified")
- For EACH constraint:
  * Constraint description
  * Business reason (why it exists)
  * Impact on implementation (high/medium/low)

### 6. Timeline & Milestones (150-200 words)
- Parse Q6 answer (or propose reasonable timeline based on scope)
- Break into phases:
  * Discovery & Planning (weeks)
  * MVP Development (weeks)
  * Beta Testing (weeks)
  * Full Release (weeks)
- Define 3-5 major milestones with deliverables
- Calculate total duration in weeks

### 7. Risks & Assumptions (100-150 words)
- Identify 3-5 key risks based on the answers
- State assumptions made during constitution creation
- Suggest mitigation strategies

## Output Requirements

- Total word count: 1000-1500 words
- Format: Structured JSON with these keys:
  {{
    "problem_statement": "string",
    "stakeholders": [
      {{"role": "string", "description": "string", "priority": "string", "needs": ["string"], "success_definition": "string"}}
    ],
    "core_functionalities": [
      {{"name": "string", "description": "string", "priority": "string", "stakeholder": "string", "dependencies": ["string"]}}
    ],
    "success_criteria": [
      {{"metric": "string", "target": "string", "measurement": "string", "timeframe": "string"}}
    ],
    "technical_constraints": [
      {{"constraint": "string", "reason": "string", "impact": "string"}}
    ],
    "timeline": {{
      "phases": [
        {{"name": "string", "duration_weeks": number, "deliverables": ["string"]}}
      ],
      "total_duration_weeks": number,
      "milestones": [
        {{"name": "string", "target_date": "string", "deliverables": ["string"]}}
      ]
    }},
    "risks_and_assumptions": {{
      "risks": [
        {{"risk": "string", "likelihood": "string", "impact": "string", "mitigation": "string"}}
      ],
      "assumptions": ["string"]
    }}
  }}
- Also generate a markdown version for readability
- Tone: Professional, clear, actionable
- Avoid: Jargon, vague statements, implementation details

## Validation Checklist

Before returning the constitution, verify:
- [ ] All 7 sections completed
- [ ] All stakeholders from Q2 included
- [ ] All functionalities from Q3 categorized by priority
- [ ] All success criteria from Q4 are measurable
- [ ] Timeline is realistic given scope
- [ ] No contradictions between sections

Generate the PROJECT CONSTITUTION now. Return ONLY valid JSON, no additional commentary.
"""
        # Enrich prompt with KB context (KB1/KB5) if available
        try:
            from app.services.knowledge_base.kb_context_provider import KBContextProvider
            from app.services.chroma_service import ChromaService
            kb_provider = KBContextProvider(ChromaService())
            problem_desc = answer_map.get(1, "")
            kb_ctx = kb_provider.get_agent_context("quinn", f"New project: {problem_desc}")
            if kb_ctx.get("context_available"):
                kb_section = "\n\n## Knowledge Base Context (for risk analysis)\n"
                for bug in kb_ctx.get("famous_bugs", [])[:2]:
                    meta = bug.get("metadata", {})
                    kb_section += f"- **{meta.get('title', 'N/A')}**: {meta.get('category', '')} - lessons relevant to this project\n"
                for pm in kb_ctx.get("post_mortems", [])[:2]:
                    meta = pm.get("metadata", {})
                    kb_section += f"- **{meta.get('title', 'N/A')}** ({meta.get('company', '')}): {meta.get('root_cause_category', '')} incident\n"
                prompt += kb_section
        except Exception:
            pass  # KB enrichment is optional

        return prompt

    # ========== Constitution Review ==========

    async def get_constitution(
        self,
        project_id: UUID,
        constitution_id: Optional[UUID] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Retrieve project constitution.

        Args:
            project_id: The project UUID
            constitution_id: Specific constitution ID (default: latest)
            format: Response format (json or markdown)

        Returns:
            Constitution data

        Raises:
            NotFoundError: If constitution not found
        """
        from app.models.green_paper import Constitution

        if constitution_id:
            # Get specific constitution
            result = await self.db.execute(
                select(Constitution).where(
                    Constitution.id == constitution_id,
                    Constitution.project_id == str(project_id)
                )
            )
        else:
            # Get latest constitution for project
            result = await self.db.execute(
                select(Constitution).where(
                    Constitution.project_id == str(project_id)
                ).order_by(Constitution.created_at.desc()).limit(1)
            )

        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution not found for project {project_id}")

        # Return in requested format
        response = {
            "constitution_id": constitution.id,
            "project_id": constitution.project_id,
            "session_id": constitution.session_id,
            "status": constitution.status,
            "generated_by": constitution.generated_by,
            "generation_attempt": constitution.generation_attempt,
            "word_count": constitution.word_count,
            "created_at": constitution.created_at.isoformat(),
            "updated_at": constitution.updated_at.isoformat(),
            "reviewed_at": constitution.reviewed_at.isoformat() if constitution.reviewed_at else None,
            "reviewed_by": constitution.reviewed_by,
            "review_feedback": constitution.review_feedback,
            "metadata": constitution.metadata or {}
        }

        if format == "markdown":
            response["content"] = constitution.content_markdown
        else:  # json format
            response["content"] = constitution.content_json

        return response

    async def review_constitution(
        self,
        project_id: UUID,
        constitution_id: UUID,
        action: str,  # "approve" or "reject"
        feedback: str,
        reviewed_by: str,
        requested_changes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        User reviews constitution (approve or reject).

        Args:
            project_id: The project UUID
            constitution_id: The constitution UUID
            action: "approve" or "reject"
            feedback: Review feedback
            reviewed_by: User ID or name
            requested_changes: List of requested changes (required for reject)

        Returns:
            Review result with next_step

        Raises:
            ValidationError: If rejection without changes
        """
        from app.models.green_paper import Constitution, ConstitutionStatus

        # 1. Validate action
        if action not in ["approve", "reject"]:
            raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")

        # 2. If reject: require requested_changes
        if action == "reject" and not requested_changes:
            raise GreenPaperValidationError(
                "Requested changes are required when rejecting a constitution"
            )

        # Get constitution
        result = await self.db.execute(
            select(Constitution).where(
                Constitution.id == constitution_id,
                Constitution.project_id == str(project_id)
            )
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found for project {project_id}")

        # Check if already reviewed
        if constitution.status in [ConstitutionStatus.APPROVED, ConstitutionStatus.REJECTED]:
            raise ValueError(
                f"Constitution already {constitution.status}. Create a new constitution or regenerate."
            )

        # 3. Update constitution status
        constitution.reviewed_at = datetime.now(timezone.utc)
        constitution.reviewed_by = reviewed_by
        constitution.review_feedback = feedback

        if action == "approve":
            constitution.status = ConstitutionStatus.APPROVED

            await self.db.commit()
            await self.db.refresh(constitution)

            # 4. If approved: return next_step (generate_specification)
            return {
                "constitution_id": constitution.id,
                "status": constitution.status,
                "action": "approved",
                "message": "Constitution approved successfully",
                "next_step": "generate_specification",
                "next_actions": [
                    {
                        "action": "generate_specification",
                        "description": "Trigger Felix agent to generate High-Level Design specification",
                        "endpoint": f"/api/green-paper/specifications",
                        "method": "POST",
                        "required_params": {
                            "project_id": str(project_id),
                            "constitution_id": str(constitution_id)
                        }
                    }
                ]
            }
        else:  # reject
            constitution.status = ConstitutionStatus.REJECTED

            # Store requested changes in metadata
            if constitution.metadata:
                constitution.metadata["requested_changes"] = requested_changes
            else:
                constitution.metadata = {"requested_changes": requested_changes}

            await self.db.commit()
            await self.db.refresh(constitution)

            # 5. If rejected: create revision task for Peter
            return {
                "constitution_id": constitution.id,
                "status": constitution.status,
                "action": "rejected",
                "message": "Constitution rejected. Regeneration required.",
                "feedback": feedback,
                "requested_changes": requested_changes,
                "next_step": "regenerate_constitution",
                "next_actions": [
                    {
                        "action": "regenerate_constitution",
                        "description": "Trigger Peter agent to regenerate constitution with feedback",
                        "endpoint": f"/api/green-paper/constitutions/{constitution_id}/regenerate",
                        "method": "POST",
                        "required_params": {
                            "session_id": str(constitution.session_id),
                            "requested_changes": requested_changes
                        }
                    }
                ],
                "generation_attempt": constitution.generation_attempt,
                "max_attempts": 3,
                "attempts_remaining": 3 - constitution.generation_attempt
            }

    async def regenerate_constitution(
        self,
        project_id: UUID,
        constitution_id: UUID,
        requested_changes: List[Dict[str, Any]],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Trigger Peter to regenerate constitution with changes.

        Args:
            project_id: The project UUID
            constitution_id: The constitution UUID to regenerate
            requested_changes: User's requested changes
            feedback: User's review feedback

        Returns:
            Task info for regeneration
        """
        from app.models.green_paper import Constitution, ConstitutionStatus, Answer

        # Get the rejected constitution
        result = await self.db.execute(
            select(Constitution).where(
                Constitution.id == constitution_id,
                Constitution.project_id == str(project_id)
            )
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found for project {project_id}")

        if constitution.status != ConstitutionStatus.REJECTED:
            raise ValueError(
                f"Constitution must be rejected before regeneration. Current status: {constitution.status}"
            )

        # Check max attempts
        if constitution.generation_attempt >= 3:
            raise ValueError(
                f"Maximum generation attempts (3) reached for constitution {constitution_id}"
            )

        # Get session and all answers
        session_id = constitution.session_id

        answers_result = await self.db.execute(
            select(Answer).where(
                Answer.session_id == session_id
            ).order_by(Answer.question_number)
        )
        answers = answers_result.scalars().all()

        # Format answers for processing
        answers_data = [
            {
                "question_number": a.question_number,
                "question_text": a.question_text,
                "answer": a.answer
            }
            for a in answers
        ]

        # Format the regeneration prompt with feedback and requested changes
        base_prompt = await self._format_answers_for_peter(answers_data)

        # Add feedback and requested changes to the prompt
        regeneration_instructions = f"""

## IMPORTANT: Regeneration Instructions

This is a REGENERATION (attempt #{constitution.generation_attempt + 1} of 3).
The previous constitution was REJECTED by the user with the following feedback:

**User Feedback**: {feedback}

**Requested Changes**:
"""
        for i, change in enumerate(requested_changes, 1):
            section = change.get("section", "Unknown")
            field = change.get("field", "Unknown")
            current = change.get("current_value", "N/A")
            suggested = change.get("suggested_value", "N/A")
            reason = change.get("reason", "No reason provided")

            regeneration_instructions += f"""
{i}. Section: {section}
   Field: {field}
   Current Value: {current}
   Suggested Value: {suggested}
   Reason: {reason}
"""

        regeneration_instructions += """

Please regenerate the constitution addressing ALL of these requested changes.
Maintain the same overall structure but incorporate the user's feedback.
"""

        peter_prompt = base_prompt + regeneration_instructions

        # Create workflow request
        workflow_request = {
            "agent_name": "Peter",
            "workflow_type": "NEW_FEATURE",
            "task_description": f"Regenerate project constitution (attempt #{constitution.generation_attempt + 1})",
            "prompt": peter_prompt,
            "model": "deepseek-r1:latest",
            "project_id": str(project_id),
            "session_id": str(session_id),
            "constitution_id": str(constitution_id),
            "is_regeneration": True,
            "attempt": constitution.generation_attempt + 1,
            "requested_changes": requested_changes,
            "options": {}
        }

        # Create new constitution record with incremented attempt
        new_constitution = Constitution(
            session_id=session_id,
            project_id=str(project_id),
            status=ConstitutionStatus.DRAFT,
            content_json={
                "status": "regeneration_in_progress",
                "workflow_request": workflow_request,
                "previous_constitution_id": str(constitution_id),
                "requested_changes": requested_changes
            },
            content_markdown="# Constitution Regeneration In Progress\n\nPeter agent is regenerating based on your feedback...",
            word_count=0,
            generated_by="Peter",
            generation_attempt=constitution.generation_attempt + 1,
            metadata={
                "workflow_triggered_at": datetime.now(timezone.utc).isoformat(),
                "model": "deepseek-r1:latest",
                "previous_constitution_id": str(constitution_id),
                "user_feedback": feedback,
                "requested_changes": requested_changes
            }
        )

        self.db.add(new_constitution)
        await self.db.commit()
        await self.db.refresh(new_constitution)

        # Return regeneration info
        return {
            "constitution_id": new_constitution.id,
            "previous_constitution_id": str(constitution_id),
            "project_id": str(project_id),
            "session_id": str(session_id),
            "status": new_constitution.status,
            "workflow_id": f"workflow_{new_constitution.id}",  # Placeholder
            "agent": "Peter",
            "model": "deepseek-r1:latest",
            "generation_attempt": new_constitution.generation_attempt,
            "max_attempts": 3,
            "attempts_remaining": 3 - new_constitution.generation_attempt,
            "estimated_completion_time": "2-5 minutes",
            "message": f"Constitution regeneration started (attempt #{new_constitution.generation_attempt})",
            "feedback_incorporated": feedback,
            "changes_requested": len(requested_changes),
            "next_steps": [
                "Wait for constitution regeneration to complete",
                "Review the regenerated constitution",
                "Approve or request additional changes"
            ]
        }

    # ========== Specification Generation ==========

    async def generate_specification(
        self,
        project_id,  # Can be str or UUID
        constitution_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger Felix to generate HLD specification.

        Args:
            project_id: The project ID (string or UUID)
            constitution_id: The constitution UUID
            options: Generation options

        Returns:
            Task info with workflow_id

        Raises:
            InvalidStatusError: If constitution not approved
        """
        from app.models.green_paper import Constitution, Specification, SpecificationStatus, ConstitutionStatus
        import json

        # Normalize project_id to string
        project_id_str = str(project_id) if project_id else None

        # 1. Verify constitution is approved
        result = await self.db.execute(
            select(Constitution).where(
                Constitution.id == constitution_id,
                Constitution.project_id == project_id_str
            )
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found for project {project_id_str}")

        if constitution.status != ConstitutionStatus.APPROVED:
            raise InvalidStatusError(
                f"Constitution must be approved before specification generation. "
                f"Current status: {constitution.status}"
            )

        # 2. Retrieve constitution content
        constitution_json = constitution.content_json
        constitution_markdown = constitution.content_markdown

        # 3. Format for Felix (Feature Architect)
        felix_prompt = await self._format_constitution_for_felix(
            constitution_json,
            constitution_markdown,
            project_id_str
        )

        # 4. Trigger Felix agent workflow via Ollama API
        workflow_request = {
            "agent_name": "Felix",
            "workflow_type": "NEW_FEATURE",
            "task_description": "Generate High-Level Design specification from constitution",
            "prompt": felix_prompt,
            "model": "qwen2.5-coder:7b",
            "project_id": project_id_str,
            "constitution_id": str(constitution_id),
            "options": options or {}
        }

        # 5. Call Ollama API directly for specification generation
        import httpx
        import json as json_module

        ollama_response = None
        specification_json = None
        specification_markdown = None
        generation_status = SpecificationStatus.DRAFT

        try:
            # Call Ollama API (qwen2.5-coder:7b for Felix)
            async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for CPU inference
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "qwen2.5-coder:7b",
                        "prompt": felix_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 6000  # Longer for HLD specification
                        }
                    }
                )

                if response.status_code == 200:
                    ollama_response = response.json()
                    raw_response = ollama_response.get("response", "")

                    # Try to parse JSON from response
                    try:
                        # Find JSON in response (may be wrapped in markdown code blocks)
                        json_start = raw_response.find('{')
                        json_end = raw_response.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = raw_response[json_start:json_end]
                            specification_json = json_module.loads(json_str)
                            generation_status = SpecificationStatus.DRAFT  # Ready for review

                            # Generate markdown from JSON
                            specification_markdown = self._specification_json_to_markdown(specification_json)
                        else:
                            # No JSON found, use raw response as markdown
                            specification_markdown = raw_response
                            specification_json = {"raw_response": raw_response}
                    except json_module.JSONDecodeError:
                        specification_markdown = raw_response
                        specification_json = {"raw_response": raw_response, "parse_error": True}
                else:
                    specification_json = {"error": f"Ollama returned status {response.status_code}"}
                    specification_markdown = f"# Generation Error\n\nOllama returned status {response.status_code}"

        except httpx.TimeoutException:
            specification_json = {"error": "Ollama request timed out (10 minutes)"}
            specification_markdown = "# Generation Timeout\n\nThe LLM request timed out. CPU inference can be slow - try again."
        except Exception as e:
            specification_json = {"error": str(e), "workflow_request": workflow_request}
            specification_markdown = f"# Generation Error\n\n{str(e)}\n\nFelix agent prompt was prepared but LLM call failed."

        # 6. Create specification record
        specification = Specification(
            constitution_id=constitution_id,
            project_id=project_id_str,
            status=generation_status,
            content_json=specification_json or {"status": "generation_failed"},
            content_markdown=specification_markdown or "# Specification Generation Failed",
            generated_by="Felix",
            generation_attempt=1,
            metadata={
                "workflow_triggered_at": datetime.now(timezone.utc).isoformat(),
                "model": "qwen2.5-coder:7b",
                "constitution_id": str(constitution_id),
                "ollama_response_meta": {
                    "total_duration": ollama_response.get("total_duration") if ollama_response else None,
                    "eval_count": ollama_response.get("eval_count") if ollama_response else None
                }
            }
        )

        self.db.add(specification)
        await self.db.commit()
        await self.db.refresh(specification)

        # 7. Return task_id and workflow info
        return {
            "specification_id": str(specification.id),
            "project_id": project_id_str,
            "constitution_id": str(constitution_id),
            "status": str(specification.status.value) if hasattr(specification.status, 'value') else str(specification.status),
            "workflow_id": f"workflow_{specification.id}",
            "agent": "Felix",
            "model": "qwen2.5-coder:7b",
            "content_preview": specification_markdown[:500] if specification_markdown else None,
            "generation_complete": specification_json and "error" not in specification_json,
            "message": "Specification generation complete." if (specification_json and "error" not in specification_json) else "Specification generation encountered an issue.",
            "next_steps": [
                "Review the generated HLD specification",
                "Approve or request changes",
                "Generate epics from specification"
            ]
        }

    async def _format_constitution_for_felix(
        self,
        constitution_json: Dict[str, Any],
        constitution_markdown: str,
        project_id  # Can be str or UUID
    ) -> str:
        """Format approved constitution into Felix's prompt."""
        import json

        prompt = f"""You are Felix, the Feature Architect agent using qwen2.5-coder:7b model.

You have received an APPROVED PROJECT CONSTITUTION from Peter (Product Owner).
Your task is to generate a comprehensive HIGH-LEVEL DESIGN (HLD) SPECIFICATION.

## Input: Approved Constitution

### Problem Statement
{constitution_json.get('problem_statement', 'Not provided')}

### Stakeholders
{json.dumps(constitution_json.get('stakeholders', []), indent=2)}

### Core Functionalities
{json.dumps(constitution_json.get('core_functionalities', []), indent=2)}

### Success Criteria
{json.dumps(constitution_json.get('success_criteria', []), indent=2)}

### Technical Constraints
{json.dumps(constitution_json.get('technical_constraints', []), indent=2, default=str)}

### Timeline
{json.dumps(constitution_json.get('timeline', dict()), indent=2, default=str)}

### Risks & Assumptions
{json.dumps(constitution_json.get('risks_and_assumptions', dict()), indent=2, default=str)}

## Your Task

Generate a HIGH-LEVEL DESIGN SPECIFICATION with the following structure:

### 1. Architecture Overview (200-300 words)
- System architecture style (microservices, monolithic, serverless, etc.)
- Major architectural components and their responsibilities
- Communication patterns between components
- Deployment architecture (cloud, on-premise, hybrid)
- Justify architecture choices based on constitution constraints

### 2. Component Breakdown (300-500 words)
For EACH major component:
- Component name
- Responsibility (what it does)
- Technology stack recommendation
- Dependencies (what it needs)
- Scalability considerations
- Related stakeholders (who uses it)

Map components to core functionalities from constitution.

### 3. Data Model (200-300 words)
- Core entities and their relationships
- Data storage strategy (SQL, NoSQL, hybrid)
- Data flow between components
- Data consistency and integrity requirements
- Data security and privacy considerations

### 4. API Design (200-300 words)
- API style (REST, GraphQL, gRPC, etc.)
- Major endpoints organized by domain
- Authentication and authorization strategy
- API versioning strategy
- Rate limiting and throttling

### 5. Integration Points (150-200 words)
- External system integrations
- Third-party service dependencies
- Data import/export mechanisms
- Webhook/event-driven integrations
- Integration with existing systems (if mentioned in constraints)

### 6. Quality Attributes (200-300 words)
Address EACH success criterion from constitution:
- Performance targets (response time, throughput)
- Scalability requirements (concurrent users, data volume)
- Reliability targets (uptime, error rates)
- Security requirements (authentication, encryption, compliance)
- Maintainability considerations (code quality, testing)

### 7. Technology Stack (150-200 words)
- Frontend technologies (if applicable)
- Backend technologies
- Database technologies
- DevOps tools (CI/CD, monitoring, logging)
- Justification for each technology choice based on constraints

### 8. Deployment & Infrastructure (150-200 words)
- Deployment strategy (blue-green, canary, rolling)
- Infrastructure requirements (compute, storage, network)
- Monitoring and observability strategy
- Disaster recovery and backup strategy
- Cost considerations

### 9. Development Phases (200-300 words)
Break development into phases based on timeline:
- Phase 1: Foundation (core infrastructure, data model)
- Phase 2: MVP (must-have functionalities)
- Phase 3: Enhancements (should-have functionalities)
- Phase 4: Polish (could-have functionalities)

For each phase:
- Duration (weeks)
- Deliverables
- Dependencies
- Success criteria validation

### 10. Risk Mitigation (150-200 words)
Address EACH risk from constitution:
- Technical mitigation strategies
- Architectural decisions that reduce risk
- Fallback plans
- Proof-of-concept recommendations

## Output Requirements

- Total word count: 2000-3000 words
- Format: Structured JSON with these keys:
  {{
    "architecture_overview": {{
      "style": "string",
      "components": ["string"],
      "communication_patterns": ["string"],
      "deployment": "string",
      "justification": "string"
    }},
    "components": [
      {{
        "name": "string",
        "responsibility": "string",
        "technology_stack": ["string"],
        "dependencies": ["string"],
        "scalability": "string",
        "stakeholders": ["string"]
      }}
    ],
    "data_model": {{
      "entities": [
        {{"name": "string", "attributes": ["string"], "relationships": ["string"]}}
      ],
      "storage_strategy": "string",
      "data_flow": "string",
      "consistency": "string",
      "security": "string"
    }},
    "api_design": {{
      "style": "string",
      "endpoints": [
        {{"path": "string", "method": "string", "description": "string", "domain": "string"}}
      ],
      "authentication": "string",
      "versioning": "string",
      "rate_limiting": "string"
    }},
    "integration_points": [
      {{
        "system": "string",
        "purpose": "string",
        "mechanism": "string"
      }}
    ],
    "quality_attributes": {{
      "performance": {{"targets": ["string"], "strategies": ["string"]}},
      "scalability": {{"requirements": ["string"], "strategies": ["string"]}},
      "reliability": {{"targets": ["string"], "strategies": ["string"]}},
      "security": {{"requirements": ["string"], "strategies": ["string"]}},
      "maintainability": {{"practices": ["string"]}}
    }},
    "technology_stack": {{
      "frontend": ["string"],
      "backend": ["string"],
      "database": ["string"],
      "devops": ["string"],
      "justifications": {{"technology": "reason"}}
    }},
    "deployment_infrastructure": {{
      "strategy": "string",
      "infrastructure": {{"compute": "string", "storage": "string", "network": "string"}},
      "monitoring": "string",
      "disaster_recovery": "string",
      "cost_estimate": "string"
    }},
    "development_phases": [
      {{
        "phase_number": number,
        "name": "string",
        "duration_weeks": number,
        "deliverables": ["string"],
        "dependencies": ["string"],
        "success_criteria": ["string"]
      }}
    ],
    "risk_mitigation": [
      {{
        "risk": "string",
        "mitigation_strategy": "string",
        "architectural_decision": "string",
        "poc_recommendation": "string"
      }}
    ]
  }}
- Also generate a markdown version for readability
- Tone: Technical, precise, actionable
- Include diagrams descriptions (mermaid syntax) where helpful
- Avoid: Vague statements, buzzwords without substance

## Validation Checklist

Before returning the specification, verify:
- [ ] All 10 sections completed
- [ ] All core functionalities from constitution have components
- [ ] All success criteria addressed in quality attributes
- [ ] All technical constraints respected in technology stack
- [ ] All risks have mitigation strategies
- [ ] Timeline phases align with constitution timeline
- [ ] No contradictions between sections

Generate the HIGH-LEVEL DESIGN SPECIFICATION now. Return ONLY valid JSON, no additional commentary.
"""
        return prompt

    def _specification_json_to_markdown(self, spec_json: Dict[str, Any]) -> str:
        """Convert specification JSON to readable markdown."""
        md = ["# High-Level Design Specification\n"]

        # Architecture Overview
        if "architecture_overview" in spec_json:
            arch = spec_json["architecture_overview"]
            md.append("## 1. Architecture Overview\n")
            md.append(f"**Style**: {arch.get('style', 'N/A')}\n")
            if arch.get('components'):
                md.append("\n**Major Components**:\n")
                for c in arch.get('components', []):
                    md.append(f"- {c}\n")
            if arch.get('communication_patterns'):
                md.append("\n**Communication Patterns**:\n")
                for p in arch.get('communication_patterns', []):
                    md.append(f"- {p}\n")
            md.append(f"\n**Deployment**: {arch.get('deployment', 'N/A')}\n")
            md.append(f"\n**Justification**: {arch.get('justification', '')}\n")

        # Components
        if "components" in spec_json:
            md.append("\n## 2. Component Breakdown\n")
            for comp in spec_json.get('components', []):
                md.append(f"### {comp.get('name', 'Component')}\n")
                md.append(f"- **Responsibility**: {comp.get('responsibility', '')}\n")
                if comp.get('technology_stack'):
                    md.append(f"- **Technology**: {', '.join(comp['technology_stack'])}\n")
                if comp.get('dependencies'):
                    md.append(f"- **Dependencies**: {', '.join(comp['dependencies'])}\n")
                md.append(f"- **Scalability**: {comp.get('scalability', '')}\n")
                if comp.get('stakeholders'):
                    md.append(f"- **Stakeholders**: {', '.join(comp['stakeholders'])}\n")

        # Data Model
        if "data_model" in spec_json:
            dm = spec_json["data_model"]
            md.append("\n## 3. Data Model\n")
            if dm.get('entities'):
                md.append("### Entities\n")
                for e in dm.get('entities', []):
                    md.append(f"**{e.get('name', 'Entity')}**\n")
                    if e.get('attributes'):
                        md.append(f"- Attributes: {', '.join(e['attributes'])}\n")
                    if e.get('relationships'):
                        md.append(f"- Relationships: {', '.join(e['relationships'])}\n")
            md.append(f"\n**Storage Strategy**: {dm.get('storage_strategy', 'N/A')}\n")
            md.append(f"\n**Data Flow**: {dm.get('data_flow', '')}\n")
            md.append(f"\n**Consistency**: {dm.get('consistency', '')}\n")
            md.append(f"\n**Security**: {dm.get('security', '')}\n")

        # API Design
        if "api_design" in spec_json:
            api = spec_json["api_design"]
            md.append("\n## 4. API Design\n")
            md.append(f"**Style**: {api.get('style', 'N/A')}\n")
            md.append(f"**Authentication**: {api.get('authentication', 'N/A')}\n")
            md.append(f"**Versioning**: {api.get('versioning', 'N/A')}\n")
            if api.get('endpoints'):
                md.append("\n### Endpoints\n")
                md.append("| Path | Method | Description | Domain |\n")
                md.append("|------|--------|-------------|--------|\n")
                for ep in api.get('endpoints', []):
                    md.append(f"| {ep.get('path', '')} | {ep.get('method', '')} | {ep.get('description', '')} | {ep.get('domain', '')} |\n")

        # Integration Points
        if "integration_points" in spec_json:
            md.append("\n## 5. Integration Points\n")
            for ip in spec_json.get('integration_points', []):
                md.append(f"### {ip.get('system', 'System')}\n")
                md.append(f"- **Purpose**: {ip.get('purpose', '')}\n")
                md.append(f"- **Mechanism**: {ip.get('mechanism', '')}\n")

        # Quality Attributes
        if "quality_attributes" in spec_json:
            qa = spec_json["quality_attributes"]
            md.append("\n## 6. Quality Attributes\n")
            for attr in ['performance', 'scalability', 'reliability', 'security', 'maintainability']:
                if attr in qa:
                    md.append(f"### {attr.capitalize()}\n")
                    attr_data = qa[attr]
                    if isinstance(attr_data, dict):
                        for k, v in attr_data.items():
                            if isinstance(v, list):
                                md.append(f"**{k.capitalize()}**: {', '.join(v)}\n")
                            else:
                                md.append(f"**{k.capitalize()}**: {v}\n")

        # Technology Stack
        if "technology_stack" in spec_json:
            ts = spec_json["technology_stack"]
            md.append("\n## 7. Technology Stack\n")
            for layer in ['frontend', 'backend', 'database', 'devops']:
                if layer in ts and ts[layer]:
                    md.append(f"**{layer.capitalize()}**: {', '.join(ts[layer])}\n")
            if ts.get('justifications'):
                md.append("\n### Justifications\n")
                for tech, reason in ts['justifications'].items():
                    md.append(f"- **{tech}**: {reason}\n")

        # Deployment & Infrastructure
        if "deployment_infrastructure" in spec_json:
            di = spec_json["deployment_infrastructure"]
            md.append("\n## 8. Deployment & Infrastructure\n")
            md.append(f"**Strategy**: {di.get('strategy', 'N/A')}\n")
            if di.get('infrastructure'):
                infra = di['infrastructure']
                md.append(f"\n**Compute**: {infra.get('compute', 'N/A')}\n")
                md.append(f"**Storage**: {infra.get('storage', 'N/A')}\n")
                md.append(f"**Network**: {infra.get('network', 'N/A')}\n")
            md.append(f"\n**Monitoring**: {di.get('monitoring', '')}\n")
            md.append(f"**Disaster Recovery**: {di.get('disaster_recovery', '')}\n")
            md.append(f"**Cost Estimate**: {di.get('cost_estimate', '')}\n")

        # Development Phases
        if "development_phases" in spec_json:
            md.append("\n## 9. Development Phases\n")
            for phase in spec_json.get('development_phases', []):
                md.append(f"### Phase {phase.get('phase_number', '?')}: {phase.get('name', 'Phase')}\n")
                md.append(f"- **Duration**: {phase.get('duration_weeks', '?')} weeks\n")
                if phase.get('deliverables'):
                    md.append(f"- **Deliverables**: {', '.join(phase['deliverables'])}\n")
                if phase.get('dependencies'):
                    md.append(f"- **Dependencies**: {', '.join(phase['dependencies'])}\n")
                if phase.get('success_criteria'):
                    md.append(f"- **Success Criteria**: {', '.join(phase['success_criteria'])}\n")

        # Risk Mitigation
        if "risk_mitigation" in spec_json:
            md.append("\n## 10. Risk Mitigation\n")
            for risk in spec_json.get('risk_mitigation', []):
                md.append(f"### {risk.get('risk', 'Risk')}\n")
                md.append(f"- **Mitigation**: {risk.get('mitigation_strategy', '')}\n")
                md.append(f"- **Architectural Decision**: {risk.get('architectural_decision', '')}\n")
                if risk.get('poc_recommendation'):
                    md.append(f"- **PoC Recommendation**: {risk['poc_recommendation']}\n")

        # Handle raw response (when JSON parsing failed)
        if "raw_response" in spec_json:
            md.append("\n---\n")
            md.append("## Raw LLM Response\n")
            md.append(f"{spec_json['raw_response']}\n")

        return "".join(md)

    # ========== Specification Review ==========

    async def get_specification(
        self,
        project_id: UUID,
        specification_id: Optional[UUID] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Retrieve project specification.

        Args:
            project_id: The project UUID
            specification_id: Specific specification ID (default: latest)
            format: Response format (json or markdown)

        Returns:
            Specification data

        Raises:
            NotFoundError: If specification not found
        """
        from app.models.green_paper import Specification

        if specification_id:
            # Get specific specification
            result = await self.db.execute(
                select(Specification).where(
                    Specification.id == specification_id,
                    Specification.project_id == str(project_id)
                )
            )
        else:
            # Get latest specification for project
            result = await self.db.execute(
                select(Specification).where(
                    Specification.project_id == str(project_id)
                ).order_by(Specification.created_at.desc()).limit(1)
            )

        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification not found for project {project_id}")

        # Return in requested format
        response = {
            "specification_id": specification.id,
            "project_id": specification.project_id,
            "constitution_id": specification.constitution_id,
            "status": specification.status,
            "generated_by": specification.generated_by,
            "generation_attempt": specification.generation_attempt,
            "created_at": specification.created_at.isoformat(),
            "updated_at": specification.updated_at.isoformat(),
            "reviewed_at": specification.reviewed_at.isoformat() if specification.reviewed_at else None,
            "reviewed_by": specification.reviewed_by,
            "review_feedback": specification.review_feedback,
            "metadata": specification.metadata or {}
        }

        if format == "markdown":
            response["content"] = specification.content_markdown
        else:  # json format
            response["content"] = specification.content_json

        return response

    async def review_specification(
        self,
        project_id: UUID,
        specification_id: UUID,
        action: str,  # "approve" or "reject"
        feedback: str,
        reviewed_by: str,
        requested_changes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        User reviews specification (approve or reject).

        Args:
            project_id: The project UUID
            specification_id: The specification UUID
            action: "approve" or "reject"
            feedback: Review feedback
            reviewed_by: User ID or name
            requested_changes: List of requested changes (required for reject)

        Returns:
            Review result with next_step

        Raises:
            ValidationError: If rejection without changes
        """
        from app.models.green_paper import Specification, SpecificationStatus

        # 1. Validate action
        if action not in ["approve", "reject"]:
            raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")

        # 2. If reject: require requested_changes
        if action == "reject" and not requested_changes:
            raise GreenPaperValidationError(
                "Requested changes are required when rejecting a specification"
            )

        # Get specification
        result = await self.db.execute(
            select(Specification).where(
                Specification.id == specification_id,
                Specification.project_id == str(project_id)
            )
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found for project {project_id}")

        # Check if already reviewed
        if specification.status in [SpecificationStatus.APPROVED, SpecificationStatus.REJECTED]:
            raise ValueError(
                f"Specification already {specification.status}. Create a new specification or regenerate."
            )

        # 3. Update specification status
        specification.reviewed_at = datetime.now(timezone.utc)
        specification.reviewed_by = reviewed_by
        specification.review_feedback = feedback

        if action == "approve":
            specification.status = SpecificationStatus.APPROVED

            await self.db.commit()
            await self.db.refresh(specification)

            # 4. If approved: return next_step (task generation - future work)
            return {
                "specification_id": specification.id,
                "status": specification.status,
                "action": "approved",
                "message": "Specification approved successfully",
                "next_step": "generate_tasks",
                "next_actions": [
                    {
                        "action": "generate_tasks",
                        "description": "Break down specification into epics, features, and stories",
                        "endpoint": f"/api/green-paper/specifications/{specification_id}/tasks",
                        "method": "POST",
                        "required_params": {
                            "project_id": str(project_id),
                            "specification_id": str(specification_id)
                        }
                    }
                ]
            }
        else:  # reject
            specification.status = SpecificationStatus.REJECTED

            # Store requested changes in metadata
            if specification.metadata:
                specification.metadata["requested_changes"] = requested_changes
            else:
                specification.metadata = {"requested_changes": requested_changes}

            await self.db.commit()
            await self.db.refresh(specification)

            # 5. If rejected: create revision task for Felix
            return {
                "specification_id": specification.id,
                "status": specification.status,
                "action": "rejected",
                "message": "Specification rejected. Regeneration required.",
                "feedback": feedback,
                "requested_changes": requested_changes,
                "next_step": "regenerate_specification",
                "next_actions": [
                    {
                        "action": "regenerate_specification",
                        "description": "Trigger Felix agent to regenerate specification with feedback",
                        "endpoint": f"/api/green-paper/specifications/{specification_id}/regenerate",
                        "method": "POST",
                        "required_params": {
                            "constitution_id": str(specification.constitution_id),
                            "requested_changes": requested_changes
                        }
                    }
                ],
                "generation_attempt": specification.generation_attempt,
                "max_attempts": 3,
                "attempts_remaining": 3 - specification.generation_attempt
            }

    async def regenerate_specification(
        self,
        project_id: UUID,
        specification_id: UUID,
        requested_changes: List[Dict[str, Any]],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Trigger Felix to regenerate specification with changes.

        Args:
            project_id: The project UUID
            specification_id: The specification UUID to regenerate
            requested_changes: User's requested changes
            feedback: User's review feedback

        Returns:
            Task info for regeneration
        """
        from app.models.green_paper import Specification, SpecificationStatus, Constitution
        import json

        # Get the rejected specification
        result = await self.db.execute(
            select(Specification).where(
                Specification.id == specification_id,
                Specification.project_id == str(project_id)
            )
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found for project {project_id}")

        if specification.status != SpecificationStatus.REJECTED:
            raise ValueError(
                f"Specification must be rejected before regeneration. Current status: {specification.status}"
            )

        # Check max attempts
        if specification.generation_attempt >= 3:
            raise ValueError(
                f"Maximum generation attempts (3) reached for specification {specification_id}"
            )

        # Get the constitution
        constitution_id = specification.constitution_id
        constitution_result = await self.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = constitution_result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        # Format the regeneration prompt with feedback and requested changes
        base_prompt = await self._format_constitution_for_felix(
            constitution.content_json,
            constitution.content_markdown,
            project_id
        )

        # Add feedback and requested changes to the prompt
        regeneration_instructions = f"""

## IMPORTANT: Regeneration Instructions

This is a REGENERATION (attempt #{specification.generation_attempt + 1} of 3).
The previous specification was REJECTED by the user with the following feedback:

**User Feedback**: {feedback}

**Requested Changes**:
"""
        for i, change in enumerate(requested_changes, 1):
            section = change.get("section", "Unknown")
            field = change.get("field", "Unknown")
            current = change.get("current_value", "N/A")
            suggested = change.get("suggested_value", "N/A")
            reason = change.get("reason", "No reason provided")

            regeneration_instructions += f"""
{i}. Section: {section}
   Field: {field}
   Current Value: {current}
   Suggested Value: {suggested}
   Reason: {reason}
"""

        regeneration_instructions += """

Please regenerate the HIGH-LEVEL DESIGN SPECIFICATION addressing ALL of these requested changes.
Maintain the same overall structure but incorporate the user's feedback.
"""

        felix_prompt = base_prompt + regeneration_instructions

        # Create workflow request
        workflow_request = {
            "agent_name": "Felix",
            "workflow_type": "NEW_FEATURE",
            "task_description": f"Regenerate HLD specification (attempt #{specification.generation_attempt + 1})",
            "prompt": felix_prompt,
            "model": "qwen2.5-coder:7b",
            "project_id": str(project_id),
            "constitution_id": str(constitution_id),
            "specification_id": str(specification_id),
            "is_regeneration": True,
            "attempt": specification.generation_attempt + 1,
            "requested_changes": requested_changes,
            "options": {}
        }

        # Create new specification record with incremented attempt
        new_specification = Specification(
            constitution_id=constitution_id,
            project_id=str(project_id),
            status=SpecificationStatus.DRAFT,
            content_json={
                "status": "regeneration_in_progress",
                "workflow_request": workflow_request,
                "previous_specification_id": str(specification_id),
                "requested_changes": requested_changes
            },
            content_markdown="# Specification Regeneration In Progress\n\nFelix agent is regenerating based on your feedback...",
            generated_by="Felix",
            generation_attempt=specification.generation_attempt + 1,
            metadata={
                "workflow_triggered_at": datetime.now(timezone.utc).isoformat(),
                "model": "qwen2.5-coder:7b",
                "previous_specification_id": str(specification_id),
                "user_feedback": feedback,
                "requested_changes": requested_changes
            }
        )

        self.db.add(new_specification)
        await self.db.commit()
        await self.db.refresh(new_specification)

        # Return regeneration info
        return {
            "specification_id": new_specification.id,
            "previous_specification_id": str(specification_id),
            "project_id": str(project_id),
            "constitution_id": str(constitution_id),
            "status": new_specification.status,
            "workflow_id": f"workflow_{new_specification.id}",  # Placeholder
            "agent": "Felix",
            "model": "qwen2.5-coder:7b",
            "generation_attempt": new_specification.generation_attempt,
            "max_attempts": 3,
            "attempts_remaining": 3 - new_specification.generation_attempt,
            "estimated_completion_time": "3-7 minutes",
            "message": f"Specification regeneration started (attempt #{new_specification.generation_attempt})",
            "feedback_incorporated": feedback,
            "changes_requested": len(requested_changes),
            "next_steps": [
                "Wait for specification regeneration to complete",
                "Review the regenerated specification",
                "Approve or request additional changes"
            ]
        }

    # ========== ChromaDB Integration ==========

    async def store_constitution_embeddings(
        self,
        constitution_id: UUID,
        constitution_content: Dict[str, Any]
    ) -> None:
        """Store constitution in ChromaDB for semantic search."""
        from app.models.green_paper import Constitution

        # Get full constitution record
        result = await self.db.execute(
            select(Constitution).where(Constitution.id == constitution_id)
        )
        constitution = result.scalar_one_or_none()

        if not constitution:
            raise ValueError(f"Constitution {constitution_id} not found")

        # 1. Extract text from constitution sections for embedding
        text_sections = []

        # Problem statement (high weight)
        if constitution_content.get('problem_statement'):
            text_sections.append(f"Problem: {constitution_content['problem_statement']}")

        # Stakeholders
        if constitution_content.get('stakeholders'):
            stakeholders_text = " ".join([
                f"{s.get('role', '')}: {s.get('description', '')}"
                for s in constitution_content['stakeholders']
            ])
            text_sections.append(f"Stakeholders: {stakeholders_text}")

        # Core functionalities (high weight)
        if constitution_content.get('core_functionalities'):
            functionalities_text = " ".join([
                f"{f.get('name', '')}: {f.get('description', '')}"
                for f in constitution_content['core_functionalities']
            ])
            text_sections.append(f"Functionalities: {functionalities_text}")

        # Success criteria
        if constitution_content.get('success_criteria'):
            criteria_text = " ".join([
                f"{c.get('metric', '')}: {c.get('target', '')}"
                for c in constitution_content['success_criteria']
            ])
            text_sections.append(f"Success Criteria: {criteria_text}")

        # Technical constraints
        if constitution_content.get('technical_constraints'):
            constraints_text = " ".join([
                f"{tc.get('constraint', '')} ({tc.get('reason', '')})"
                for tc in constitution_content['technical_constraints']
            ])
            text_sections.append(f"Constraints: {constraints_text}")

        # Combine all sections
        combined_text = " ".join(text_sections)

        # 2 & 3. Generate embeddings and store in ChromaDB
        try:
            collection_name = "project_constitutions"

            # Prepare metadata
            metadata = {
                "constitution_id": str(constitution_id),
                "project_id": str(constitution.project_id),
                "session_id": str(constitution.session_id),
                "status": constitution.status,
                "word_count": constitution.word_count or 0,
                "generated_by": constitution.generated_by,
                "created_at": constitution.created_at.isoformat(),
                "has_problem_statement": bool(constitution_content.get('problem_statement')),
                "num_stakeholders": len(constitution_content.get('stakeholders', [])),
                "num_functionalities": len(constitution_content.get('core_functionalities', [])),
                "num_success_criteria": len(constitution_content.get('success_criteria', []))
            }

            # Store in ChromaDB using embedding service
            await self.chroma_service.add_documents(
                collection_name=collection_name,
                documents=[combined_text],
                metadatas=[metadata],
                ids=[str(constitution_id)]
            )

        except Exception as e:
            # Log error but don't fail the constitution generation
            print(f"Warning: Failed to store constitution embeddings: {e}")
            # TODO: Add proper logging

    async def search_similar_projects(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar projects based on constitution content."""
        try:
            collection_name = "project_constitutions"

            # 1 & 2. Generate embedding for query and search ChromaDB
            results = await self.chroma_service.query(
                collection_name=collection_name,
                query_texts=[query],
                n_results=limit
            )

            # 3. Return similar projects with metadata
            similar_projects = []

            if results and results.get('ids') and len(results['ids']) > 0:
                for i, constitution_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    distance = results['distances'][0][i] if results.get('distances') else None
                    document = results['documents'][0][i] if results.get('documents') else ""

                    # Calculate similarity score (1 - normalized distance)
                    similarity_score = 1.0 - (distance if distance is not None else 0.5)

                    similar_projects.append({
                        "constitution_id": constitution_id,
                        "project_id": metadata.get("project_id"),
                        "session_id": metadata.get("session_id"),
                        "similarity_score": round(similarity_score, 3),
                        "status": metadata.get("status"),
                        "generated_by": metadata.get("generated_by"),
                        "created_at": metadata.get("created_at"),
                        "word_count": metadata.get("word_count"),
                        "num_stakeholders": metadata.get("num_stakeholders"),
                        "num_functionalities": metadata.get("num_functionalities"),
                        "preview": document[:200] + "..." if len(document) > 200 else document
                    })

            return similar_projects

        except Exception as e:
            print(f"Warning: Failed to search similar projects: {e}")
            # Return empty list on error
            return []

    # ========== Validation & Helper Methods ==========

    async def check_session_complete(
        self,
        session_id: UUID
    ) -> bool:
        """Check if session has all required answers."""
        from app.models.green_paper import Answer

        # Required questions: 1, 2, 3, 4
        required_questions = {1, 2, 3, 4}

        # Get all answers for this session
        result = await self.db.execute(
            select(Answer.question_number).where(
                Answer.session_id == session_id
            )
        )
        answered_questions = {row[0] for row in result.fetchall()}

        # Check if all required questions are answered
        return required_questions.issubset(answered_questions)

    async def calculate_progress(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """Calculate session progress."""
        from app.models.green_paper import Answer

        # Get all answers for this session
        result = await self.db.execute(
            select(Answer).where(
                Answer.session_id == session_id
            )
        )
        answers = result.scalars().all()

        # Count answered questions
        answered_count = len(answers)
        remaining_count = 6 - answered_count

        # Count required questions answered
        required_questions = {1, 2, 3, 4}
        answered_questions = {a.question_number for a in answers}
        required_remaining = len(required_questions - answered_questions)

        # Calculate percentage (0-100)
        percentage = int((answered_count / 6) * 100)

        return {
            "answered": answered_count,
            "remaining": remaining_count,
            "percentage": percentage,
            "required_remaining": required_remaining
        }

    async def get_session_statistics(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Get statistics for project's green-paper sessions."""
        from app.models.green_paper import (
            GreenPaperSession,
            Constitution,
            SessionStatus,
            ConstitutionStatus
        )
        from sqlalchemy import func

        # Count total sessions
        total_result = await self.db.execute(
            select(func.count(GreenPaperSession.id)).where(
                GreenPaperSession.project_id == str(project_id)
            )
        )
        total_sessions = total_result.scalar() or 0

        # Count completed sessions
        completed_result = await self.db.execute(
            select(func.count(GreenPaperSession.id)).where(
                GreenPaperSession.project_id == str(project_id),
                GreenPaperSession.status == SessionStatus.COMPLETED
            )
        )
        completed_sessions = completed_result.scalar() or 0

        # Count constitutions generated
        constitutions_result = await self.db.execute(
            select(func.count(Constitution.id)).where(
                Constitution.project_id == str(project_id)
            )
        )
        constitutions_generated = constitutions_result.scalar() or 0

        # Count approved constitutions
        approved_result = await self.db.execute(
            select(func.count(Constitution.id)).where(
                Constitution.project_id == str(project_id),
                Constitution.status == ConstitutionStatus.APPROVED
            )
        )
        approved_constitutions = approved_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "constitutions_generated": constitutions_generated,
            "approved_constitutions": approved_constitutions
        }


class GreenPaperValidationError(Exception):
    """Raised when green-paper validation fails."""
    pass


class IncompleteSessionError(Exception):
    """Raised when session is incomplete."""
    pass


class InvalidStatusError(Exception):
    """Raised when resource status is invalid."""
    pass

"""
Self-Questioning API Endpoints

Week 23-24: API for agent self-improvement metrics and training management

Endpoints:
- GET /api/self-questioning/sessions - List training sessions
- POST /api/self-questioning/sessions - Start new training session
- GET /api/self-questioning/sessions/{id} - Get session details
- GET /api/self-questioning/metrics - Get improvement metrics
- GET /api/self-questioning/questions/{agent} - Get agent's questions
- POST /api/self-questioning/schedule - Schedule training
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

router = APIRouter(prefix="/api/self-questioning", tags=["Self-Questioning"])


# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class AgentName(str, Enum):
    FELIX = "Felix"
    MARCUS = "Marcus"
    QUINN = "Quinn"
    BETTY = "Betty"
    ELIZA = "Eliza"
    TESSA = "Tessa"
    MIGUEL = "Miguel"
    DIANA = "Diana"
    PETER = "Peter"
    PAUL = "Paul"


class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuestionCategory(str, Enum):
    PERFORMANCE_GAP = "performance_gap"
    EDGE_CASE = "edge_case"
    KNOWLEDGE_GAP = "knowledge_gap"
    SKILL_IMPROVEMENT = "skill_improvement"
    PATTERN_DISCOVERY = "pattern_discovery"


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on_demand"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TrainingSessionConfig(BaseModel):
    agent_name: AgentName
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    max_tasks: int = Field(default=5, ge=1, le=20)
    include_edge_cases: bool = True
    improvement_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    max_time_per_task: int = Field(default=30, ge=5, le=120)
    enable_validation: bool = True
    auto_retry: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)


class TrainingSessionCreate(BaseModel):
    config: TrainingSessionConfig


class SelfQuestion(BaseModel):
    id: str
    agent_name: AgentName
    category: QuestionCategory
    question: str
    context: str
    priority: int = Field(ge=1, le=10)
    created_at: datetime
    metadata: Dict[str, Any] = {}


class SyntheticTask(BaseModel):
    id: str
    agent_name: AgentName
    title: str
    description: str
    difficulty: TaskDifficulty
    category: QuestionCategory
    expected_outcome: str
    validation_criteria: List[str]
    hints: List[str] = []
    time_limit: Optional[int] = None
    created_at: datetime


class TrainingTaskResult(BaseModel):
    id: str
    task_id: str
    status: str
    attempts: int
    score: Optional[float] = None
    validation_passed: Optional[bool] = None
    feedback: List[str] = []
    time_spent: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SessionMetrics(BaseModel):
    tasks_attempted: int
    tasks_completed: int
    tasks_failed: int
    average_score: float
    total_time_spent: float
    improvement_measured: float


class TrainingSessionResponse(BaseModel):
    id: str
    agent_name: AgentName
    status: SessionStatus
    config: TrainingSessionConfig
    started_at: datetime
    completed_at: Optional[datetime] = None
    questions_generated: int
    tasks_generated: int
    edge_cases_discovered: int
    metrics: SessionMetrics
    insights: List[str] = []
    recommendations: List[str] = []


class TrainingSchedule(BaseModel):
    id: str
    agent_name: AgentName
    frequency: ScheduleFrequency
    next_run: datetime
    last_run: Optional[datetime] = None
    config: TrainingSessionConfig
    enabled: bool = True


class ScheduleCreate(BaseModel):
    agent_name: AgentName
    frequency: ScheduleFrequency
    config: Optional[TrainingSessionConfig] = None


class ImprovementMetrics(BaseModel):
    agent_name: AgentName
    total_sessions: int
    total_tasks_completed: int
    average_score: float
    improvement_trend: float  # Positive = improving
    top_strengths: List[str]
    areas_for_improvement: List[str]
    last_session: Optional[datetime] = None
    recommended_focus: str


class AllAgentMetrics(BaseModel):
    generated_at: datetime
    total_sessions: int
    total_questions_generated: int
    total_tasks_completed: int
    overall_improvement: float
    agents: List[ImprovementMetrics]


# ============================================================================
# IN-MEMORY STORAGE (Replace with DB in production)
# ============================================================================

_sessions: Dict[str, TrainingSessionResponse] = {}
_schedules: Dict[str, TrainingSchedule] = {}
_questions: Dict[str, List[SelfQuestion]] = {}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "self-questioning",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/sessions", response_model=List[TrainingSessionResponse])
async def list_sessions(
    agent_name: Optional[AgentName] = None,
    status: Optional[SessionStatus] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List all training sessions with optional filters"""
    sessions = list(_sessions.values())

    if agent_name:
        sessions = [s for s in sessions if s.agent_name == agent_name]

    if status:
        sessions = [s for s in sessions if s.status == status]

    # Sort by started_at descending
    sessions.sort(key=lambda x: x.started_at, reverse=True)

    return sessions[offset:offset + limit]


@router.post("/sessions", response_model=TrainingSessionResponse)
async def create_session(request: TrainingSessionCreate):
    """Start a new training session for an agent"""
    session_id = f"ts-{uuid.uuid4().hex[:8]}"

    # Create session with mock data (in production, this would trigger the TypeScript workflow)
    session = TrainingSessionResponse(
        id=session_id,
        agent_name=request.config.agent_name,
        status=SessionStatus.RUNNING,
        config=request.config,
        started_at=datetime.utcnow(),
        questions_generated=0,
        tasks_generated=0,
        edge_cases_discovered=0,
        metrics=SessionMetrics(
            tasks_attempted=0,
            tasks_completed=0,
            tasks_failed=0,
            average_score=0.0,
            total_time_spent=0.0,
            improvement_measured=0.0
        ),
        insights=[],
        recommendations=[]
    )

    _sessions[session_id] = session

    # Simulate running (in production, call TypeScript service)
    await _simulate_session_execution(session)

    return session


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(session_id: str):
    """Get details of a specific training session"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return _sessions[session_id]


@router.delete("/sessions/{session_id}")
async def cancel_session(session_id: str):
    """Cancel a running training session"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]

    if session.status == SessionStatus.RUNNING:
        session.status = SessionStatus.CANCELLED
        session.completed_at = datetime.utcnow()

    return {"message": f"Session {session_id} cancelled", "status": session.status}


@router.get("/metrics", response_model=AllAgentMetrics)
async def get_all_metrics():
    """Get improvement metrics for all agents"""
    agent_metrics = []

    for agent in AgentName:
        agent_sessions = [s for s in _sessions.values() if s.agent_name == agent]

        if agent_sessions:
            completed = [s for s in agent_sessions if s.status == SessionStatus.COMPLETED]
            total_tasks = sum(s.metrics.tasks_completed for s in completed)
            avg_score = sum(s.metrics.average_score for s in completed) / len(completed) if completed else 0

            agent_metrics.append(ImprovementMetrics(
                agent_name=agent,
                total_sessions=len(agent_sessions),
                total_tasks_completed=total_tasks,
                average_score=avg_score,
                improvement_trend=0.05 if avg_score > 7 else -0.02,
                top_strengths=_get_agent_strengths(agent),
                areas_for_improvement=_get_agent_improvements(agent),
                last_session=max((s.started_at for s in agent_sessions), default=None),
                recommended_focus=_get_recommended_focus(agent)
            ))
        else:
            agent_metrics.append(ImprovementMetrics(
                agent_name=agent,
                total_sessions=0,
                total_tasks_completed=0,
                average_score=0.0,
                improvement_trend=0.0,
                top_strengths=[],
                areas_for_improvement=["No training data yet"],
                last_session=None,
                recommended_focus="Start initial training session"
            ))

    return AllAgentMetrics(
        generated_at=datetime.utcnow(),
        total_sessions=len(_sessions),
        total_questions_generated=sum(len(q) for q in _questions.values()),
        total_tasks_completed=sum(s.metrics.tasks_completed for s in _sessions.values()),
        overall_improvement=sum(m.improvement_trend for m in agent_metrics) / len(agent_metrics) if agent_metrics else 0,
        agents=agent_metrics
    )


@router.get("/metrics/{agent_name}", response_model=ImprovementMetrics)
async def get_agent_metrics(agent_name: AgentName):
    """Get improvement metrics for a specific agent"""
    agent_sessions = [s for s in _sessions.values() if s.agent_name == agent_name]

    if not agent_sessions:
        return ImprovementMetrics(
            agent_name=agent_name,
            total_sessions=0,
            total_tasks_completed=0,
            average_score=0.0,
            improvement_trend=0.0,
            top_strengths=[],
            areas_for_improvement=["No training data yet"],
            last_session=None,
            recommended_focus="Start initial training session"
        )

    completed = [s for s in agent_sessions if s.status == SessionStatus.COMPLETED]
    total_tasks = sum(s.metrics.tasks_completed for s in completed)
    avg_score = sum(s.metrics.average_score for s in completed) / len(completed) if completed else 0

    return ImprovementMetrics(
        agent_name=agent_name,
        total_sessions=len(agent_sessions),
        total_tasks_completed=total_tasks,
        average_score=avg_score,
        improvement_trend=0.05 if avg_score > 7 else -0.02,
        top_strengths=_get_agent_strengths(agent_name),
        areas_for_improvement=_get_agent_improvements(agent_name),
        last_session=max((s.started_at for s in agent_sessions), default=None),
        recommended_focus=_get_recommended_focus(agent_name)
    )


@router.get("/questions/{agent_name}", response_model=List[SelfQuestion])
async def get_agent_questions(
    agent_name: AgentName,
    category: Optional[QuestionCategory] = None,
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get self-generated questions for an agent"""
    questions = _questions.get(agent_name.value, [])

    if category:
        questions = [q for q in questions if q.category == category]

    return questions[:limit]


@router.get("/schedules", response_model=List[TrainingSchedule])
async def list_schedules(
    agent_name: Optional[AgentName] = None,
    enabled_only: bool = False
):
    """List all training schedules"""
    schedules = list(_schedules.values())

    if agent_name:
        schedules = [s for s in schedules if s.agent_name == agent_name]

    if enabled_only:
        schedules = [s for s in schedules if s.enabled]

    return schedules


@router.post("/schedules", response_model=TrainingSchedule)
async def create_schedule(request: ScheduleCreate):
    """Create a training schedule for an agent"""
    schedule_id = f"sched-{uuid.uuid4().hex[:8]}"

    # Calculate next run based on frequency
    next_run = _calculate_next_run(request.frequency)

    schedule = TrainingSchedule(
        id=schedule_id,
        agent_name=request.agent_name,
        frequency=request.frequency,
        next_run=next_run,
        config=request.config or TrainingSessionConfig(agent_name=request.agent_name),
        enabled=True
    )

    _schedules[schedule_id] = schedule
    return schedule


@router.put("/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    """Enable or disable a training schedule"""
    if schedule_id not in _schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule = _schedules[schedule_id]
    schedule.enabled = not schedule.enabled

    return {"schedule_id": schedule_id, "enabled": schedule.enabled}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a training schedule"""
    if schedule_id not in _schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")

    del _schedules[schedule_id]
    return {"message": f"Schedule {schedule_id} deleted"}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _simulate_session_execution(session: TrainingSessionResponse):
    """Simulate session execution (in production, call TypeScript service)"""
    import random

    # Simulate questions and tasks
    session.questions_generated = random.randint(3, 10)
    session.tasks_generated = random.randint(3, 8)
    session.edge_cases_discovered = random.randint(1, 5)

    # Simulate metrics
    tasks_attempted = session.tasks_generated
    tasks_completed = random.randint(int(tasks_attempted * 0.6), tasks_attempted)
    tasks_failed = tasks_attempted - tasks_completed

    session.metrics = SessionMetrics(
        tasks_attempted=tasks_attempted,
        tasks_completed=tasks_completed,
        tasks_failed=tasks_failed,
        average_score=random.uniform(5.5, 9.0),
        total_time_spent=random.uniform(10, 60),
        improvement_measured=random.uniform(-0.05, 0.15)
    )

    # Generate insights
    session.insights = [
        f"{session.agent_name.value} completed {tasks_completed}/{tasks_attempted} tasks",
        f"Average score: {session.metrics.average_score:.1f}/10"
    ]

    if session.metrics.improvement_measured > 0:
        session.insights.append(f"Improvement of {session.metrics.improvement_measured*100:.1f}% measured")

    # Generate recommendations
    session.recommendations = [
        f"Focus on {_get_recommended_focus(session.agent_name)} in next session"
    ]

    if tasks_failed > 0:
        session.recommendations.append(f"Review {tasks_failed} failed tasks for patterns")

    session.status = SessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()

    # Store generated questions
    _questions[session.agent_name.value] = _generate_mock_questions(session.agent_name)


def _generate_mock_questions(agent_name: AgentName) -> List[SelfQuestion]:
    """Generate mock questions for an agent"""
    questions = []
    templates = _get_question_templates(agent_name)

    for i, (category, question) in enumerate(templates[:5]):
        questions.append(SelfQuestion(
            id=f"sq-{uuid.uuid4().hex[:8]}",
            agent_name=agent_name,
            category=category,
            question=question,
            context=f"{agent_name.value} performance area",
            priority=10 - i,
            created_at=datetime.utcnow(),
            metadata={"triggered_by": "performance_analysis"}
        ))

    return questions


def _get_question_templates(agent_name: AgentName) -> List[tuple]:
    """Get question templates for an agent"""
    templates = {
        AgentName.FELIX: [
            (QuestionCategory.PERFORMANCE_GAP, "What architectural patterns am I not considering?"),
            (QuestionCategory.EDGE_CASE, "How should I handle partial failures?"),
            (QuestionCategory.KNOWLEDGE_GAP, "What microservice patterns should I learn?"),
        ],
        AgentName.MARCUS: [
            (QuestionCategory.PERFORMANCE_GAP, "Why are my refactorings causing regressions?"),
            (QuestionCategory.SKILL_IMPROVEMENT, "How can I make refactoring safer?"),
        ],
        AgentName.QUINN: [
            (QuestionCategory.EDGE_CASE, "What security vulnerabilities am I missing?"),
            (QuestionCategory.KNOWLEDGE_GAP, "What OWASP checks should I add?"),
        ],
    }
    return templates.get(agent_name, [(QuestionCategory.SKILL_IMPROVEMENT, "How can I improve?")])


def _get_agent_strengths(agent_name: AgentName) -> List[str]:
    """Get mock strengths for an agent"""
    strengths = {
        AgentName.FELIX: ["API design", "System decomposition"],
        AgentName.MARCUS: ["Code health analysis", "Dependency management"],
        AgentName.QUINN: ["Security scanning", "Vulnerability detection"],
        AgentName.BETTY: ["Root cause analysis", "Debugging"],
        AgentName.ELIZA: ["Complexity assessment", "Risk evaluation"],
        AgentName.TESSA: ["Test coverage", "Edge case detection"],
        AgentName.MIGUEL: ["Data migration", "Rollback procedures"],
        AgentName.DIANA: ["Technical writing", "Documentation clarity"],
        AgentName.PETER: ["Requirement gathering", "User stories"],
        AgentName.PAUL: ["Resource planning", "Timeline management"],
    }
    return strengths.get(agent_name, ["General competency"])


def _get_agent_improvements(agent_name: AgentName) -> List[str]:
    """Get mock areas for improvement for an agent"""
    improvements = {
        AgentName.FELIX: ["Event-driven patterns", "Scalability considerations"],
        AgentName.MARCUS: ["Breaking change detection", "Automated fixes"],
        AgentName.QUINN: ["Compliance requirements", "Advanced security patterns"],
        AgentName.BETTY: ["Race condition detection", "Performance debugging"],
        AgentName.ELIZA: ["Uncertainty communication", "Historical calibration"],
        AgentName.TESSA: ["Mutation testing", "Performance tests"],
        AgentName.MIGUEL: ["Zero-downtime migrations", "Cross-platform compatibility"],
        AgentName.DIANA: ["Interactive examples", "Troubleshooting guides"],
        AgentName.PETER: ["Acceptance criteria clarity", "Edge case requirements"],
        AgentName.PAUL: ["Risk identification", "Buffer estimation"],
    }
    return improvements.get(agent_name, ["Continuous learning"])


def _get_recommended_focus(agent_name: AgentName) -> str:
    """Get recommended focus area for an agent"""
    focus = {
        AgentName.FELIX: "event-driven architecture patterns",
        AgentName.MARCUS: "automated refactoring safety checks",
        AgentName.QUINN: "advanced OWASP vulnerability detection",
        AgentName.BETTY: "concurrent bug reproduction techniques",
        AgentName.ELIZA: "historical estimation calibration",
        AgentName.TESSA: "mutation testing integration",
        AgentName.MIGUEL: "zero-downtime migration strategies",
        AgentName.DIANA: "interactive documentation techniques",
        AgentName.PETER: "measurable acceptance criteria",
        AgentName.PAUL: "risk-adjusted planning buffers",
    }
    return focus.get(agent_name, "general skill improvement")


def _calculate_next_run(frequency: ScheduleFrequency) -> datetime:
    """Calculate next run time based on frequency"""
    now = datetime.utcnow()

    if frequency == ScheduleFrequency.DAILY:
        return now + timedelta(days=1)
    elif frequency == ScheduleFrequency.WEEKLY:
        return now + timedelta(weeks=1)
    else:  # ON_DEMAND
        return now

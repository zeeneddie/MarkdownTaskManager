"""
ROADMAP Import Script

Imports ROADMAP.md content into the platform as Epics/Features/Stories/Tasks.

Mapping:
- Fase (Phase) -> Epic
- Week -> Feature
- Deliverable item -> Story
- Sub-tasks (for IN_PROGRESS/PLANNED) -> Tasks

Status mapping:
- DONE/COMPLETE -> completed
- IN PROGRESS -> in_progress
- PLANNED -> draft (backlog)

Usage:
    python -m app.scripts.import_roadmap

Author: Claude Code (Week 58)
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.green_paper import Constitution, Specification, ConstitutionStatus, SpecificationStatus
from app.models.task_hierarchy import Epic, Feature, Story, Task, EpicStatus, FeatureStatus, StoryStatus, TaskStatus, Priority


@dataclass
class ParsedWeek:
    """Parsed week data from ROADMAP."""
    number: int
    title: str
    status: str  # DONE, IN_PROGRESS, PLANNED
    deliverables: List[str] = field(default_factory=list)
    output_summary: Optional[str] = None
    days: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedPhase:
    """Parsed phase (Fase) data from ROADMAP."""
    number: int
    title: str
    weeks_range: str
    status: str
    key_deliverables: str
    weeks: List[ParsedWeek] = field(default_factory=list)


def parse_roadmap(content: str) -> Dict[str, Any]:
    """Parse ROADMAP.md content into structured data."""

    result = {
        "phases": [],
        "weeks": [],
        "milestones": [],
        "current_week": None,
    }

    # Parse Completed Phases table
    # | Fase 1 | 1-4 | DONE | FastAPI, PostgreSQL, Frontend |
    phase_pattern = r'\| Fase (\d+) \| ([\d-]+) \| (DONE|IN PROGRESS|PLANNED) \| (.+?) \|'
    for match in re.finditer(phase_pattern, content):
        phase = ParsedPhase(
            number=int(match.group(1)),
            title=f"Fase {match.group(1)}",
            weeks_range=match.group(2),
            status=match.group(3).replace(" ", "_").upper(),
            key_deliverables=match.group(4).strip(),
        )
        result["phases"].append(phase)

    # Parse Future Phases table
    # | Fase 5 | 17-20 | Quality & Testing | Planned |
    future_phase_pattern = r'\| Fase (\d+) \| ([\d-]+) \| (.+?) \| (Planned|In Progress|Done) \|'
    for match in re.finditer(future_phase_pattern, content):
        # Check if already parsed
        phase_num = int(match.group(1))
        if not any(p.number == phase_num for p in result["phases"]):
            phase = ParsedPhase(
                number=phase_num,
                title=f"Fase {phase_num}: {match.group(3).strip()}",
                weeks_range=match.group(2),
                status=match.group(4).upper().replace(" ", "_"),
                key_deliverables=match.group(3).strip(),
            )
            result["phases"].append(phase)

    # Parse Weekly Progress History
    # ### Week 57 COMPLETE (28 Nov 2025)
    week_header_pattern = r'### Week (\d+) (COMPLETE|IN PROGRESS|PLANNED).*?\n'
    completed_pattern = r'\*\*Completed:\*\*\n((?:- .+\n)+)'
    output_pattern = r'\*\*Output:\*\* (.+)'

    # Find all week sections
    week_sections = re.split(r'### Week \d+', content)
    week_headers = re.findall(r'### Week (\d+) (COMPLETE|IN PROGRESS|PLANNED)', content)

    for i, (week_num, status) in enumerate(week_headers):
        if i + 1 < len(week_sections):
            section = week_sections[i + 1]

            # Extract deliverables
            deliverables = []
            completed_match = re.search(r'\*\*Completed:\*\*\n((?:- .+\n)+)', section)
            if completed_match:
                deliverables = [
                    line.strip('- \n')
                    for line in completed_match.group(1).split('\n')
                    if line.strip().startswith('-')
                ]

            # Extract output summary
            output_match = re.search(r'\*\*Output:\*\* (.+)', section)
            output_summary = output_match.group(1) if output_match else None

            week = ParsedWeek(
                number=int(week_num),
                title=f"Week {week_num}",
                status=status.replace(" ", "_").upper(),
                deliverables=deliverables,
                output_summary=output_summary,
            )
            result["weeks"].append(week)

    # Parse detailed week plans (Week 54-58 format)
    # | Dag | Taak | Output | Lines Est. | Status |
    # | 1 | Provider Registry | `providers/` module | 400 | DONE |
    day_pattern = r'\| (\d+) \| (.+?) \| (.+?) \| [\d~]+.*? \| *([\w\s]+)? *\|'

    # Find Week 54-58 sections with day details
    for week_num in [54, 55, 56, 57, 58, 59]:
        week_section_match = re.search(
            rf'### Week {week_num}[:\s].*?\n(.*?)(?=### Week|\Z)',
            content,
            re.DOTALL
        )
        if week_section_match:
            section = week_section_match.group(1)
            days = []
            for day_match in re.finditer(day_pattern, section):
                status_text = day_match.group(4).strip() if day_match.group(4) else "PLANNED"
                days.append({
                    "day": int(day_match.group(1)),
                    "task": day_match.group(2).strip(),
                    "output": day_match.group(3).strip(),
                    "status": status_text.upper().replace(" ", "_"),
                })

            # Find or create week
            existing_week = next((w for w in result["weeks"] if w.number == week_num), None)
            if existing_week:
                existing_week.days = days
            elif days:
                # Determine overall status from days
                if all(d["status"] in ["DONE", "COMPLETE"] for d in days):
                    status = "COMPLETE"
                elif any(d["status"] == "IN_PROGRESS" for d in days):
                    status = "IN_PROGRESS"
                else:
                    status = "PLANNED"

                week = ParsedWeek(
                    number=week_num,
                    title=f"Week {week_num}",
                    status=status,
                    deliverables=[d["task"] for d in days],
                    days=days,
                )
                result["weeks"].append(week)

    # Sort phases and weeks
    result["phases"].sort(key=lambda p: p.number)
    result["weeks"].sort(key=lambda w: w.number)

    return result


def map_status_to_epic(status: str) -> str:
    """Map ROADMAP status to Epic status."""
    mapping = {
        "DONE": EpicStatus.COMPLETED,
        "COMPLETE": EpicStatus.COMPLETED,
        "IN_PROGRESS": EpicStatus.IN_PROGRESS,
        "PLANNED": EpicStatus.PLANNED,
        "DRAFT": EpicStatus.DRAFT,
    }
    return mapping.get(status, EpicStatus.DRAFT)


def map_status_to_feature(status: str) -> str:
    """Map ROADMAP status to Feature status."""
    mapping = {
        "DONE": FeatureStatus.COMPLETED,
        "COMPLETE": FeatureStatus.COMPLETED,
        "IN_PROGRESS": FeatureStatus.IN_PROGRESS,
        "PLANNED": FeatureStatus.PLANNED,
        "DRAFT": FeatureStatus.DRAFT,
    }
    return mapping.get(status, FeatureStatus.DRAFT)


def map_status_to_story(status: str) -> str:
    """Map ROADMAP status to Story status."""
    mapping = {
        "DONE": StoryStatus.DONE,
        "COMPLETE": StoryStatus.DONE,
        "IN_PROGRESS": StoryStatus.IN_PROGRESS,
        "PLANNED": StoryStatus.READY,
        "DRAFT": StoryStatus.DRAFT,
    }
    return mapping.get(status, StoryStatus.DRAFT)


def map_status_to_task(status: str) -> str:
    """Map ROADMAP status to Task status."""
    mapping = {
        "DONE": TaskStatus.DONE,
        "COMPLETE": TaskStatus.DONE,
        "IN_PROGRESS": TaskStatus.IN_PROGRESS,
        "PLANNED": TaskStatus.TODO,
        "DRAFT": TaskStatus.TODO,
    }
    return mapping.get(status, TaskStatus.TODO)


async def create_specification_for_brownpaper(
    db: AsyncSession,
    project_id: str,
) -> uuid.UUID:
    """Create a Constitution and Specification for Brown Paper import."""

    # First check if we need to create a GreenPaperSession
    from app.models.green_paper import GreenPaperSession, SessionStatus

    session = GreenPaperSession(
        id=uuid.uuid4(),
        project_id=project_id,
        session_type="brown-paper-import",
        status=SessionStatus.COMPLETED,
        current_question=6,
        total_questions=6,
        progress_percentage=100,
        generation_metadata={"source": "roadmap_import", "imported_at": datetime.now(timezone.utc).isoformat()},
    )
    db.add(session)

    # Constitution content
    constitution_json = {
        "mission_vision": {
            "mission": "Multi-Stack AI Agent Platform voor intelligent task management",
            "vision": "Een platform dat meerdere projecten beheert met gespecialiseerde AI agents",
        },
        "core_principles": [
            {"name": "AI-First", "description": "Agents als primaire workflow executors"},
            {"name": "Multi-Stack", "description": "Ondersteuning voor Python, JS, Go, Rust"},
            {"name": "Quality Gates", "description": "Automatische kwaliteitsvalidatie"},
        ],
        "key_requirements": [
            {"id": "REQ-001", "description": "10 Core Agents", "priority": "high"},
            {"id": "REQ-002", "description": "196+ API Endpoints", "priority": "high"},
            {"id": "REQ-003", "description": "15 Dashboards", "priority": "medium"},
        ],
        "constraints": [
            {"type": "technology", "constraint": "FastAPI backend, PostgreSQL database"},
        ],
        "risks": [
            {"risk": "API complexity", "severity": "medium", "mitigation": "Modular design"},
        ],
        "scope": {
            "in_scope": ["Task management", "Agent workflows", "Quality gates"],
            "out_of_scope": ["Mobile app", "Public cloud deployment"],
        },
        "success_criteria": [
            {"criterion": "95% agent success rate", "measurement": "Observability metrics"},
        ],
    }

    constitution_markdown = """# Project Constitution: Multi-Stack AI Agent Platform

## Mission & Vision
**Mission:** Multi-Stack AI Agent Platform voor intelligent task management
**Vision:** Een platform dat meerdere projecten beheert met gespecialiseerde AI agents

## Core Principles
1. **AI-First** - Agents als primaire workflow executors
2. **Multi-Stack** - Ondersteuning voor Python, JS, Go, Rust
3. **Quality Gates** - Automatische kwaliteitsvalidatie

## Key Requirements
- REQ-001: 10 Core Agents (high priority)
- REQ-002: 196+ API Endpoints (high priority)
- REQ-003: 15 Dashboards (medium priority)

## Scope
**In Scope:** Task management, Agent workflows, Quality gates
**Out of Scope:** Mobile app, Public cloud deployment

## Success Criteria
- 95% agent success rate (measured via Observability metrics)
"""

    # Create Constitution
    constitution = Constitution(
        id=uuid.uuid4(),
        session_id=session.id,
        project_id=project_id,
        content_json=constitution_json,
        content_markdown=constitution_markdown,
        word_count=len(constitution_markdown.split()),
        status=ConstitutionStatus.APPROVED,
        generated_by="brown_paper_import",
    )
    db.add(constitution)

    # Specification content
    specification_json = {
        "title": "Multi-Stack AI Agent Platform Specification",
        "executive_summary": "Complete platform voor AI-gedreven task management",
        "architecture": {
            "pattern": "3-Layer Agent Architecture",
            "layers": ["Core Agents", "Stack Templates", "Platform Agents"],
            "database": "PostgreSQL + ChromaDB",
        },
        "components": [
            {"name": "Backend API", "technology": "FastAPI"},
            {"name": "Frontend", "technology": "HTML/JS Dashboards"},
            {"name": "Agents", "technology": "Ollama + Claude"},
        ],
        "data_model": {
            "tables": 58,
            "key_entities": ["Epic", "Feature", "Story", "Task", "Agent"],
        },
        "api_design": {
            "style": "REST",
            "endpoints": 196,
        },
    }

    specification_markdown = """# High-Level Design: Multi-Stack AI Agent Platform

## Executive Summary
Complete platform voor AI-gedreven task management met 10 agents, 196+ endpoints, en 15 dashboards.

## Architecture
- **Pattern:** 3-Layer Agent Architecture
- **Layers:** Core Agents, Stack Templates, Platform Agents
- **Database:** PostgreSQL + ChromaDB

## Components
1. Backend API (FastAPI)
2. Frontend (HTML/JS Dashboards)
3. Agents (Ollama + Claude)

## Data Model
- 58 database tables
- Key entities: Epic, Feature, Story, Task, Agent

## API Design
- Style: REST
- Endpoints: 196+
"""

    # Create Specification
    specification = Specification(
        id=uuid.uuid4(),
        constitution_id=constitution.id,
        project_id=project_id,
        content_json=specification_json,
        content_markdown=specification_markdown,
        status=SpecificationStatus.APPROVED,
        generated_by="brown_paper_import",
    )
    db.add(specification)
    await db.flush()

    return specification.id


async def import_roadmap_to_platform(
    db: AsyncSession,
    project_id: str = "MarkdownTaskManager",
    roadmap_path: str = "/home/eddie/Projects/MarkdownTaskManager/ROADMAP.md",
):
    """Import ROADMAP.md into platform as Epics/Features/Stories/Tasks."""

    print(f"Reading ROADMAP from {roadmap_path}...")
    content = Path(roadmap_path).read_text()

    print("Parsing ROADMAP content...")
    parsed = parse_roadmap(content)

    print(f"Found {len(parsed['phases'])} phases and {len(parsed['weeks'])} weeks")

    # Create Specification for Brown Paper import
    print("Creating Constitution and Specification...")
    specification_id = await create_specification_for_brownpaper(db, project_id)

    # Import Phases as Epics
    print("\nImporting Phases as Epics...")
    epic_map = {}  # phase_number -> epic_id

    for i, phase in enumerate(parsed["phases"]):
        epic = Epic(
            id=uuid.uuid4(),
            specification_id=specification_id,
            project_id=project_id,
            title=phase.title,
            description=f"Key deliverables: {phase.key_deliverables}\nWeeks: {phase.weeks_range}",
            status=map_status_to_epic(phase.status),
            priority=Priority.HIGH if phase.number <= 4 else Priority.MEDIUM,
            business_value=phase.key_deliverables,
            sequence_number=i + 1,
            progress_percentage=100 if phase.status in ["DONE", "COMPLETE"] else 0,
            generated_by="roadmap_import",
        )
        db.add(epic)
        epic_map[phase.number] = epic.id
        print(f"  Created Epic: {phase.title} ({phase.status})")

    # Also create Epics for Week groups (54-58 Multi-Stack Platform)
    multistack_epic = Epic(
        id=uuid.uuid4(),
        specification_id=specification_id,
        project_id=project_id,
        title="Multi-Stack Platform Foundation (Week 54-58)",
        description="Transform single-project system into multi-stack agent platform.\n"
                   "Key deliverables: Provider Registry, Observability, Stack Templates, Brown Paper.",
        status=EpicStatus.IN_PROGRESS,
        priority=Priority.CRITICAL,
        business_value="Multi-LLM routing, Agent monitoring, Stack-specific agents",
        sequence_number=len(parsed["phases"]) + 1,
        progress_percentage=60,
        generated_by="roadmap_import",
    )
    db.add(multistack_epic)
    multistack_epic_id = multistack_epic.id
    print(f"  Created Epic: Multi-Stack Platform Foundation")

    await db.flush()

    # Import Weeks as Features
    print("\nImporting Weeks as Features...")
    feature_map = {}  # week_number -> feature_id

    for i, week in enumerate(parsed["weeks"]):
        # Determine parent epic
        if week.number >= 54:
            parent_epic_id = multistack_epic_id
        else:
            # Find appropriate phase
            parent_phase = None
            for phase in parsed["phases"]:
                if "-" in phase.weeks_range:
                    start, end = map(int, phase.weeks_range.split("-"))
                    if start <= week.number <= end:
                        parent_phase = phase.number
                        break
            parent_epic_id = epic_map.get(parent_phase, multistack_epic_id)

        feature = Feature(
            id=uuid.uuid4(),
            epic_id=parent_epic_id,
            project_id=project_id,
            title=f"Week {week.number}",
            description=f"Deliverables:\n" + "\n".join(f"- {d}" for d in week.deliverables[:10]),
            status=map_status_to_feature(week.status),
            priority=Priority.HIGH if week.status == "IN_PROGRESS" else Priority.MEDIUM,
            sequence_number=i + 1,
            progress_percentage=100 if week.status in ["DONE", "COMPLETE"] else 0,
            generated_by="roadmap_import",
            extra_metadata={
                "output_summary": week.output_summary,
                "days_count": len(week.days),
            },
        )
        db.add(feature)
        feature_map[week.number] = feature.id
        print(f"  Created Feature: Week {week.number} ({week.status})")

    await db.flush()

    # Import Deliverables as Stories
    print("\nImporting Deliverables as Stories...")
    story_count = 0

    for week in parsed["weeks"]:
        feature_id = feature_map.get(week.number)
        if not feature_id:
            continue

        # Create stories from deliverables
        for j, deliverable in enumerate(week.deliverables):
            story = Story(
                id=uuid.uuid4(),
                feature_id=feature_id,
                project_id=project_id,
                title=deliverable[:200],
                description=f"As a developer, I want {deliverable.lower()} so that the platform functionality is extended.",
                user_type="Developer",
                user_goal=deliverable,
                user_benefit="Platform extension",
                status=map_status_to_story(week.status),
                priority=Priority.MEDIUM,
                acceptance_criteria=[
                    {"criterion": f"Implementation of {deliverable[:50]}... is complete"},
                    {"criterion": "Tests pass"},
                    {"criterion": "Documentation updated"},
                ],
                story_points=3 if "API" in deliverable or "Service" in deliverable else 2,
                sequence_number=j + 1,
                generated_by="roadmap_import",
            )
            db.add(story)
            story_count += 1

        # Create tasks from day details (for weeks 54-58)
        if week.days:
            for day in week.days:
                # Find or create story for this day
                day_story = Story(
                    id=uuid.uuid4(),
                    feature_id=feature_id,
                    project_id=project_id,
                    title=f"Day {day['day']}: {day['task'][:150]}",
                    description=f"Output: {day['output']}",
                    user_type="Developer",
                    user_goal=day['task'],
                    user_benefit="Sprint deliverable",
                    status=map_status_to_story(day['status']),
                    priority=Priority.HIGH,
                    acceptance_criteria=[
                        {"criterion": f"{day['task']} completed"},
                        {"criterion": f"Output: {day['output'][:100]}"},
                    ],
                    story_points=5,
                    sequence_number=100 + day['day'],
                    generated_by="roadmap_import",
                )
                db.add(day_story)
                story_count += 1

                # Create task for non-done items
                if day['status'] not in ["DONE", "COMPLETE"]:
                    task = Task(
                        id=uuid.uuid4(),
                        story_id=day_story.id,
                        project_id=project_id,
                        title=f"Implement: {day['task'][:150]}",
                        description=f"Expected output: {day['output']}",
                        status=map_status_to_task(day['status']),
                        priority=Priority.HIGH,
                        task_type="backend" if "API" in day['task'] or "Service" in day['task'] else "frontend",
                        estimated_hours=4.0,
                        sequence_number=1,
                        generated_by="roadmap_import",
                    )
                    db.add(task)

    print(f"  Created {story_count} Stories")

    await db.commit()
    print("\n" + "=" * 50)
    print("ROADMAP import complete!")
    print(f"  Epics: {len(parsed['phases']) + 1}")
    print(f"  Features: {len(parsed['weeks'])}")
    print(f"  Stories: {story_count}")
    print("=" * 50)


async def main():
    """Main entry point."""
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        await import_roadmap_to_platform(db)


if __name__ == "__main__":
    asyncio.run(main())

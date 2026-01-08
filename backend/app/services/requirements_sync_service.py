# backend/app/services/requirements_sync_service.py
"""
Requirements Sync Service - Week 117

Bidirectional sync between MarQed database and rmtoo files.

Features:
- Export requirements to .req files
- Import requirements from .req files
- Detect and handle conflicts
- Git integration (auto-commit)
- Generate documentation (HTML, PDF, graphs)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from pathlib import Path
import os
import subprocess
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.rmtoo import (
    RmtooRequirement,
    RmtooTopic,
    RmtooSyncSession,
    RmtooExport,
    SyncDirection,
    SyncStatus,
    ExportType,
)
from app.services.rmtoo_adapter_service import RmtooAdapterService


class RequirementsSyncService:
    """Service for syncing requirements between database and rmtoo files."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.adapter = RmtooAdapterService(db)

    async def sync_db_to_files(
        self,
        project_id: int,
        output_path: str,
        git_auto_commit: bool = False,
    ) -> RmtooSyncSession:
        """Export all requirements from database to rmtoo files."""
        session = RmtooSyncSession(
            id=uuid4(),
            project_id=project_id,
            direction=SyncDirection.DB_TO_FILES.value,
            status=SyncStatus.RUNNING.value,
            output_path=output_path,
            git_auto_commit=git_auto_commit,
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        try:
            # Create output directory structure
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            req_dir = output_dir / "requirements"
            req_dir.mkdir(exist_ok=True)
            topics_dir = output_dir / "topics"
            topics_dir.mkdir(exist_ok=True)

            files_written = []
            requirements_created = 0

            # Export topics
            topics = await self._get_topics(project_id)
            for topic in topics:
                topic_file = topics_dir / f"{topic.name}.tpc"
                content = self._generate_topic_file(topic)
                topic_file.write_text(content)
                files_written.append(str(topic_file))

            session.topics_synced = len(topics)

            # Export requirements by topic
            requirements = await self.adapter.get_requirements_by_project(project_id)
            for req in requirements:
                # Create file in topic subdirectory or root
                if req.topic:
                    topic_req_dir = req_dir / req.topic
                    topic_req_dir.mkdir(exist_ok=True)
                    req_file = topic_req_dir / f"{req.name}.req"
                else:
                    req_file = req_dir / f"{req.name}.req"

                content = req.rmtoo_content or req.to_rmtoo_format()
                req_file.write_text(content)
                files_written.append(str(req_file))
                requirements_created += 1

            session.requirements_created = requirements_created
            session.files_written = files_written

            # Generate configuration file
            config_file = output_dir / "rmtoo.yaml"
            config_content = self._generate_config(project_id, output_path)
            config_file.write_text(config_content)
            files_written.append(str(config_file))

            # Git auto-commit if enabled
            if git_auto_commit and self._is_git_repo(output_dir):
                commit_hash = await self._git_commit(
                    output_dir,
                    f"[MarQed] Sync requirements for project {project_id}"
                )
                session.git_commit_hash = commit_hash

            session.status = SyncStatus.COMPLETED.value
            session.completed_at = datetime.utcnow()
            session.duration_ms = int((session.completed_at - session.started_at).total_seconds() * 1000)

        except Exception as e:
            session.status = SyncStatus.FAILED.value
            session.errors = [str(e)]
            session.completed_at = datetime.utcnow()

        await self.db.commit()
        return session

    async def sync_files_to_db(
        self,
        project_id: int,
        input_path: str,
    ) -> RmtooSyncSession:
        """Import requirements from rmtoo files to database."""
        session = RmtooSyncSession(
            id=uuid4(),
            project_id=project_id,
            direction=SyncDirection.FILES_TO_DB.value,
            status=SyncStatus.RUNNING.value,
            output_path=input_path,
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        try:
            input_dir = Path(input_path)
            if not input_dir.exists():
                raise ValueError(f"Input path does not exist: {input_path}")

            requirements_created = 0
            requirements_updated = 0
            conflicts_detected = 0
            warnings = []

            # Find all .req files
            req_files = list(input_dir.rglob("*.req"))

            for req_file in req_files:
                try:
                    content = req_file.read_text()
                    parsed = self.adapter.parse_rmtoo_file(content)

                    if 'Name' not in parsed:
                        warnings.append(f"Skipping {req_file}: Missing Name field")
                        continue

                    # Check if requirement exists
                    existing = await self.adapter.get_requirement_by_name(
                        project_id, parsed['Name']
                    )

                    if existing:
                        # Check for conflicts
                        if existing.rmtoo_content != content:
                            conflicts_detected += 1
                            # For now, skip conflicts - could implement merge logic
                            warnings.append(f"Conflict detected for {parsed['Name']}")
                            continue
                        requirements_updated += 1
                    else:
                        # Import new requirement
                        await self.adapter.import_from_rmtoo_file(
                            project_id,
                            content,
                            str(req_file)
                        )
                        requirements_created += 1

                except Exception as e:
                    warnings.append(f"Error processing {req_file}: {str(e)}")

            # Import topics
            topic_files = list(input_dir.rglob("*.tpc"))
            topics_synced = 0
            for topic_file in topic_files:
                try:
                    await self._import_topic(project_id, topic_file)
                    topics_synced += 1
                except Exception as e:
                    warnings.append(f"Error importing topic {topic_file}: {str(e)}")

            session.requirements_created = requirements_created
            session.requirements_updated = requirements_updated
            session.conflicts_detected = conflicts_detected
            session.topics_synced = topics_synced
            session.warnings = warnings
            session.status = SyncStatus.COMPLETED.value
            session.completed_at = datetime.utcnow()
            session.duration_ms = int((session.completed_at - session.started_at).total_seconds() * 1000)

        except Exception as e:
            session.status = SyncStatus.FAILED.value
            session.errors = [str(e)]
            session.completed_at = datetime.utcnow()

        await self.db.commit()
        return session

    async def export_documentation(
        self,
        project_id: int,
        export_type: ExportType,
        output_path: str,
        include_topics: Optional[List[str]] = None,
        include_categories: Optional[List[str]] = None,
    ) -> RmtooExport:
        """Generate documentation from requirements."""
        export = RmtooExport(
            id=uuid4(),
            project_id=project_id,
            export_type=export_type.value,
            status=SyncStatus.RUNNING.value,
            output_path=output_path,
            include_topics=include_topics or [],
            include_categories=include_categories or [],
            started_at=datetime.utcnow(),
        )
        self.db.add(export)
        await self.db.flush()

        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get requirements
            requirements = await self.adapter.get_requirements_by_project(project_id)

            # Filter by topics and categories
            if include_topics:
                requirements = [r for r in requirements if r.topic in include_topics]
            if include_categories:
                requirements = [r for r in requirements if r.category in include_categories]

            export.requirements_included = len(requirements)

            if export_type == ExportType.HTML:
                await self._generate_html(requirements, output_dir, project_id)
            elif export_type == ExportType.MARKDOWN:
                await self._generate_markdown(requirements, output_dir, project_id)
            elif export_type == ExportType.GRAPH:
                await self._generate_dependency_graph(requirements, output_dir)
            elif export_type == ExportType.PDF:
                # PDF requires LaTeX - generate markdown as fallback
                await self._generate_markdown(requirements, output_dir, project_id)
                export.warnings = ["PDF export requires rmtoo with LaTeX. Generated markdown instead."]

            # Calculate file size
            total_size = sum(
                f.stat().st_size for f in output_dir.rglob("*") if f.is_file()
            )
            export.file_size_bytes = total_size

            export.status = SyncStatus.COMPLETED.value
            export.completed_at = datetime.utcnow()
            export.duration_ms = int((export.completed_at - export.started_at).total_seconds() * 1000)

        except Exception as e:
            export.status = SyncStatus.FAILED.value
            export.errors = [str(e)]
            export.completed_at = datetime.utcnow()

        await self.db.commit()
        return export

    async def _get_topics(self, project_id: int) -> List[RmtooTopic]:
        """Get all topics for a project."""
        result = await self.db.execute(
            select(RmtooTopic).where(
                RmtooTopic.project_id == project_id
            ).order_by(RmtooTopic.order_index)
        )
        return list(result.scalars().all())

    def _generate_topic_file(self, topic: RmtooTopic) -> str:
        """Generate rmtoo topic file content."""
        lines = [
            f"Name: {topic.name}",
        ]
        if topic.title:
            lines.append(f"Title: {topic.title}")
        if topic.description:
            lines.append(f"Description: {topic.description}")
        if topic.content:
            lines.append("")
            lines.append(topic.content)
        return '\n'.join(lines)

    def _generate_config(self, project_id: int, output_path: str) -> str:
        """Generate rmtoo configuration YAML."""
        return f"""# rmtoo configuration - Generated by MarQed
# Project ID: {project_id}
# Generated: {datetime.utcnow().isoformat()}

requirements:
  input:
    directory: requirements

topics:
  input:
    directory: topics

output:
  html:
    directory: output/html
  graph:
    directory: output/graphs
    format: svg

processing:
  analytics: true
  stats: true
"""

    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is a git repository."""
        git_dir = path / ".git"
        return git_dir.exists() or (path.parent / ".git").exists()

    async def _git_commit(self, path: Path, message: str) -> Optional[str]:
        """Commit changes to git repository."""
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=path,
                check=True,
                capture_output=True
            )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                return hash_result.stdout.strip()[:40]

        except Exception:
            pass

        return None

    async def _import_topic(self, project_id: int, topic_file: Path) -> RmtooTopic:
        """Import a topic from a .tpc file."""
        content = topic_file.read_text()
        parsed = self.adapter.parse_rmtoo_file(content)

        if 'Name' not in parsed:
            raise ValueError(f"Topic file missing Name: {topic_file}")

        # Check if exists
        result = await self.db.execute(
            select(RmtooTopic).where(
                and_(
                    RmtooTopic.project_id == project_id,
                    RmtooTopic.name == parsed['Name']
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.title = parsed.get('Title')
            existing.description = parsed.get('Description')
            return existing
        else:
            topic = RmtooTopic(
                id=uuid4(),
                project_id=project_id,
                name=parsed['Name'],
                title=parsed.get('Title'),
                description=parsed.get('Description'),
            )
            self.db.add(topic)
            return topic

    async def _generate_html(
        self,
        requirements: List[RmtooRequirement],
        output_dir: Path,
        project_id: int,
    ) -> None:
        """Generate HTML documentation."""
        html_file = output_dir / "requirements.html"

        # Group by topic
        by_topic: Dict[str, List[RmtooRequirement]] = {}
        for req in requirements:
            topic = req.topic or "Uncategorized"
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(req)

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Requirements - Project {project_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #1a1a2e; }}
        h2 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 10px; }}
        .requirement {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .req-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .req-name {{ font-weight: bold; font-size: 1.2em; color: #0f3460; }}
        .req-category {{ background: #e94560; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.9em; }}
        .req-category.BR {{ background: #1a1a2e; }}
        .req-category.FR {{ background: #16213e; }}
        .req-category.NFR {{ background: #0f3460; }}
        .req-category.TR {{ background: #533483; }}
        .req-category.CMP {{ background: #e94560; }}
        .req-desc {{ margin-top: 15px; line-height: 1.6; }}
        .req-meta {{ margin-top: 15px; font-size: 0.9em; color: #666; }}
        .validated {{ color: green; }}
        .not-validated {{ color: orange; }}
        .stats {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }}
        .stat-item {{ text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.8; }}
    </style>
</head>
<body>
    <h1>Requirements Documentation</h1>
    <p>Project {project_id} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>

    <div class="stats">
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{len(requirements)}</div>
                <div class="stat-label">Total Requirements</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len([r for r in requirements if r.validated])}</div>
                <div class="stat-label">Validated</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(by_topic)}</div>
                <div class="stat-label">Topics</div>
            </div>
        </div>
    </div>
"""

        for topic, reqs in sorted(by_topic.items()):
            html_content += f"    <h2>{topic}</h2>\n"
            for req in sorted(reqs, key=lambda r: r.name):
                validated_class = "validated" if req.validated else "not-validated"
                validated_text = "✓ Validated" if req.validated else "⚠ Not validated"
                html_content += f"""
    <div class="requirement">
        <div class="req-header">
            <span class="req-name">{req.name}</span>
            <span class="req-category {req.category}">{req.category}</span>
        </div>
        <div class="req-desc">{req.description}</div>
        <div class="req-meta">
            <span class="{validated_class}">{validated_text}</span>
            | Status: {req.status}
            | Confidence: {req.confidence:.0%} if req.confidence else 'N/A'
        </div>
    </div>
"""

        html_content += """
</body>
</html>
"""
        html_file.write_text(html_content)

    async def _generate_markdown(
        self,
        requirements: List[RmtooRequirement],
        output_dir: Path,
        project_id: int,
    ) -> None:
        """Generate Markdown documentation."""
        md_file = output_dir / "requirements.md"

        # Group by topic
        by_topic: Dict[str, List[RmtooRequirement]] = {}
        for req in requirements:
            topic = req.topic or "Uncategorized"
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(req)

        lines = [
            f"# Requirements Documentation",
            f"",
            f"**Project:** {project_id}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Total Requirements:** {len(requirements)}",
            f"**Validated:** {len([r for r in requirements if r.validated])}",
            f"",
            "---",
            "",
        ]

        for topic, reqs in sorted(by_topic.items()):
            lines.append(f"## {topic}")
            lines.append("")
            for req in sorted(reqs, key=lambda r: r.name):
                status = "✅" if req.validated else "⚠️"
                lines.append(f"### {req.name} {status}")
                lines.append("")
                lines.append(f"**Category:** {req.category}")
                lines.append(f"**Status:** {req.status}")
                if req.confidence:
                    lines.append(f"**Confidence:** {req.confidence:.0%}")
                lines.append("")
                lines.append(req.description)
                lines.append("")
                if req.rationale:
                    lines.append(f"*Rationale:* {req.rationale}")
                    lines.append("")
                if req.solved_by:
                    lines.append(f"**Solved by:** {', '.join(req.solved_by)}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        md_file.write_text('\n'.join(lines))

    async def _generate_dependency_graph(
        self,
        requirements: List[RmtooRequirement],
        output_dir: Path,
    ) -> None:
        """Generate dependency graph in DOT format."""
        dot_file = output_dir / "dependencies.dot"

        lines = [
            "digraph requirements {",
            "    rankdir=TB;",
            "    node [shape=box, style=filled];",
            "",
            "    // Category colors",
            '    node [fillcolor="#1a1a2e", fontcolor="white"];  // Default',
            "",
        ]

        # Color map
        colors = {
            "BR": "#1a1a2e",
            "FR": "#16213e",
            "NFR": "#0f3460",
            "TR": "#533483",
            "CMP": "#e94560",
        }

        # Add nodes
        for req in requirements:
            color = colors.get(req.category, "#1a1a2e")
            lines.append(f'    "{req.name}" [fillcolor="{color}", label="{req.name}\\n{req.category}"];')

        lines.append("")
        lines.append("    // Dependencies")

        # Add edges
        for req in requirements:
            if req.solved_by:
                for dep in req.solved_by:
                    lines.append(f'    "{req.name}" -> "{dep}";')
            if req.depends_on:
                for dep in req.depends_on:
                    lines.append(f'    "{dep}" -> "{req.name}" [style=dashed];')

        lines.append("}")

        dot_file.write_text('\n'.join(lines))

        # Try to generate SVG if graphviz is installed
        svg_file = output_dir / "dependencies.svg"
        try:
            subprocess.run(
                ["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # graphviz not installed, DOT file is still useful

    async def get_sync_history(
        self,
        project_id: int,
        limit: int = 10,
    ) -> List[RmtooSyncSession]:
        """Get sync session history for a project."""
        result = await self.db.execute(
            select(RmtooSyncSession).where(
                RmtooSyncSession.project_id == project_id
            ).order_by(RmtooSyncSession.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_export_history(
        self,
        project_id: int,
        limit: int = 10,
    ) -> List[RmtooExport]:
        """Get export history for a project."""
        result = await self.db.execute(
            select(RmtooExport).where(
                RmtooExport.project_id == project_id
            ).order_by(RmtooExport.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

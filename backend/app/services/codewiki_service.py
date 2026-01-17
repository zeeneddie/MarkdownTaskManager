"""
CodeWiki Service - Repository Documentation Analysis

Week 62: Code Understanding Integration

Features:
- CodeWiki CLI wrapper for repository analysis
- Module tree parsing and storage
- Diagram extraction and storage
- Agent context preparation
- Integration with Miguel, Felix, Quinn, Diana

Reference: github.com/zeeneddie/CodeWiki
"""

import asyncio
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.codewiki import (
    CodeWikiAnalysis, CodeWikiAnalysisStatus,
    CodeWikiModule, CodeWikiDiagram, DiagramType,
    CodeWikiAgentContext
)

logger = logging.getLogger(__name__)


class CodeWikiService:
    """
    Service for CodeWiki repository documentation analysis.

    Provides:
    - Repository analysis via CodeWiki CLI
    - Module tree parsing and hierarchy building
    - Diagram extraction (Mermaid)
    - Agent-specific context preparation
    """

    # Language detection patterns
    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
        "csharp": [".cs"],
        "go": [".go"],
        "rust": [".rs"],
    }

    # Mermaid diagram patterns
    MERMAID_PATTERN = re.compile(r'```mermaid\s*([\s\S]*?)```', re.MULTILINE)

    def __init__(self, db: Session):
        """Initialize CodeWiki service."""
        self.db = db

    def create_analysis(
        self,
        project_id: int,
        repository_path: str,
        branch: str = "main"
    ) -> CodeWikiAnalysis:
        """
        Create a new CodeWiki analysis session.

        Args:
            project_id: Project ID in database
            repository_path: Path to repository
            branch: Git branch to analyze

        Returns:
            Created analysis record
        """
        # Detect languages in repository
        languages = self._detect_languages(repository_path)

        analysis = CodeWikiAnalysis(
            project_id=project_id,
            repository_path=repository_path,
            branch=branch,
            languages_detected=languages,
            status=CodeWikiAnalysisStatus.PENDING,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        logger.info(f"Created CodeWiki analysis {analysis.id} for project {project_id}")
        return analysis

    def get_analysis(self, analysis_id: int) -> Optional[CodeWikiAnalysis]:
        """Get analysis by ID."""
        return self.db.query(CodeWikiAnalysis).filter(
            CodeWikiAnalysis.id == analysis_id
        ).first()

    def get_project_analyses(
        self,
        project_id: int,
        status: Optional[CodeWikiAnalysisStatus] = None
    ) -> List[CodeWikiAnalysis]:
        """Get all analyses for a project."""
        query = self.db.query(CodeWikiAnalysis).filter(
            CodeWikiAnalysis.project_id == project_id
        )
        if status:
            query = query.filter(CodeWikiAnalysis.status == status)
        return query.order_by(CodeWikiAnalysis.created_at.desc()).all()

    def get_latest_analysis(self, project_id: int) -> Optional[CodeWikiAnalysis]:
        """Get most recent completed analysis for project."""
        return self.db.query(CodeWikiAnalysis).filter(
            and_(
                CodeWikiAnalysis.project_id == project_id,
                CodeWikiAnalysis.status == CodeWikiAnalysisStatus.COMPLETED
            )
        ).order_by(CodeWikiAnalysis.completed_at.desc()).first()

    async def run_analysis(self, analysis_id: int) -> CodeWikiAnalysis:
        """
        Run CodeWiki analysis on repository.

        This is an async method that:
        1. Runs codewiki generate CLI
        2. Parses output files
        3. Stores modules and diagrams
        4. Prepares agent contexts

        Args:
            analysis_id: Analysis ID to run

        Returns:
            Updated analysis record
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Update status
        analysis.status = CodeWikiAnalysisStatus.SCANNING
        analysis.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            # Run CodeWiki CLI
            output_dir = await self._run_codewiki_cli(analysis)

            # Parse outputs
            analysis.status = CodeWikiAnalysisStatus.DOCUMENTING
            self.db.commit()

            await self._parse_codewiki_outputs(analysis, output_dir)

            # Generate agent contexts
            analysis.status = CodeWikiAnalysisStatus.GENERATING_DIAGRAMS
            self.db.commit()

            await self._prepare_agent_contexts(analysis)

            # Complete
            analysis.status = CodeWikiAnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now(timezone.utc)
            if analysis.started_at:
                analysis.duration_seconds = int(
                    (analysis.completed_at - analysis.started_at).total_seconds()
                )
            self.db.commit()

            logger.info(f"CodeWiki analysis {analysis_id} completed successfully")

        except Exception as e:
            analysis.status = CodeWikiAnalysisStatus.FAILED
            analysis.status_message = str(e)
            self.db.commit()
            logger.error(f"CodeWiki analysis {analysis_id} failed: {e}")
            raise

        return analysis

    async def _run_codewiki_cli(self, analysis: CodeWikiAnalysis) -> Path:
        """
        Run CodeWiki CLI command.

        Returns path to output directory.
        """
        repo_path = Path(analysis.repository_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        # Create output directory
        output_dir = repo_path / "docs" / "codewiki"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if CodeWiki is installed
        try:
            result = subprocess.run(
                ["codewiki", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("CodeWiki not installed, using fallback analysis")
                return await self._fallback_analysis(analysis, output_dir)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("CodeWiki not available, using fallback analysis")
            return await self._fallback_analysis(analysis, output_dir)

        # Run CodeWiki generate
        cmd = [
            "codewiki", "generate",
            "--output", str(output_dir),
            str(repo_path)
        ]

        logger.info(f"Running CodeWiki: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(repo_path)
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.warning(f"CodeWiki CLI failed: {error_msg}, using fallback")
            return await self._fallback_analysis(analysis, output_dir)

        return output_dir

    async def _fallback_analysis(
        self,
        analysis: CodeWikiAnalysis,
        output_dir: Path
    ) -> Path:
        """
        Fallback analysis when CodeWiki CLI is not available.

        Performs basic code scanning and generates similar outputs.
        """
        repo_path = Path(analysis.repository_path)

        # Scan repository structure
        modules = self._scan_repository_structure(repo_path)

        # Generate module tree
        module_tree = {
            "name": repo_path.name,
            "type": "repository",
            "children": modules,
            "metadata": {
                "generated_by": "marqed_fallback",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        # Save module_tree.json
        module_tree_path = output_dir / "module_tree.json"
        with open(module_tree_path, "w") as f:
            json.dump(module_tree, f, indent=2)

        # Generate overview
        overview = self._generate_overview(repo_path, modules)
        overview_path = output_dir / "overview.md"
        with open(overview_path, "w") as f:
            f.write(overview)

        # Generate architecture diagram
        diagram = self._generate_architecture_diagram(modules)
        diagram_path = output_dir / "architecture.md"
        with open(diagram_path, "w") as f:
            f.write(f"# Architecture\n\n```mermaid\n{diagram}\n```\n")

        return output_dir

    def _scan_repository_structure(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Scan repository and build module structure."""
        modules = []

        # Find main directories
        for item in repo_path.iterdir():
            if item.is_dir() and not item.name.startswith(('.', '_', 'node_modules', 'venv', '__pycache__')):
                module = self._scan_directory(item, level=0)
                if module:
                    modules.append(module)

        return modules

    def _scan_directory(self, path: Path, level: int = 0) -> Optional[Dict[str, Any]]:
        """Scan a directory and build module info."""
        if level > 4:  # Max depth
            return None

        files = []
        children = []
        functions = 0
        classes = 0
        lines = 0

        for item in path.iterdir():
            if item.name.startswith(('.', '_', '__pycache__')):
                continue

            if item.is_file():
                ext = item.suffix.lower()
                if any(ext in exts for exts in self.LANGUAGE_EXTENSIONS.values()):
                    files.append(str(item.relative_to(path.parent.parent)))
                    # Count lines and basic stats
                    try:
                        content = item.read_text(errors='ignore')
                        lines += len(content.splitlines())
                        # Simple pattern matching for functions/classes
                        functions += len(re.findall(r'\bdef\s+\w+|function\s+\w+|\bfn\s+\w+', content))
                        classes += len(re.findall(r'\bclass\s+\w+|interface\s+\w+|struct\s+\w+', content))
                    except Exception:
                        pass

            elif item.is_dir():
                child = self._scan_directory(item, level + 1)
                if child:
                    children.append(child)

        if not files and not children:
            return None

        return {
            "name": path.name,
            "path": str(path.relative_to(path.parent.parent)),
            "type": "module",
            "level": level,
            "files": files,
            "file_count": len(files),
            "function_count": functions,
            "class_count": classes,
            "line_count": lines,
            "children": children,
        }

    def _generate_overview(self, repo_path: Path, modules: List[Dict]) -> str:
        """Generate overview markdown."""
        total_files = sum(m.get("file_count", 0) for m in modules)
        total_functions = sum(m.get("function_count", 0) for m in modules)
        total_classes = sum(m.get("class_count", 0) for m in modules)

        overview = f"""# {repo_path.name} - Repository Overview

## Statistics

| Metric | Value |
|--------|-------|
| Total Modules | {len(modules)} |
| Total Files | {total_files} |
| Total Functions | {total_functions} |
| Total Classes | {total_classes} |

## Modules

"""
        for module in modules:
            overview += f"### {module['name']}\n\n"
            overview += f"- Files: {module.get('file_count', 0)}\n"
            overview += f"- Functions: {module.get('function_count', 0)}\n"
            overview += f"- Classes: {module.get('class_count', 0)}\n\n"

        return overview

    def _generate_architecture_diagram(self, modules: List[Dict]) -> str:
        """Generate Mermaid architecture diagram."""
        lines = ["graph TD"]

        for i, module in enumerate(modules):
            node_id = f"M{i}"
            label = module["name"]
            lines.append(f"    {node_id}[{label}]")

            # Add children
            for j, child in enumerate(module.get("children", [])[:5]):  # Limit children
                child_id = f"{node_id}_{j}"
                lines.append(f"    {child_id}[{child['name']}]")
                lines.append(f"    {node_id} --> {child_id}")

        return "\n".join(lines)

    async def _parse_codewiki_outputs(
        self,
        analysis: CodeWikiAnalysis,
        output_dir: Path
    ) -> None:
        """Parse CodeWiki output files and store in database."""
        # Parse module_tree.json
        module_tree_path = output_dir / "module_tree.json"
        if module_tree_path.exists():
            with open(module_tree_path) as f:
                module_tree = json.load(f)
            analysis.module_tree_json = module_tree
            await self._store_modules(analysis, module_tree)

        # Parse overview.md
        overview_path = output_dir / "overview.md"
        if overview_path.exists():
            analysis.overview_md = overview_path.read_text()

        # Parse metadata.json
        metadata_path = output_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                analysis.metadata_json = json.load(f)

        # Extract diagrams from all markdown files
        for md_file in output_dir.glob("*.md"):
            content = md_file.read_text()
            await self._extract_diagrams(analysis, md_file.stem, content)

        # Update statistics
        modules = self.db.query(CodeWikiModule).filter(
            CodeWikiModule.analysis_id == analysis.id
        ).all()

        analysis.total_modules = len(modules)
        analysis.total_files = sum(m.file_count or 0 for m in modules)
        analysis.total_functions = sum(m.function_count or 0 for m in modules)
        analysis.total_classes = sum(m.class_count or 0 for m in modules)

        self.db.commit()

    async def _store_modules(
        self,
        analysis: CodeWikiAnalysis,
        module_tree: Dict[str, Any],
        parent_id: Optional[int] = None,
        level: int = 0
    ) -> None:
        """Recursively store modules from module tree."""
        # Create module record
        module = CodeWikiModule(
            analysis_id=analysis.id,
            name=module_tree.get("name", "unknown"),
            path=module_tree.get("path"),
            parent_module_id=parent_id,
            level=level,
            description=module_tree.get("description"),
            purpose=module_tree.get("purpose"),
            files=module_tree.get("files", []),
            file_count=module_tree.get("file_count", 0),
            function_count=module_tree.get("function_count", 0),
            class_count=module_tree.get("class_count", 0),
            line_count=module_tree.get("line_count", 0),
            dependencies=module_tree.get("dependencies", []),
            external_dependencies=module_tree.get("external_dependencies", []),
        )
        self.db.add(module)
        self.db.flush()  # Get ID

        # Process children
        for child in module_tree.get("children", []):
            await self._store_modules(analysis, child, module.id, level + 1)

    async def _extract_diagrams(
        self,
        analysis: CodeWikiAnalysis,
        source_name: str,
        content: str
    ) -> None:
        """Extract Mermaid diagrams from markdown content."""
        matches = self.MERMAID_PATTERN.findall(content)

        for i, mermaid_code in enumerate(matches):
            # Detect diagram type
            diagram_type = self._detect_diagram_type(mermaid_code)

            diagram = CodeWikiDiagram(
                analysis_id=analysis.id,
                name=f"{source_name}_diagram_{i+1}",
                diagram_type=diagram_type,
                mermaid_code=mermaid_code.strip(),
            )
            self.db.add(diagram)

        self.db.commit()

    def _detect_diagram_type(self, mermaid_code: str) -> DiagramType:
        """Detect type of Mermaid diagram from code."""
        code_lower = mermaid_code.lower()

        if code_lower.startswith("sequencediagram"):
            return DiagramType.SEQUENCE
        elif code_lower.startswith("classdiagram"):
            return DiagramType.CLASS
        elif code_lower.startswith("erdiagram"):
            return DiagramType.ERD
        elif "flowchart" in code_lower or "graph" in code_lower:
            if "data" in code_lower:
                return DiagramType.DATA_FLOW
            return DiagramType.ARCHITECTURE
        elif "component" in code_lower:
            return DiagramType.COMPONENT

        return DiagramType.ARCHITECTURE

    async def _prepare_agent_contexts(self, analysis: CodeWikiAnalysis) -> None:
        """Prepare optimized contexts for each agent type."""
        # Get modules
        modules = self.db.query(CodeWikiModule).filter(
            CodeWikiModule.analysis_id == analysis.id
        ).all()

        # Get diagrams
        diagrams = self.db.query(CodeWikiDiagram).filter(
            CodeWikiDiagram.analysis_id == analysis.id
        ).all()

        # Felix (Feature Architect) - Architecture focus
        await self._create_agent_context(
            analysis,
            agent_name="felix",
            context_type="architecture",
            summary=self._generate_felix_summary(analysis, modules, diagrams),
            details={
                "module_count": len(modules),
                "top_level_modules": [m.to_dict() for m in modules if m.level == 0],
                "architecture_diagrams": [
                    d.to_dict() for d in diagrams
                    if d.diagram_type == DiagramType.ARCHITECTURE
                ],
            }
        )

        # Miguel (Migration Architect) - Dependencies focus
        await self._create_agent_context(
            analysis,
            agent_name="miguel",
            context_type="dependencies",
            summary=self._generate_miguel_summary(modules),
            details={
                "internal_dependencies": self._collect_dependencies(modules, "dependencies"),
                "external_dependencies": self._collect_dependencies(modules, "external_dependencies"),
                "module_hierarchy": self._build_hierarchy_map(modules),
            }
        )

        # Quinn (Quality Inspector) - Complexity focus
        await self._create_agent_context(
            analysis,
            agent_name="quinn",
            context_type="complexity",
            summary=self._generate_quinn_summary(modules),
            details={
                "modules_by_complexity": self._rank_modules_by_complexity(modules),
                "large_modules": [m.to_dict() for m in modules if (m.file_count or 0) > 10],
                "dependency_hotspots": self._find_dependency_hotspots(modules),
            }
        )

        # Diana (Documentation Writer) - Documentation focus
        await self._create_agent_context(
            analysis,
            agent_name="diana",
            context_type="documentation",
            summary=self._generate_diana_summary(analysis, modules),
            details={
                "overview": analysis.overview_md,
                "module_descriptions": {m.name: m.description for m in modules if m.description},
                "undocumented_modules": [m.name for m in modules if not m.description],
            }
        )

        self.db.commit()

    async def _create_agent_context(
        self,
        analysis: CodeWikiAnalysis,
        agent_name: str,
        context_type: str,
        summary: str,
        details: Dict[str, Any]
    ) -> CodeWikiAgentContext:
        """Create agent context record."""
        context = CodeWikiAgentContext(
            analysis_id=analysis.id,
            agent_name=agent_name,
            context_type=context_type,
            context_summary=summary,
            context_details=details,
        )
        self.db.add(context)
        return context

    def _generate_felix_summary(
        self,
        analysis: CodeWikiAnalysis,
        modules: List[CodeWikiModule],
        diagrams: List[CodeWikiDiagram]
    ) -> str:
        """Generate architecture summary for Felix."""
        top_modules = [m for m in modules if m.level == 0]
        return f"""Repository Architecture Summary:
- {len(top_modules)} main components/modules
- {analysis.total_files or 0} total files
- {analysis.total_functions or 0} functions, {analysis.total_classes or 0} classes
- {len(diagrams)} architecture diagrams available
- Languages: {', '.join(analysis.languages_detected or ['unknown'])}

Main components: {', '.join(m.name for m in top_modules[:5])}"""

    def _generate_miguel_summary(self, modules: List[CodeWikiModule]) -> str:
        """Generate dependency summary for Miguel."""
        all_deps = set()
        all_ext_deps = set()
        for m in modules:
            all_deps.update(m.dependencies or [])
            all_ext_deps.update(m.external_dependencies or [])

        return f"""Dependency Analysis:
- {len(all_deps)} internal dependencies identified
- {len(all_ext_deps)} external packages used
- Module count: {len(modules)}

Top external dependencies: {', '.join(list(all_ext_deps)[:10])}"""

    def _generate_quinn_summary(self, modules: List[CodeWikiModule]) -> str:
        """Generate complexity summary for Quinn."""
        total_lines = sum(m.line_count or 0 for m in modules)
        large_modules = [m for m in modules if (m.file_count or 0) > 10]

        return f"""Code Complexity Overview:
- {total_lines} total lines of code
- {len(large_modules)} large modules (>10 files)
- Average module size: {total_lines // len(modules) if modules else 0} lines

Focus areas for review: {', '.join(m.name for m in large_modules[:5])}"""

    def _generate_diana_summary(
        self,
        analysis: CodeWikiAnalysis,
        modules: List[CodeWikiModule]
    ) -> str:
        """Generate documentation summary for Diana."""
        documented = len([m for m in modules if m.description])

        return f"""Documentation Status:
- {documented}/{len(modules)} modules have descriptions
- Overview available: {'Yes' if analysis.overview_md else 'No'}
- Languages: {', '.join(analysis.languages_detected or ['unknown'])}

Modules needing documentation: {', '.join(m.name for m in modules if not m.description)[:5]}"""

    def _collect_dependencies(
        self,
        modules: List[CodeWikiModule],
        dep_type: str
    ) -> Dict[str, List[str]]:
        """Collect dependencies by module."""
        return {
            m.name: getattr(m, dep_type) or []
            for m in modules
            if getattr(m, dep_type)
        }

    def _build_hierarchy_map(self, modules: List[CodeWikiModule]) -> Dict[str, Any]:
        """Build module hierarchy map."""
        hierarchy = {}
        for m in modules:
            if m.level == 0:
                hierarchy[m.name] = {
                    "children": [c.name for c in modules if c.parent_module_id == m.id],
                    "files": m.file_count or 0,
                }
        return hierarchy

    def _rank_modules_by_complexity(
        self,
        modules: List[CodeWikiModule]
    ) -> List[Dict[str, Any]]:
        """Rank modules by complexity score."""
        scored = []
        for m in modules:
            score = (
                (m.file_count or 0) * 10 +
                (m.function_count or 0) * 2 +
                (m.class_count or 0) * 5 +
                len(m.dependencies or []) * 3
            )
            scored.append({
                "name": m.name,
                "complexity_score": score,
                "file_count": m.file_count,
                "function_count": m.function_count,
            })

        return sorted(scored, key=lambda x: x["complexity_score"], reverse=True)[:10]

    def _find_dependency_hotspots(
        self,
        modules: List[CodeWikiModule]
    ) -> List[Dict[str, Any]]:
        """Find modules with many dependencies."""
        hotspots = []
        for m in modules:
            dep_count = len(m.dependencies or []) + len(m.external_dependencies or [])
            if dep_count > 5:
                hotspots.append({
                    "name": m.name,
                    "total_dependencies": dep_count,
                    "internal": len(m.dependencies or []),
                    "external": len(m.external_dependencies or []),
                })

        return sorted(hotspots, key=lambda x: x["total_dependencies"], reverse=True)[:5]

    def _detect_languages(self, repo_path: str) -> List[str]:
        """Detect programming languages in repository."""
        path = Path(repo_path)
        if not path.exists():
            return []

        detected = set()
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            for ext in extensions:
                if list(path.rglob(f"*{ext}"))[:1]:  # Check if any file exists
                    detected.add(lang)
                    break

        return list(detected)

    # ============ Query Methods ============

    def get_modules(
        self,
        analysis_id: int,
        level: Optional[int] = None
    ) -> List[CodeWikiModule]:
        """Get modules for analysis."""
        query = self.db.query(CodeWikiModule).filter(
            CodeWikiModule.analysis_id == analysis_id
        )
        if level is not None:
            query = query.filter(CodeWikiModule.level == level)
        return query.all()

    def get_diagrams(
        self,
        analysis_id: int,
        diagram_type: Optional[DiagramType] = None
    ) -> List[CodeWikiDiagram]:
        """Get diagrams for analysis."""
        query = self.db.query(CodeWikiDiagram).filter(
            CodeWikiDiagram.analysis_id == analysis_id
        )
        if diagram_type:
            query = query.filter(CodeWikiDiagram.diagram_type == diagram_type)
        return query.all()

    def get_agent_context(
        self,
        analysis_id: int,
        agent_name: str,
        context_type: Optional[str] = None
    ) -> Optional[CodeWikiAgentContext]:
        """Get agent context for analysis."""
        query = self.db.query(CodeWikiAgentContext).filter(
            and_(
                CodeWikiAgentContext.analysis_id == analysis_id,
                CodeWikiAgentContext.agent_name == agent_name
            )
        )
        if context_type:
            query = query.filter(CodeWikiAgentContext.context_type == context_type)

        context = query.first()
        if context:
            # Update usage stats
            context.times_used = (context.times_used or 0) + 1
            context.last_used_at = datetime.now(timezone.utc)
            self.db.commit()

        return context

    def get_module_tree_json(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get raw module tree JSON."""
        analysis = self.get_analysis(analysis_id)
        return analysis.module_tree_json if analysis else None

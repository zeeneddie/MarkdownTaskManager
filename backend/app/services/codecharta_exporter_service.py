"""
CodeCharta Exporter Service

Week 145 - Fase 28: CodeCharta Integration

Exports code analysis metrics to CodeCharta's JSON format for 3D visualization.
CodeCharta visualizes software metrics as a city: files as buildings, folders as districts.

Format specification: https://maibornwolff.github.io/codecharta/

Output format: .cc.json
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeChartaAttribute:
    """A metric attribute for CodeCharta nodes."""
    name: str
    value: float


@dataclass
class CodeChartaNode:
    """A node in the CodeCharta tree (file or folder)."""
    name: str
    type: str  # "File" or "Folder"
    attributes: Dict[str, float] = field(default_factory=dict)
    children: List['CodeChartaNode'] = field(default_factory=list)
    link: Optional[str] = None  # Optional link to source
    path: Optional[str] = None  # Full path for reference

    def to_dict(self) -> Dict[str, Any]:
        """Convert to CodeCharta JSON format."""
        result = {
            "name": self.name,
            "type": self.type,
            "attributes": self.attributes,
        }
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        if self.link:
            result["link"] = self.link
        return result


@dataclass
class CodeChartaProject:
    """A CodeCharta project with metadata and root node."""
    projectName: str
    apiVersion: str = "1.3"
    nodes: List[CodeChartaNode] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)  # Dependencies
    attributeTypes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    attributeDescriptors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    blacklist: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to CodeCharta JSON format."""
        return {
            "projectName": self.projectName,
            "apiVersion": self.apiVersion,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": self.edges,
            "attributeTypes": self.attributeTypes,
            "attributeDescriptors": self.attributeDescriptors,
            "blacklist": self.blacklist,
        }


# Standard metrics supported by CodeCharta
STANDARD_METRICS = {
    "loc": {"title": "Lines of Code", "description": "Total lines of code", "direction": -1},
    "rloc": {"title": "Real Lines of Code", "description": "Non-empty, non-comment lines", "direction": -1},
    "complexity": {"title": "Cyclomatic Complexity", "description": "McCabe cyclomatic complexity", "direction": -1},
    "functions": {"title": "Functions", "description": "Number of functions/methods", "direction": -1},
    "classes": {"title": "Classes", "description": "Number of classes", "direction": -1},
    "coupling": {"title": "Coupling", "description": "Afferent + efferent coupling", "direction": -1},
    "cohesion": {"title": "Cohesion", "description": "LCOM (Lack of Cohesion)", "direction": -1},
    "coverage": {"title": "Test Coverage", "description": "Percentage of code covered by tests", "direction": 1},
    "debt_hours": {"title": "Technical Debt (hours)", "description": "Estimated hours to fix debt", "direction": -1},
    "age_days": {"title": "File Age (days)", "description": "Days since last modification", "direction": -1},
    "commits": {"title": "Commits", "description": "Number of commits touching this file", "direction": 0},
    "authors": {"title": "Authors", "description": "Number of unique authors", "direction": 0},
    "churn": {"title": "Code Churn", "description": "Lines added + deleted recently", "direction": -1},
    "duplicates": {"title": "Duplicate Lines", "description": "Lines of duplicated code", "direction": -1},
    "issues": {"title": "Issues", "description": "Number of code issues/warnings", "direction": -1},
    "security_issues": {"title": "Security Issues", "description": "Security vulnerabilities", "direction": -1},
}


class CodeChartaExporterService:
    """
    Service for exporting code analysis data to CodeCharta format.

    Supports multiple input sources:
    - DependencyGraphService analysis
    - CodeAnalysisAggregatorService metrics
    - Static analysis results
    - Git metrics
    """

    def __init__(self):
        self.attribute_descriptors = {
            k: {"title": v["title"], "description": v["description"], "direction": v["direction"]}
            for k, v in STANDARD_METRICS.items()
        }
        self.attribute_types = {
            "nodes": {k: "absolute" for k in STANDARD_METRICS.keys()},
            "edges": {"coupling": "absolute", "calls": "absolute"},
        }

    def create_project(
        self,
        project_name: str,
        root_path: str,
        analysis_data: Dict[str, Any],
        include_edges: bool = True,
    ) -> CodeChartaProject:
        """
        Create a CodeCharta project from analysis data.

        Args:
            project_name: Name of the project
            root_path: Root path of the analyzed codebase
            analysis_data: Analysis results with file metrics
            include_edges: Whether to include dependency edges

        Returns:
            CodeChartaProject ready for JSON export
        """
        project = CodeChartaProject(
            projectName=project_name,
            attributeTypes=self.attribute_types,
            attributeDescriptors=self.attribute_descriptors,
        )

        # Create root node
        root_node = CodeChartaNode(
            name=project_name,
            type="Folder",
            path=root_path,
        )

        # Process files from analysis data
        files_data = analysis_data.get("files", [])
        self._build_tree(root_node, files_data, root_path)

        project.nodes = [root_node]

        # Add dependency edges if requested
        if include_edges:
            dependencies = analysis_data.get("dependencies", [])
            project.edges = self._create_edges(dependencies)

        return project

    def _build_tree(
        self,
        root: CodeChartaNode,
        files: List[Dict[str, Any]],
        root_path: str,
    ) -> None:
        """Build the folder/file tree from flat file list."""
        folder_map: Dict[str, CodeChartaNode] = {"": root}

        for file_data in files:
            file_path = file_data.get("path", "")
            relative_path = self._get_relative_path(file_path, root_path)

            if not relative_path:
                continue

            # Create folder structure
            parts = relative_path.split("/")
            current_path = ""

            for i, part in enumerate(parts[:-1]):  # All but the filename
                parent_path = current_path
                current_path = f"{current_path}/{part}" if current_path else part

                if current_path not in folder_map:
                    folder_node = CodeChartaNode(
                        name=part,
                        type="Folder",
                        path=current_path,
                    )
                    parent_node = folder_map.get(parent_path, root)
                    parent_node.children.append(folder_node)
                    folder_map[current_path] = folder_node

            # Create file node
            filename = parts[-1]
            parent_path = "/".join(parts[:-1])
            parent_node = folder_map.get(parent_path, root)

            file_node = CodeChartaNode(
                name=filename,
                type="File",
                path=relative_path,
                attributes=self._extract_metrics(file_data),
            )
            parent_node.children.append(file_node)

    def _get_relative_path(self, file_path: str, root_path: str) -> str:
        """Get relative path from root."""
        try:
            return str(Path(file_path).relative_to(Path(root_path)))
        except ValueError:
            # File is not under root path
            return file_path.replace(root_path, "").lstrip("/\\")

    def _extract_metrics(self, file_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract metrics from file data to CodeCharta attributes."""
        metrics = {}

        # Map common metric names
        metric_mapping = {
            "loc": ["loc", "lines_of_code", "total_lines"],
            "rloc": ["rloc", "real_loc", "source_lines"],
            "complexity": ["complexity", "cyclomatic_complexity", "mccabe"],
            "functions": ["functions", "function_count", "methods"],
            "classes": ["classes", "class_count"],
            "coupling": ["coupling", "afferent_coupling", "efferent_coupling"],
            "cohesion": ["cohesion", "lcom", "lack_of_cohesion"],
            "coverage": ["coverage", "test_coverage", "line_coverage"],
            "debt_hours": ["debt_hours", "technical_debt_hours", "sqale_debt"],
            "issues": ["issues", "issue_count", "warnings"],
            "security_issues": ["security_issues", "vulnerabilities", "security_warnings"],
            "duplicates": ["duplicates", "duplicate_lines", "duplicated_blocks"],
            "commits": ["commits", "commit_count"],
            "authors": ["authors", "author_count", "contributors"],
            "churn": ["churn", "code_churn", "lines_changed"],
        }

        for target_metric, source_names in metric_mapping.items():
            for source_name in source_names:
                if source_name in file_data:
                    value = file_data[source_name]
                    if isinstance(value, (int, float)):
                        metrics[target_metric] = float(value)
                        break

        # Handle nested metrics
        if "metrics" in file_data:
            nested = file_data["metrics"]
            for target_metric, source_names in metric_mapping.items():
                if target_metric not in metrics:
                    for source_name in source_names:
                        if source_name in nested:
                            value = nested[source_name]
                            if isinstance(value, (int, float)):
                                metrics[target_metric] = float(value)
                                break

        return metrics

    def _create_edges(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create edge list from dependency data."""
        edges = []

        for dep in dependencies:
            from_path = dep.get("from", dep.get("source", ""))
            to_path = dep.get("to", dep.get("target", ""))

            if from_path and to_path:
                edge = {
                    "fromNodeName": from_path,
                    "toNodeName": to_path,
                    "attributes": {
                        "coupling": dep.get("weight", dep.get("coupling", 1)),
                        "calls": dep.get("calls", dep.get("references", 1)),
                    }
                }
                edges.append(edge)

        return edges

    def export_to_json(
        self,
        project: CodeChartaProject,
        output_path: Optional[str] = None,
        indent: int = 2,
    ) -> str:
        """
        Export project to JSON string or file.

        Args:
            project: CodeChartaProject to export
            output_path: Optional file path (should end with .cc.json)
            indent: JSON indentation level

        Returns:
            JSON string
        """
        json_data = project.to_dict()
        json_str = json.dumps(json_data, indent=indent, ensure_ascii=False)

        if output_path:
            # Ensure .cc.json extension
            if not output_path.endswith(".cc.json"):
                output_path = output_path.rsplit(".", 1)[0] + ".cc.json"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"CodeCharta export saved to: {output_path}")

        return json_str

    def from_code_analysis_aggregator(
        self,
        project_name: str,
        root_path: str,
        aggregator_result: Dict[str, Any],
    ) -> CodeChartaProject:
        """
        Create CodeCharta project from CodeAnalysisAggregatorService output.

        Args:
            project_name: Name of the project
            root_path: Root path of the codebase
            aggregator_result: Output from CodeAnalysisAggregatorService

        Returns:
            CodeChartaProject
        """
        # Transform aggregator format to our standard format
        files = []

        for file_analysis in aggregator_result.get("file_analyses", []):
            file_data = {
                "path": file_analysis.get("file_path", ""),
                "loc": file_analysis.get("loc", 0),
                "complexity": file_analysis.get("complexity", 0),
                "functions": file_analysis.get("function_count", 0),
                "classes": file_analysis.get("class_count", 0),
                "coupling": file_analysis.get("coupling", 0),
                "issues": file_analysis.get("issue_count", 0),
            }
            files.append(file_data)

        analysis_data = {
            "files": files,
            "dependencies": aggregator_result.get("dependencies", []),
        }

        return self.create_project(project_name, root_path, analysis_data)

    def from_dependency_graph(
        self,
        project_name: str,
        root_path: str,
        graph_data: Dict[str, Any],
    ) -> CodeChartaProject:
        """
        Create CodeCharta project from DependencyGraphService output.

        Args:
            project_name: Name of the project
            root_path: Root path of the codebase
            graph_data: Output from DependencyGraphService

        Returns:
            CodeChartaProject
        """
        # Transform graph format to our standard format
        files = []
        nodes = graph_data.get("nodes", [])

        for node in nodes:
            file_data = {
                "path": node.get("path", node.get("id", "")),
                "loc": node.get("loc", 0),
                "complexity": node.get("complexity", 0),
                "coupling": node.get("afferent_coupling", 0) + node.get("efferent_coupling", 0),
            }
            files.append(file_data)

        analysis_data = {
            "files": files,
            "dependencies": graph_data.get("edges", []),
        }

        return self.create_project(project_name, root_path, analysis_data)

    def from_static_analysis(
        self,
        project_name: str,
        root_path: str,
        static_analysis_result: Dict[str, Any],
    ) -> CodeChartaProject:
        """
        Create CodeCharta project from static analysis results.

        Args:
            project_name: Name of the project
            root_path: Root path of the codebase
            static_analysis_result: Output from static analysis tools

        Returns:
            CodeChartaProject
        """
        files = []

        # Handle various static analysis formats
        for file_result in static_analysis_result.get("results", []):
            file_data = {
                "path": file_result.get("file", file_result.get("path", "")),
                "loc": file_result.get("loc", 0),
                "issues": len(file_result.get("issues", [])),
                "security_issues": len([
                    i for i in file_result.get("issues", [])
                    if i.get("type") == "security" or i.get("category") == "security"
                ]),
                "complexity": file_result.get("complexity", 0),
            }
            files.append(file_data)

        analysis_data = {"files": files, "dependencies": []}

        return self.create_project(project_name, root_path, analysis_data, include_edges=False)


# Singleton instance
_codecharta_exporter: Optional[CodeChartaExporterService] = None


def get_codecharta_exporter() -> CodeChartaExporterService:
    """Get singleton CodeCharta exporter instance."""
    global _codecharta_exporter
    if _codecharta_exporter is None:
        _codecharta_exporter = CodeChartaExporterService()
    return _codecharta_exporter

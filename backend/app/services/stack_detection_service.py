"""
Stack Detection Service

Week 65 Day 3: Comprehensive stack detection for legacy code analysis.
Detects 20+ technology stacks including .NET, Angular, Vue, React, PHP, Java, Python.

Features:
- File extension analysis with confidence scoring
- Framework configuration file detection
- Pattern matching in source files
- Lizard complexity analysis integration
- Database detection from connection strings and configs

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import re
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FileStats:
    """Statistics for a single file"""
    path: str
    extension: str
    lines: int = 0
    size_bytes: int = 0
    stack_hints: List[str] = field(default_factory=list)


@dataclass
class StackDetection:
    """Detection result for a technology stack"""
    stack_name: str
    confidence: float = 0.0  # 0.0 - 1.0
    file_count: int = 0
    total_loc: int = 0
    config_files: List[str] = field(default_factory=list)
    pattern_matches: int = 0
    evidence: List[str] = field(default_factory=list)


@dataclass
class ComplexityMetrics:
    """Complexity metrics from Lizard analysis"""
    avg_cyclomatic: float = 0.0
    max_cyclomatic: float = 0.0
    avg_cognitive: float = 0.0
    total_functions: int = 0
    high_complexity_count: int = 0  # Functions with CC > 10
    nloc: int = 0


@dataclass
class ScanResult:
    """Complete scan result for a repository"""
    repo_path: str
    total_files: int = 0
    total_loc: int = 0
    primary_stack: Optional[str] = None
    secondary_stacks: List[str] = field(default_factory=list)
    stack_detections: Dict[str, StackDetection] = field(default_factory=dict)
    database_type: Optional[str] = None
    database_evidence: List[str] = field(default_factory=list)
    complexity: Optional[ComplexityMetrics] = None
    file_inventory: Dict[str, int] = field(default_factory=dict)  # extension -> count
    errors: List[str] = field(default_factory=list)
    detection_time_ms: int = 0  # Time taken for detection in milliseconds

    @property
    def primary_stacks(self) -> List[str]:
        """Get primary stacks as a list (primary + secondary)."""
        stacks = []
        if self.primary_stack:
            stacks.append(self.primary_stack)
        stacks.extend(self.secondary_stacks)
        return stacks

    @property
    def project_type(self) -> str:
        """Infer project type from stacks."""
        if self.primary_stack:
            web_stacks = {"aspnet_webforms", "aspnet_mvc", "aspnet_core", "react", "vue", "angular", "php"}
            if self.primary_stack in web_stacks:
                return "web_application"
        return "unknown"

    @property
    def frameworks(self) -> Dict[str, List[str]]:
        """Get detected frameworks grouped by stack category."""
        result: Dict[str, List[str]] = {}
        for name, det in self.stack_detections.items():
            if det.confidence >= 0.5:
                # Group by primary stack or use 'general'
                category = self.primary_stack or "general"
                if category not in result:
                    result[category] = []
                result[category].append(name)
        return result

    # =========================================================================
    # New terminology: 1 tech_stack with multiple technologies
    # =========================================================================

    @property
    def tech_stack(self) -> Optional[str]:
        """
        The primary technology stack for this project.

        This represents the main/dominant technology (e.g., 'aspnet_webforms',
        'vue2', 'react'). A project has ONE tech_stack with multiple technologies.

        Alias for primary_stack (backward compatible).
        """
        return self.primary_stack

    @property
    def technologies(self) -> List[str]:
        """
        All detected technologies in this project with confidence >= 0.5.

        Includes the tech_stack plus all supporting technologies like:
        - Frontend frameworks (vue2, jquery, typescript)
        - Backend technologies (wcf, aspnet_mvc)
        - Database connectors
        - Build tools

        Returns technologies sorted by confidence (highest first).
        """
        return [
            name for name, det in sorted(
                self.stack_detections.items(),
                key=lambda x: x[1].confidence,
                reverse=True
            )
            if det.confidence >= 0.5
        ]

    @property
    def technology_summary(self) -> Dict[str, any]:
        """
        Summary of the project's technology profile.

        Returns a dict with:
        - tech_stack: The primary technology
        - technologies: List of all detected technologies
        - database: Detected database type
        - total_technologies: Count of technologies
        """
        return {
            "tech_stack": self.tech_stack,
            "technologies": self.technologies,
            "database": self.database_type,
            "total_technologies": len(self.technologies),
        }


# Stack definitions with detection patterns
STACK_DEFINITIONS = {
    # .NET Legacy
    "aspnet_webforms": {
        "extensions": [".aspx", ".aspx.cs", ".aspx.vb", ".ascx", ".master"],
        "config_files": ["Web.config"],
        "patterns": [
            r"<%@\s*Page",
            r'runat="server"',
            r"<asp:",
            r"ViewState",
            r"PostBack",
            r"CodeBehind=",
            r"AutoEventWireup",
        ],
        "weight": 1.5,
    },
    "asp_classic": {
        "extensions": [".asp"],
        "config_files": [],
        "patterns": [
            r"<%\s*=",
            r"Response\.Write",
            r"Request\.Form",
            r"Server\.CreateObject",
            r"ADODB\.",
        ],
        "weight": 1.3,
    },
    "aspnet_mvc": {
        "extensions": [".cshtml", ".vbhtml"],
        "config_files": ["Web.config", "RouteConfig.cs"],
        "patterns": [
            r"@Html\.",
            r"@Model",
            r"@ViewBag",
            r"ActionResult",
            r"\[HttpGet\]",
            r"\[HttpPost\]",
        ],
        "weight": 1.2,
    },
    "wcf": {
        "extensions": [".svc"],
        "config_files": ["Web.config"],
        "patterns": [
            r"ServiceContract",
            r"OperationContract",
            r"DataContract",
            r"<endpoint\s+",
            r"basicHttpBinding",
        ],
        "weight": 1.4,
    },
    "dotnet_core": {
        "extensions": [".cs", ".razor"],
        "config_files": ["appsettings.json", "Program.cs", "Startup.cs", "*.csproj"],
        "patterns": [
            r"IServiceCollection",
            r"AddControllers",
            r"UseRouting",
            r"MapControllers",
            r"<TargetFramework>net[5-8]",
        ],
        "weight": 1.0,
    },

    # JavaScript/TypeScript Frontend
    "angularjs": {
        "extensions": [".js"],
        "config_files": [],
        "patterns": [
            r"angular\.module",
            r"\.controller\(",
            r"\.directive\(",
            r"\.factory\(",
            r"\.service\(",
            r"\$scope",
            r"\$http",
            r"ng-app",
            r"ng-controller",
        ],
        "weight": 1.3,
    },
    "angular": {
        "extensions": [".ts", ".component.ts", ".service.ts", ".module.ts"],
        "config_files": ["angular.json"],  # tsconfig.json removed - not Angular-specific
        "patterns": [
            r"@Component\(",
            r"@Injectable\(",
            r"@NgModule\(",
            r"import.*@angular/core",
            r"from\s+['\"]@angular/",
        ],
        "weight": 1.2,
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "config_files": ["tsconfig.json"],
        "patterns": [
            r"interface\s+\w+",
            r"type\s+\w+\s*=",
            r":\s*(string|number|boolean|any|void|never)",
            r"export\s+interface",
            r"as\s+const",
        ],
        "weight": 0.8,  # Lower weight - TypeScript is support tech, not primary stack
    },
    "vue2": {
        "extensions": [".vue"],
        "config_files": ["vue.config.js"],
        "patterns": [
            r"new Vue\(",
            r"Vue\.component",
            r"Vue\.extend",
            r"export default\s*{[^}]*data\s*\(\)",
            r"this\.\$emit",
        ],
        "weight": 1.2,
    },
    "vue3": {
        "extensions": [".vue"],
        "config_files": ["vite.config.js", "vite.config.ts"],
        "patterns": [
            r"createApp\(",
            r"defineComponent\(",
            r"<script setup>",
            r"ref\(",
            r"reactive\(",
            r"computed\(",
        ],
        "weight": 1.2,
    },
    "react_class": {
        "extensions": [".jsx", ".tsx"],
        "config_files": ["package.json"],
        "patterns": [
            r"extends\s+React\.Component",
            r"extends\s+Component",
            r"this\.state",
            r"this\.setState",
            r"componentDidMount",
            r"componentWillUnmount",
        ],
        "weight": 1.1,
    },
    "react_hooks": {
        "extensions": [".jsx", ".tsx"],
        "config_files": ["package.json"],
        "patterns": [
            r"useState\(",
            r"useEffect\(",
            r"useContext\(",
            r"useReducer\(",
            r"useMemo\(",
            r"useCallback\(",
        ],
        "weight": 1.0,
    },
    "jquery": {
        "extensions": [".js"],
        "config_files": [],
        "patterns": [
            r"\$\(",
            r"jQuery\(",
            r"\.click\(",
            r"\.ajax\(",
            r"\.ready\(",
            r"\$\.get\(",
            r"\$\.post\(",
        ],
        "weight": 0.8,
    },

    # PHP
    "php_legacy": {
        "extensions": [".php"],
        "config_files": [],
        "patterns": [
            r"mysql_connect",
            r"mysql_query",
            r"\$_GET\[",
            r"\$_POST\[",
            r"include\s*['\"]",
            r"require\s*['\"]",
        ],
        "weight": 1.2,
    },
    "laravel": {
        "extensions": [".php", ".blade.php"],
        "config_files": ["artisan", "composer.json"],
        "patterns": [
            r"Illuminate\\\\",
            r"Route::",
            r"Eloquent",
            r"@extends\(",
            r"@section\(",
            r"Auth::",
        ],
        "weight": 1.3,
    },
    "symfony": {
        "extensions": [".php", ".twig"],
        "config_files": ["symfony.lock", "composer.json"],
        "patterns": [
            r"Symfony\\\\",
            r"@Route\(",
            r"extends\s+AbstractController",
            r"{% extends",
            r"{% block",
        ],
        "weight": 1.3,
    },

    # Java
    "java_servlet": {
        "extensions": [".java", ".jsp"],
        "config_files": ["web.xml"],
        "patterns": [
            r"extends\s+HttpServlet",
            r"doGet\(",
            r"doPost\(",
            r"HttpServletRequest",
            r"HttpServletResponse",
        ],
        "weight": 1.2,
    },
    "spring": {
        "extensions": [".java"],
        "config_files": ["pom.xml", "build.gradle", "application.properties", "application.yml"],
        "patterns": [
            r"@SpringBootApplication",
            r"@RestController",
            r"@Service",
            r"@Repository",
            r"@Autowired",
            r"SpringApplication\.run",
        ],
        "weight": 1.3,
    },
    "struts": {
        "extensions": [".java", ".jsp"],
        "config_files": ["struts.xml", "struts-config.xml"],
        "patterns": [
            r"extends\s+ActionSupport",
            r"extends\s+Action",
            r"ActionForward",
            r"ActionMapping",
        ],
        "weight": 1.4,
    },

    # Python
    "django": {
        "extensions": [".py", ".html"],
        "config_files": ["manage.py", "settings.py", "urls.py"],
        "patterns": [
            r"from django",
            r"import django",
            r"models\.Model",
            r"{% block",
            r"{% extends",
            r"INSTALLED_APPS",
        ],
        "weight": 1.3,
    },
    "flask": {
        "extensions": [".py"],
        "config_files": [],
        "patterns": [
            r"from flask import",
            r"Flask\(__name__\)",
            r"@app\.route",
            r"render_template\(",
        ],
        "weight": 1.2,
    },
    "fastapi": {
        "extensions": [".py"],
        "config_files": [],
        "patterns": [
            r"from fastapi import",
            r"FastAPI\(",
            r"@app\.(get|post|put|delete)",
            r"async def",
            r"Depends\(",
        ],
        "weight": 1.2,
    },
}

# Database definitions
DATABASE_DEFINITIONS = {
    "sqlserver": {
        "connection_patterns": [
            r"Data Source=",
            r"Server=.*\.database\.windows\.net",
            r"SqlConnection",
            r"System\.Data\.SqlClient",
            r"SQLOLEDB",
        ],
        "sql_patterns": [
            r"@@IDENTITY",
            r"GETDATE\(\)",
            r"ISNULL\(",
            r"TOP\s+\d+",
            r"WITH\s*\(NOLOCK\)",
            r"sp_executesql",
        ],
        "config_files": ["web.config", "appsettings.json"],
    },
    "oracle": {
        "connection_patterns": [
            r"Data Source=.*\.oracle",
            r"OracleConnection",
            r"Oracle\.DataAccess",
            r"ODP\.NET",
            r"TNS_ADMIN",
        ],
        "sql_patterns": [
            r"SYSDATE",
            r"NVL\(",
            r"DECODE\(",
            r"ROWNUM",
            r"CONNECT BY",
            r"START WITH",
            r"DBMS_",
        ],
        "config_files": ["tnsnames.ora", "web.config"],
    },
    "mysql": {
        "connection_patterns": [
            r"mysql://",
            r"MySqlConnection",
            r"mysqli_",
            r"mysql_connect",
            r"PDO.*mysql",
        ],
        "sql_patterns": [
            r"NOW\(\)",
            r"IFNULL\(",
            r"LIMIT\s+\d+",
            r"AUTO_INCREMENT",
            r"ENGINE\s*=\s*InnoDB",
        ],
        "config_files": ["my.cnf", ".my.cnf"],
    },
    "postgresql": {
        "connection_patterns": [
            r"postgres://",
            r"postgresql://",
            r"NpgsqlConnection",
            r"psycopg2",
            r"asyncpg",
        ],
        "sql_patterns": [
            r"SERIAL",
            r"::text",
            r"::integer",
            r"COALESCE\(",
            r"RETURNING",
            r"ON CONFLICT",
        ],
        "config_files": ["pg_hba.conf", "postgresql.conf"],
    },
}


class StackDetectionService:
    """
    Comprehensive stack detection service for legacy code analysis.
    """

    SCANNABLE_EXTENSIONS = {
        ".cs", ".vb", ".aspx", ".ascx", ".master", ".cshtml", ".razor",
        ".js", ".jsx", ".ts", ".tsx", ".vue", ".mjs",
        ".php", ".blade.php", ".twig",
        ".java", ".jsp", ".groovy", ".kt",
        ".py", ".pyx",
        ".rb", ".erb",
        ".go",
        ".rs",
        ".sql",
    }

    CODE_EXTENSIONS = SCANNABLE_EXTENSIONS | {
        ".css", ".scss", ".less", ".sass",
        ".html", ".htm", ".xml", ".xsl", ".xslt",
        ".json", ".yaml", ".yml", ".toml",
        ".sh", ".bash", ".ps1", ".bat", ".cmd",
        ".c", ".cpp", ".h", ".hpp",
        ".swift", ".m", ".mm",
    }

    SKIP_DIRS = {
        "node_modules", "vendor", "packages", ".git", ".svn", ".hg",
        "bin", "obj", "target", "dist", "build", "out", "__pycache__",
        ".idea", ".vs", ".vscode", "coverage", ".next", ".nuxt",
    }

    MAX_SCAN_SIZE = 5 * 1024 * 1024

    def __init__(self, repo_path: str):
        """Initialize with repository path"""
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self.result = ScanResult(repo_path=str(self.repo_path))
        self._file_cache: Dict[str, str] = {}

    def scan(self) -> ScanResult:
        """Perform complete stack detection scan."""
        start_time = time.time()
        try:
            self._scan_files()
            self._detect_framework_configs()
            self._detect_stacks()
            self._detect_database()
            self._run_lizard()
            self._determine_stack_hierarchy()
        except Exception as e:
            self.result.errors.append(f"Scan error: {str(e)}")
        finally:
            self.result.detection_time_ms = int((time.time() - start_time) * 1000)
        return self.result

    def _scan_files(self) -> None:
        """Scan repository for files and count extensions"""
        file_counts: Dict[str, int] = defaultdict(int)
        total_loc = 0
        total_files = 0

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for filename in files:
                filepath = Path(root) / filename
                ext = filepath.suffix.lower()

                if filename.endswith(".aspx.cs"):
                    ext = ".aspx.cs"
                elif filename.endswith(".aspx.vb"):
                    ext = ".aspx.vb"
                elif filename.endswith(".blade.php"):
                    ext = ".blade.php"
                elif filename.endswith(".component.ts"):
                    ext = ".component.ts"
                elif filename.endswith(".service.ts"):
                    ext = ".service.ts"
                elif filename.endswith(".module.ts"):
                    ext = ".module.ts"

                if ext in self.CODE_EXTENSIONS:
                    file_counts[ext] += 1
                    total_files += 1
                    try:
                        loc = self._count_lines(filepath)
                        total_loc += loc
                    except Exception:
                        pass

        self.result.file_inventory = dict(file_counts)
        self.result.total_files = total_files
        self.result.total_loc = total_loc

    def _count_lines(self, filepath: Path) -> int:
        """Count non-empty, non-comment lines"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            count = 0
            in_block_comment = False

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if "/*" in stripped:
                    in_block_comment = True
                if "*/" in stripped:
                    in_block_comment = False
                    continue
                if in_block_comment:
                    continue
                if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("--"):
                    continue
                count += 1

            return count
        except Exception:
            return 0

    def _detect_framework_configs(self) -> None:
        """Detect framework configuration files"""
        for stack_name, stack_def in STACK_DEFINITIONS.items():
            for config_pattern in stack_def.get("config_files", []):
                matches = list(self.repo_path.rglob(config_pattern))

                for match in matches:
                    if any(skip in str(match) for skip in self.SKIP_DIRS):
                        continue

                    if stack_name not in self.result.stack_detections:
                        self.result.stack_detections[stack_name] = StackDetection(
                            stack_name=stack_name
                        )

                    rel_path = str(match.relative_to(self.repo_path))
                    self.result.stack_detections[stack_name].config_files.append(rel_path)
                    self.result.stack_detections[stack_name].evidence.append(
                        f"Config file: {rel_path}"
                    )

    def _detect_stacks(self) -> None:
        """Detect stacks by scanning source files for patterns"""
        pattern_matches: Dict[str, int] = defaultdict(int)
        file_matches: Dict[str, Set[str]] = defaultdict(set)

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for filename in files:
                filepath = Path(root) / filename
                ext = filepath.suffix.lower()

                if filename.endswith(".aspx.cs"):
                    ext = ".aspx.cs"
                elif filename.endswith(".blade.php"):
                    ext = ".blade.php"

                if ext not in self.SCANNABLE_EXTENSIONS and ext not in [".aspx.cs", ".aspx.vb", ".blade.php"]:
                    continue

                try:
                    if filepath.stat().st_size > self.MAX_SCAN_SIZE:
                        continue
                except Exception:
                    continue

                try:
                    content = self._read_file(filepath)
                except Exception:
                    continue

                for stack_name, stack_def in STACK_DEFINITIONS.items():
                    stack_extensions = set(stack_def.get("extensions", []))
                    if ext in stack_extensions or any(filename.endswith(e) for e in stack_extensions):
                        file_matches[stack_name].add(str(filepath))

                    for pattern in stack_def.get("patterns", []):
                        try:
                            if re.search(pattern, content, re.IGNORECASE):
                                pattern_matches[stack_name] += 1
                                file_matches[stack_name].add(str(filepath))
                        except re.error:
                            pass

        for stack_name, match_count in pattern_matches.items():
            if stack_name not in self.result.stack_detections:
                self.result.stack_detections[stack_name] = StackDetection(
                    stack_name=stack_name
                )

            detection = self.result.stack_detections[stack_name]
            detection.pattern_matches = match_count
            detection.file_count = len(file_matches.get(stack_name, set()))
            detection.evidence.append(f"Pattern matches: {match_count}")
            detection.evidence.append(f"Files matched: {detection.file_count}")

    def _read_file(self, filepath: Path) -> str:
        """Read file content with caching"""
        str_path = str(filepath)
        if str_path not in self._file_cache:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self._file_cache[str_path] = f.read()
        return self._file_cache[str_path]

    def _detect_database(self) -> None:
        """Detect database type from connection strings and SQL patterns"""
        db_scores: Dict[str, float] = defaultdict(float)
        db_evidence: Dict[str, List[str]] = defaultdict(list)

        config_patterns = ["*.config", "*.json", "*.yml", "*.yaml", "*.properties", "*.env"]

        for pattern in config_patterns:
            for config_file in self.repo_path.rglob(pattern):
                if any(skip in str(config_file) for skip in self.SKIP_DIRS):
                    continue

                try:
                    content = self._read_file(config_file)
                    rel_path = str(config_file.relative_to(self.repo_path))

                    for db_name, db_def in DATABASE_DEFINITIONS.items():
                        for pat in db_def.get("connection_patterns", []):
                            if re.search(pat, content, re.IGNORECASE):
                                db_scores[db_name] += 2.0
                                db_evidence[db_name].append(f"Connection pattern in {rel_path}")
                except Exception:
                    pass

        sql_extensions = {".sql", ".cs", ".java", ".php", ".py", ".vb"}

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for filename in files:
                filepath = Path(root) / filename
                if filepath.suffix.lower() not in sql_extensions:
                    continue

                try:
                    content = self._read_file(filepath)
                    rel_path = str(filepath.relative_to(self.repo_path))

                    for db_name, db_def in DATABASE_DEFINITIONS.items():
                        for pat in db_def.get("sql_patterns", []):
                            matches = len(re.findall(pat, content, re.IGNORECASE))
                            if matches > 0:
                                db_scores[db_name] += 0.5 * matches
                                if f"SQL pattern in {rel_path}" not in db_evidence[db_name]:
                                    db_evidence[db_name].append(f"SQL pattern in {rel_path}")
                except Exception:
                    pass

        if db_scores:
            primary_db = max(db_scores.items(), key=lambda x: x[1])
            if primary_db[1] > 2.0:
                self.result.database_type = primary_db[0]
                self.result.database_evidence = db_evidence[primary_db[0]][:10]

    def _run_lizard(self) -> None:
        """Run Lizard complexity analysis if available"""
        try:
            result = subprocess.run(
                ["lizard", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.result.errors.append("Lizard not installed")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.result.errors.append("Lizard not available")
            return

        try:
            result = subprocess.run(
                ["lizard", "-l", "python", "-l", "java", "-l", "csharp",
                 "-l", "javascript", "-l", "php", "--json", str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)

                functions = data.get("functions", [])
                if functions:
                    complexities = [f.get("cyclomatic_complexity", 0) for f in functions]
                    nlocs = [f.get("nloc", 0) for f in functions]

                    self.result.complexity = ComplexityMetrics(
                        avg_cyclomatic=sum(complexities) / len(complexities) if complexities else 0,
                        max_cyclomatic=max(complexities) if complexities else 0,
                        total_functions=len(functions),
                        high_complexity_count=len([c for c in complexities if c > 10]),
                        nloc=sum(nlocs)
                    )
        except subprocess.TimeoutExpired:
            self.result.errors.append("Lizard analysis timed out")
        except json.JSONDecodeError:
            self.result.errors.append("Failed to parse Lizard output")
        except Exception as e:
            self.result.errors.append(f"Lizard error: {str(e)}")

    def _determine_stack_hierarchy(self) -> None:
        """Determine primary and secondary stacks based on confidence scores"""
        for stack_name, detection in self.result.stack_detections.items():
            stack_def = STACK_DEFINITIONS.get(stack_name, {})
            weight = stack_def.get("weight", 1.0)

            confidence = 0.0

            if detection.config_files:
                confidence += 0.3 * len(detection.config_files)

            if detection.pattern_matches > 0:
                confidence += min(0.4, 0.02 * detection.pattern_matches)

            if detection.file_count > 0:
                confidence += min(0.3, 0.01 * detection.file_count)

            confidence *= weight
            detection.confidence = min(1.0, confidence)

        sorted_stacks = sorted(
            self.result.stack_detections.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )

        if sorted_stacks:
            self.result.primary_stack = sorted_stacks[0][0]
            self.result.secondary_stacks = [
                name for name, det in sorted_stacks[1:6]
                if det.confidence >= 0.2
            ]

    def detect_stacks(
        self,
        project_path: Optional[str] = None,
        max_files: int = 1000,
        scan_depth: int = 3,
    ) -> ScanResult:
        """
        Wrapper method for scanning stacks in a project.

        Args:
            project_path: Optional path (uses repo_path if not provided)
            max_files: Maximum files to scan
            scan_depth: Directory depth to scan

        Returns:
            ScanResult with detected stacks
        """
        # If a different path is provided, create a new service for it
        if project_path and str(project_path) != str(self.repo_path):
            temp_service = StackDetectionService(project_path)
            return temp_service.scan()
        return self.scan()

    @property
    def primary_stacks(self) -> List[str]:
        """Get primary stacks as a list."""
        if self.result.primary_stack:
            return [self.result.primary_stack] + self.result.secondary_stacks
        return self.result.secondary_stacks

    def get_recommended_agents(self, result: ScanResult) -> List[Tuple[str, str]]:
        """
        Get recommended agents based on scan result.

        Args:
            result: ScanResult from scan

        Returns:
            List of (role, stack) tuples
        """
        recommendations = []

        # Map stacks to agent roles
        stack_to_roles = {
            "aspnet_webforms": ["backend_dev", "frontend_dev"],
            "aspnet_mvc": ["backend_dev", "frontend_dev"],
            "aspnet_core": ["backend_dev", "api_dev"],
            "csharp": ["backend_dev"],
            "vbnet": ["backend_dev"],
            "python": ["backend_dev", "data_engineer"],
            "javascript": ["frontend_dev"],
            "typescript": ["frontend_dev", "fullstack_dev"],
            "react": ["frontend_dev"],
            "vue": ["frontend_dev"],
            "angular": ["frontend_dev"],
            "java": ["backend_dev"],
            "php": ["backend_dev", "frontend_dev"],
            "go": ["backend_dev", "infra_dev"],
            "rust": ["backend_dev", "systems_dev"],
            "sql_server": ["db_admin", "data_engineer"],
            "oracle": ["db_admin", "data_engineer"],
            "postgresql": ["db_admin"],
            "mysql": ["db_admin"],
        }

        # Get all stacks
        all_stacks = []
        if result.primary_stack:
            all_stacks.append(result.primary_stack)
        all_stacks.extend(result.secondary_stacks)

        # Add recommendations
        for stack in all_stacks:
            roles = stack_to_roles.get(stack, ["backend_dev"])
            for role in roles:
                if (role, stack) not in recommendations:
                    recommendations.append((role, stack))

        return recommendations

    def to_dict(self, result: ScanResult) -> Dict[str, Any]:
        """
        Convert ScanResult to dictionary.

        Args:
            result: ScanResult to convert

        Returns:
            Dictionary representation
        """
        return {
            "repo_path": result.repo_path,
            "total_files": result.total_files,
            "total_loc": result.total_loc,
            # New terminology: 1 tech_stack with multiple technologies
            "tech_stack": result.tech_stack,
            "technologies": result.technologies,
            "technology_summary": result.technology_summary,
            # Backward compatible fields
            "primary_stack": result.primary_stack,
            "primary_stacks": [result.primary_stack] if result.primary_stack else [],
            "secondary_stacks": result.secondary_stacks,
            "database_type": result.database_type,
            "database_evidence": result.database_evidence,
            "file_inventory": result.file_inventory,
            "errors": result.errors,
            "project_type": result.project_type,
            "frameworks": result.frameworks,
            "detection_time_ms": result.detection_time_ms,
        }


def get_stack_detection_service(repo_path: str) -> StackDetectionService:
    """Factory function to create StackDetectionService instance"""
    return StackDetectionService(repo_path)


# Backwards compatibility aliases
DetectionResult = ScanResult
StackInfo = StackDetection

# Derived exports for backwards compatibility with tests
FILE_EXTENSION_MAP = {
    ".py": "python", ".pyx": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cs": "csharp", ".vb": "vbnet",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".h": "cpp", ".hpp": "cpp",
    ".c": "c",
}

CONFIG_FILE_PATTERNS = {
    "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
    "javascript": ["package.json", ".npmrc", "yarn.lock"],
    "typescript": ["tsconfig.json", "package.json"],
    "go": ["go.mod", "go.sum"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "csharp": ["*.csproj", "*.sln", "packages.config"],
}

FRAMEWORK_PATTERNS = {
    "python": {"fastapi": r"from fastapi", "django": r"from django", "flask": r"from flask"},
    "javascript": {"react": r"from ['\"]react", "vue": r"from ['\"]vue", "angular": r"@angular"},
    "go": {"gin": r"github.com/gin-gonic", "echo": r"github.com/labstack/echo"},
    "rust": {"actix": r"actix-web", "rocket": r"rocket", "axum": r"axum"},
}

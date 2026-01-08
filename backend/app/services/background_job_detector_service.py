"""
Background Job Detector Service - Week 131

Detects scheduled tasks, batch jobs, and background processes in legacy codebases.

Detection patterns:
- Naming: Nachtjob, Batch, Scheduler, Cron, Timer
- Directories: /Beheer/, /Admin/, /Batch/, /Jobs/
- Code: [WebMethod], Timer_Elapsed, Task.Run, sp_Agent
- Tables: *Log, *Batch, *Job, *Queue suffixes
- Config: Quartz.NET, Hangfire, Windows Task Scheduler

Agent: Miguel (Migration Architect)
"""
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import logging

from app.models.week131_research import (
    BackgroundJob,
    BackgroundJobDetectionResult,
    JobType,
    TriggerType,
    DetectionMethod,
    ResourceIntensity,
)

logger = logging.getLogger(__name__)


# Detection pattern configurations
NAMING_PATTERNS = {
    'nachtjob': (JobType.NIGHTLY, 0.9),
    'nightjob': (JobType.NIGHTLY, 0.9),
    'nightly': (JobType.NIGHTLY, 0.85),
    'batch': (JobType.ON_DEMAND, 0.8),
    'scheduler': (JobType.CRON, 0.85),
    'cron': (JobType.CRON, 0.9),
    'timer': (JobType.INTERVAL, 0.8),
    'job': (JobType.ON_DEMAND, 0.6),
    'task': (JobType.ON_DEMAND, 0.5),
    'worker': (JobType.ON_DEMAND, 0.7),
    'processor': (JobType.ON_DEMAND, 0.6),
    'daemon': (JobType.STARTUP, 0.8),
    'service': (JobType.STARTUP, 0.5),
    'background': (JobType.ON_DEMAND, 0.7),
    'queue': (JobType.EVENT_DRIVEN, 0.75),
    'handler': (JobType.EVENT_DRIVEN, 0.5),
}

DIRECTORY_PATTERNS = {
    '/beheer/': (JobType.ON_DEMAND, 0.7),
    '/admin/': (JobType.ON_DEMAND, 0.6),
    '/batch/': (JobType.ON_DEMAND, 0.85),
    '/jobs/': (JobType.ON_DEMAND, 0.85),
    '/tasks/': (JobType.ON_DEMAND, 0.8),
    '/schedulers/': (JobType.CRON, 0.9),
    '/workers/': (JobType.ON_DEMAND, 0.8),
    '/background/': (JobType.ON_DEMAND, 0.8),
    '/services/': (JobType.STARTUP, 0.4),
    '/daemons/': (JobType.STARTUP, 0.85),
}

CODE_PATTERNS = {
    # .NET patterns
    r'\[WebMethod\]': (TriggerType.HTTP, 0.6),
    r'Timer_Elapsed': (TriggerType.TIMER, 0.9),
    r'System\.Timers\.Timer': (TriggerType.TIMER, 0.85),
    r'Task\.Run\s*\(': (TriggerType.MANUAL, 0.5),
    r'BackgroundWorker': (TriggerType.MANUAL, 0.8),
    r'ThreadPool\.QueueUserWorkItem': (TriggerType.MANUAL, 0.7),
    r'HostedService|IHostedService': (TriggerType.STARTUP, 0.9),
    r'BackgroundService': (TriggerType.STARTUP, 0.9),
    # SQL Agent patterns
    r'sp_add_job': (TriggerType.SQL_AGENT, 0.95),
    r'sp_add_jobstep': (TriggerType.SQL_AGENT, 0.95),
    r'msdb\.dbo\.sysjobs': (TriggerType.SQL_AGENT, 0.9),
    r'EXEC\s+msdb': (TriggerType.SQL_AGENT, 0.85),
    # Quartz.NET patterns
    r'IJob\s*{|:.*IJob': (TriggerType.QUARTZ, 0.9),
    r'ITrigger|CronTrigger|SimpleTrigger': (TriggerType.QUARTZ, 0.85),
    r'IScheduler\.ScheduleJob': (TriggerType.QUARTZ, 0.9),
    r'JobBuilder\.Create': (TriggerType.QUARTZ, 0.9),
    # Hangfire patterns
    r'BackgroundJob\.Enqueue': (TriggerType.HANGFIRE, 0.9),
    r'RecurringJob\.AddOrUpdate': (TriggerType.HANGFIRE, 0.95),
    r'\[AutomaticRetry\]': (TriggerType.HANGFIRE, 0.8),
    r'IBackgroundJobClient': (TriggerType.HANGFIRE, 0.85),
    # Windows Task Scheduler
    r'TaskScheduler|ITaskService': (TriggerType.WINDOWS_SCHEDULER, 0.9),
    r'RegisterTaskDefinition': (TriggerType.WINDOWS_SCHEDULER, 0.9),
    # Event-driven
    r'MessageQueue|MSMQ': (TriggerType.MESSAGE_QUEUE, 0.85),
    r'RabbitMQ|IModel\.BasicConsume': (TriggerType.MESSAGE_QUEUE, 0.9),
    r'ServiceBus|IMessageReceiver': (TriggerType.MESSAGE_QUEUE, 0.85),
}

TABLE_SUFFIX_PATTERNS = [
    ('log', 0.5),
    ('batch', 0.8),
    ('job', 0.85),
    ('queue', 0.8),
    ('task', 0.7),
    ('schedule', 0.85),
    ('history', 0.4),
    ('audit', 0.3),
]

CONFIG_PATTERNS = {
    # Quartz.NET config
    'quartz': {
        'pattern': r'<quartz>|quartz\.config|Quartz\.Impl',
        'trigger_type': TriggerType.QUARTZ,
        'confidence': 0.9,
    },
    # Hangfire config
    'hangfire': {
        'pattern': r'<hangfire>|UseHangfire|HangfireConfiguration',
        'trigger_type': TriggerType.HANGFIRE,
        'confidence': 0.9,
    },
    # Windows Service
    'windows_service': {
        'pattern': r'ServiceBase|OnStart|OnStop.*override',
        'trigger_type': TriggerType.WINDOWS_SERVICE,
        'confidence': 0.85,
    },
}

ERROR_HANDLING_PATTERNS = [
    r'try\s*{.*catch',
    r'Try\s+.*\s+Catch',  # VB.NET
    r'On\s+Error\s+',     # VB6/VBScript
    r'BEGIN\s+TRY.*END\s+TRY',  # T-SQL
    r'\.catch\s*\(',      # JavaScript/TypeScript
    r'except\s*:',        # Python
]

LOGGING_PATTERNS = [
    r'Log\.|Logger\.|ILogger',
    r'Console\.Write',
    r'Debug\.Print',
    r'Trace\.',
    r'EventLog\.',
    r'NLog|log4net|Serilog',
    r'logging\.',  # Python
    r'console\.log',  # JavaScript
]


class BackgroundJobDetectorService:
    """
    Detects background jobs, scheduled tasks, and batch processes in legacy codebases.

    Uses multiple detection strategies:
    1. Naming conventions (Nachtjob, Batch, etc.)
    2. Directory patterns (/Beheer/, /Jobs/, etc.)
    3. Code patterns ([WebMethod], Timer_Elapsed, etc.)
    4. Database table patterns (*Job, *Queue, etc.)
    5. Configuration patterns (Quartz, Hangfire, etc.)
    """

    def __init__(self):
        self._job_counter = 0
        self._detected_jobs: Dict[str, BackgroundJob] = {}

    def detect(
        self,
        project_path: Path,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> BackgroundJobDetectionResult:
        """
        Detect all background jobs in a project.

        Args:
            project_path: Path to the project root
            include_extensions: File extensions to scan (default: common code files)
            exclude_patterns: Glob patterns to exclude

        Returns:
            BackgroundJobDetectionResult with detected jobs and metadata
        """
        start_time = time.time()
        errors: List[str] = []
        self._job_counter = 0
        self._detected_jobs = {}

        if not project_path.exists():
            return BackgroundJobDetectionResult(
                success=False,
                errors=[f"Project path does not exist: {project_path}"],
                jobs=[],
            )

        # Default extensions for code files
        if include_extensions is None:
            include_extensions = [
                '.vb', '.cs', '.vbs', '.asp', '.aspx', '.ascx',
                '.sql', '.py', '.js', '.ts', '.java', '.go',
                '.config', '.xml', '.json', '.yaml', '.yml',
            ]

        if exclude_patterns is None:
            exclude_patterns = [
                '**/node_modules/**',
                '**/bin/**',
                '**/obj/**',
                '**/.git/**',
                '**/packages/**',
            ]

        try:
            # Collect files
            all_files = self._collect_files(project_path, include_extensions, exclude_patterns)

            # Separate file types
            code_files = [f for f in all_files if f.suffix.lower() in ['.vb', '.cs', '.vbs', '.asp', '.aspx', '.py', '.js', '.ts', '.java', '.go']]
            sql_files = [f for f in all_files if f.suffix.lower() == '.sql']
            config_files = [f for f in all_files if f.suffix.lower() in ['.config', '.xml', '.json', '.yaml', '.yml']]

            # Run detection strategies
            self._detect_by_naming(code_files)
            self._detect_by_directory(code_files)
            self._detect_by_code_patterns(code_files)
            self._detect_sql_agent_jobs(sql_files)
            self._detect_from_config(config_files)

            # Analyze additional properties
            for job_key, job in self._detected_jobs.items():
                source_path = project_path / job.source_file
                if source_path.exists():
                    content = self._read_file_safe(source_path)
                    if content:
                        job.has_error_handling = self._analyze_error_handling(content)
                        job.error_handling_pattern = self._get_error_handling_pattern(content)
                        job.has_logging = self._analyze_logging(content)
                        job.database_dependencies = self._extract_db_dependencies(content)
                        job.service_dependencies = self._extract_service_dependencies(content)

            jobs = list(self._detected_jobs.values())
            duration_ms = int((time.time() - start_time) * 1000)

            # Calculate statistics
            job_type_counts = {}
            trigger_type_counts = {}
            for job in jobs:
                jt = job.job_type.value if isinstance(job.job_type, JobType) else str(job.job_type)
                tt = job.trigger_type.value if isinstance(job.trigger_type, TriggerType) else str(job.trigger_type)
                job_type_counts[jt] = job_type_counts.get(jt, 0) + 1
                trigger_type_counts[tt] = trigger_type_counts.get(tt, 0) + 1

            return BackgroundJobDetectionResult(
                success=True,
                jobs=jobs,
                detection_stats={
                    "by_job_type": job_type_counts,
                    "by_trigger_type": trigger_type_counts,
                    "files_scanned": len(all_files),
                },
                duration_ms=duration_ms,
                errors=errors,
            )

        except Exception as e:
            logger.exception(f"Error detecting background jobs: {e}")
            return BackgroundJobDetectionResult(
                success=False,
                errors=[str(e)],
                jobs=[],
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _collect_files(
        self,
        project_path: Path,
        extensions: List[str],
        exclude_patterns: List[str],
    ) -> List[Path]:
        """Collect all files matching extensions, excluding patterns."""
        files = []
        for ext in extensions:
            for file_path in project_path.rglob(f'*{ext}'):
                # Check exclusions
                excluded = False
                rel_path = str(file_path.relative_to(project_path))
                for pattern in exclude_patterns:
                    if self._match_glob_pattern(rel_path, pattern):
                        excluded = True
                        break
                if not excluded:
                    files.append(file_path)
        return files

    def _match_glob_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob pattern matching."""
        import fnmatch
        # Normalize path separators
        path = path.replace('\\', '/')
        pattern = pattern.replace('\\', '/')
        return fnmatch.fnmatch(path, pattern)

    def _read_file_safe(self, file_path: Path) -> Optional[str]:
        """Read file content safely, handling encoding issues."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        self._job_counter += 1
        return f"BGJ-{self._job_counter:03d}"

    def _add_or_update_job(
        self,
        source_file: str,
        name: str,
        job_type: JobType,
        detection_method: DetectionMethod,
        confidence: float,
        trigger_type: TriggerType = TriggerType.MANUAL,
        schedule: Optional[str] = None,
        entry_point: Optional[str] = None,
        source_line_start: Optional[int] = None,
        source_line_end: Optional[int] = None,
        description: Optional[str] = None,
    ) -> BackgroundJob:
        """Add a new job or update existing one with higher confidence."""
        key = f"{source_file}:{name}"

        if key in self._detected_jobs:
            existing = self._detected_jobs[key]
            # Update if new detection has higher confidence
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.detection_method = detection_method
                if trigger_type != TriggerType.MANUAL:
                    existing.trigger_type = trigger_type
            return existing

        # Convert line start/end to source_lines tuple
        source_lines = (
            source_line_start or 0,
            source_line_end or source_line_start or 0
        )

        job = BackgroundJob(
            job_id=self._generate_job_id(),
            name=name,
            job_type=job_type,
            source_file=source_file,
            confidence=confidence,
            trigger_type=trigger_type,
            detection_method=detection_method,
            schedule=schedule,
            entry_point=entry_point or "",
            source_lines=source_lines,
            description=description or "",
        )
        self._detected_jobs[key] = job
        return job

    def _detect_by_naming(self, files: List[Path]) -> List[BackgroundJob]:
        """Detect jobs by file naming conventions."""
        detected = []

        for file_path in files:
            filename_lower = file_path.stem.lower()

            for pattern, (job_type, base_confidence) in NAMING_PATTERNS.items():
                if pattern in filename_lower:
                    job = self._add_or_update_job(
                        source_file=str(file_path),
                        name=file_path.stem,
                        job_type=job_type,
                        detection_method=DetectionMethod.NAMING,
                        confidence=base_confidence,
                    )
                    detected.append(job)
                    break  # Only match first pattern per file

        return detected

    def _detect_by_directory(self, files: List[Path]) -> List[BackgroundJob]:
        """Detect jobs by directory patterns."""
        detected = []

        for file_path in files:
            path_lower = str(file_path).lower().replace('\\', '/')

            for pattern, (job_type, base_confidence) in DIRECTORY_PATTERNS.items():
                if pattern in path_lower:
                    job = self._add_or_update_job(
                        source_file=str(file_path),
                        name=file_path.stem,
                        job_type=job_type,
                        detection_method=DetectionMethod.DIRECTORY,
                        confidence=base_confidence,
                    )
                    detected.append(job)
                    break

        return detected

    def _detect_by_code_patterns(self, files: List[Path]) -> List[BackgroundJob]:
        """Detect jobs by code patterns."""
        detected = []

        for file_path in files:
            content = self._read_file_safe(file_path)
            if not content:
                continue

            for pattern, (trigger_type, confidence) in CODE_PATTERNS.items():
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches:
                    # Find the line number of first match
                    first_match = matches[0]
                    line_num = content[:first_match.start()].count('\n') + 1

                    # Determine job type based on trigger
                    job_type = self._infer_job_type_from_trigger(trigger_type)

                    # Try to extract method/class name
                    entry_point = self._extract_entry_point(content, first_match.start())

                    job = self._add_or_update_job(
                        source_file=str(file_path),
                        name=entry_point or file_path.stem,
                        job_type=job_type,
                        detection_method=DetectionMethod.CODE_PATTERN,
                        confidence=confidence,
                        trigger_type=trigger_type,
                        entry_point=entry_point,
                        source_line_start=line_num,
                    )
                    detected.append(job)

        return detected

    def _detect_sql_agent_jobs(self, sql_files: List[Path]) -> List[BackgroundJob]:
        """Detect SQL Server Agent jobs from SQL files."""
        detected = []

        job_pattern = re.compile(
            r"sp_add_job\s+@job_name\s*=\s*N?['\"]([^'\"]+)['\"]",
            re.IGNORECASE
        )
        schedule_pattern = re.compile(
            r"sp_add_schedule.*@freq_type\s*=\s*(\d+)",
            re.IGNORECASE | re.DOTALL
        )

        for file_path in sql_files:
            content = self._read_file_safe(file_path)
            if not content:
                continue

            # Find job definitions
            for match in job_pattern.finditer(content):
                job_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Try to find schedule type
                schedule = None
                schedule_match = schedule_pattern.search(content)
                if schedule_match:
                    freq_type = int(schedule_match.group(1))
                    schedule = self._interpret_sql_freq_type(freq_type)

                job = self._add_or_update_job(
                    source_file=str(file_path),
                    name=job_name,
                    job_type=JobType.NIGHTLY if 'nacht' in job_name.lower() or 'night' in job_name.lower() else JobType.CRON,
                    detection_method=DetectionMethod.CONFIG,
                    confidence=0.95,
                    trigger_type=TriggerType.SQL_AGENT,
                    schedule=schedule,
                    source_line_start=line_num,
                    description=f"SQL Server Agent Job: {job_name}",
                )
                detected.append(job)

        return detected

    def _detect_from_config(self, config_files: List[Path]) -> List[BackgroundJob]:
        """Detect jobs from configuration files."""
        detected = []

        for file_path in config_files:
            content = self._read_file_safe(file_path)
            if not content:
                continue

            for config_name, config_info in CONFIG_PATTERNS.items():
                if re.search(config_info['pattern'], content, re.IGNORECASE):
                    job = self._add_or_update_job(
                        source_file=str(file_path),
                        name=f"{config_name}_configuration",
                        job_type=JobType.CRON,
                        detection_method=DetectionMethod.CONFIG,
                        confidence=config_info['confidence'],
                        trigger_type=config_info['trigger_type'],
                        description=f"Detected {config_name} configuration",
                    )
                    detected.append(job)

                    # Try to extract specific jobs from Quartz config
                    if config_name == 'quartz' and file_path.suffix.lower() == '.xml':
                        detected.extend(self._parse_quartz_config(file_path, content))

        return detected

    def _parse_quartz_config(self, file_path: Path, content: str) -> List[BackgroundJob]:
        """Parse Quartz.NET XML configuration for job definitions."""
        detected = []
        try:
            root = ET.fromstring(content)
            # Look for job definitions
            for job in root.iter():
                if 'job' in job.tag.lower():
                    name = job.get('name') or job.findtext('.//name') or 'Unknown'
                    cron = job.findtext('.//cron-expression')

                    bg_job = self._add_or_update_job(
                        source_file=str(file_path),
                        name=name,
                        job_type=JobType.CRON,
                        detection_method=DetectionMethod.CONFIG,
                        confidence=0.9,
                        trigger_type=TriggerType.QUARTZ,
                        schedule=cron,
                    )
                    detected.append(bg_job)
        except ET.ParseError:
            pass
        return detected

    def _infer_job_type_from_trigger(self, trigger_type: TriggerType) -> JobType:
        """Infer job type from trigger type."""
        mapping = {
            TriggerType.TIMER: JobType.INTERVAL,
            TriggerType.QUARTZ: JobType.CRON,
            TriggerType.HANGFIRE: JobType.CRON,
            TriggerType.SQL_AGENT: JobType.NIGHTLY,
            TriggerType.WINDOWS_SCHEDULER: JobType.CRON,
            TriggerType.WINDOWS_SERVICE: JobType.STARTUP,
            TriggerType.STARTUP: JobType.STARTUP,
            TriggerType.MESSAGE_QUEUE: JobType.EVENT_DRIVEN,
            TriggerType.HTTP: JobType.ON_DEMAND,
            TriggerType.MANUAL: JobType.ON_DEMAND,
        }
        return mapping.get(trigger_type, JobType.ON_DEMAND)

    def _extract_entry_point(self, content: str, position: int) -> Optional[str]:
        """Extract method or class name near a code pattern match."""
        # Look backwards for method/function declaration
        before = content[:position]

        # .NET method pattern
        method_match = re.search(
            r'(?:Public|Private|Protected|Friend)?\s*(?:Shared\s+)?(?:Sub|Function)\s+(\w+)',
            before[-500:],
            re.IGNORECASE
        )
        if method_match:
            return method_match.group(1)

        # C# method pattern
        method_match = re.search(
            r'(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?(?:\w+\s+)+(\w+)\s*\(',
            before[-500:],
            re.IGNORECASE
        )
        if method_match:
            return method_match.group(1)

        # Class pattern
        class_match = re.search(
            r'(?:Public\s+)?Class\s+(\w+)',
            before[-1000:],
            re.IGNORECASE
        )
        if class_match:
            return class_match.group(1)

        return None

    def _interpret_sql_freq_type(self, freq_type: int) -> str:
        """Interpret SQL Server Agent schedule frequency type."""
        freq_types = {
            1: 'Once',
            4: 'Daily',
            8: 'Weekly',
            16: 'Monthly (relative)',
            32: 'Monthly',
            64: 'On SQL Server Agent start',
            128: 'When CPU idle',
        }
        return freq_types.get(freq_type, f'freq_type={freq_type}')

    def _analyze_error_handling(self, content: str) -> bool:
        """Check if content has error handling patterns."""
        for pattern in ERROR_HANDLING_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True
        return False

    def _get_error_handling_pattern(self, content: str) -> Optional[str]:
        """Get the type of error handling used."""
        patterns = {
            r'try\s*{.*catch': 'try-catch (C#/JS)',
            r'Try\s+.*\s+Catch': 'Try-Catch (VB.NET)',
            r'On\s+Error\s+': 'On Error (VB6)',
            r'BEGIN\s+TRY': 'TRY-CATCH (T-SQL)',
            r'except\s*:': 'try-except (Python)',
        }
        for pattern, name in patterns.items():
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return name
        return None

    def _analyze_logging(self, content: str) -> bool:
        """Check if content has logging patterns."""
        for pattern in LOGGING_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    def _extract_db_dependencies(self, content: str) -> List[str]:
        """Extract database table/procedure dependencies."""
        dependencies = set()

        # SQL table references
        table_patterns = [
            r'FROM\s+(\[?\w+\]?\.?\[?\w+\]?)',
            r'JOIN\s+(\[?\w+\]?\.?\[?\w+\]?)',
            r'INTO\s+(\[?\w+\]?\.?\[?\w+\]?)',
            r'UPDATE\s+(\[?\w+\]?\.?\[?\w+\]?)',
            r'DELETE\s+FROM\s+(\[?\w+\]?\.?\[?\w+\]?)',
        ]
        for pattern in table_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                table = match.group(1).strip('[]')
                if table.lower() not in ('select', 'where', 'set'):
                    dependencies.add(table)

        # Stored procedure calls
        sp_patterns = [
            r'EXEC(?:UTE)?\s+(\[?\w+\]?\.?\[?\w+\]?)',
            r'\.ExecuteNonQuery.*"(\w+)"',
            r'\.ExecuteReader.*"(\w+)"',
        ]
        for pattern in sp_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                dependencies.add(match.group(1).strip('[]'))

        return list(dependencies)[:20]  # Limit to 20

    def _extract_service_dependencies(self, content: str) -> List[str]:
        """Extract external service dependencies."""
        dependencies = set()

        # HTTP endpoints
        url_pattern = r'https?://[^\s\'"<>]+'
        for match in re.finditer(url_pattern, content):
            url = match.group(0)
            # Extract domain
            domain_match = re.search(r'https?://([^/]+)', url)
            if domain_match:
                dependencies.add(domain_match.group(1))

        # Web service references
        ws_patterns = [
            r'WebService\s*\(\s*["\']([^"\']+)',
            r'ServiceReference\s*=\s*["\']([^"\']+)',
            r'\.asmx',
            r'\.svc',
        ]
        for pattern in ws_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                if match.lastindex:
                    dependencies.add(match.group(1))
                else:
                    dependencies.add(match.group(0))

        return list(dependencies)[:10]  # Limit to 10

    def detect_batch_tables(self, table_names: List[str]) -> List[str]:
        """
        Identify tables that likely store batch job data.

        Args:
            table_names: List of table names from the database

        Returns:
            List of table names that appear to be batch-related
        """
        batch_tables = []

        for table in table_names:
            table_lower = table.lower()
            for suffix, confidence in TABLE_SUFFIX_PATTERNS:
                if table_lower.endswith(suffix):
                    batch_tables.append(table)
                    break
            # Also check for batch-related prefixes
            if any(prefix in table_lower for prefix in ['batch', 'job', 'queue', 'task', 'schedule']):
                if table not in batch_tables:
                    batch_tables.append(table)

        return batch_tables

    def estimate_resource_intensity(self, job: BackgroundJob) -> ResourceIntensity:
        """
        Estimate the resource intensity of a background job.

        Based on:
        - Number of database dependencies
        - Presence of loops/batch processing patterns
        - File I/O patterns
        """
        intensity_score = 0

        # More DB dependencies = more intensive
        if len(job.database_dependencies) > 5:
            intensity_score += 2
        elif len(job.database_dependencies) > 2:
            intensity_score += 1

        # Service dependencies add complexity
        if len(job.service_dependencies) > 2:
            intensity_score += 1

        # Certain job types are typically more intensive
        if job.job_type in [JobType.NIGHTLY, JobType.ETL]:
            intensity_score += 2
        elif job.job_type == JobType.HOURLY:
            intensity_score += 1

        # Map score to intensity
        if intensity_score >= 4:
            return ResourceIntensity.HIGH
        elif intensity_score >= 2:
            return ResourceIntensity.MEDIUM
        else:
            return ResourceIntensity.LOW

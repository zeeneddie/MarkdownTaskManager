"""
Load Estimation Service - Week 131

Analyzes connection pooling, session state, and query complexity to estimate
concurrent user capacity for legacy applications.

Analysis components:
- web.config parsing: Min/Max Pool Size, Connection Timeout
- Session state: InProc/StateServer/SQLServer mode, timeout
- Code scanning: SqlConnection Using blocks, open/close ratio
- Query complexity: JOIN count, subqueries, lock patterns

Agent: Miguel (Migration Architect)
"""
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from app.models.research import (
    LoadEstimationResult,
    ConnectionPoolConfig,
    SessionStateConfig,
    QueryComplexityMetrics,
    SessionMode,
    CapacityBottleneck,
)

logger = logging.getLogger(__name__)


# Default connection pool settings (SQL Server defaults)
DEFAULT_MIN_POOL_SIZE = 0
DEFAULT_MAX_POOL_SIZE = 100
DEFAULT_CONNECTION_TIMEOUT = 15
DEFAULT_SESSION_TIMEOUT = 20


class LoadEstimationService:
    """
    Estimates concurrent user capacity based on connection pooling,
    session state configuration, and query complexity analysis.

    Capacity Formula:
    - base = max_pool_size * 0.8
    - if complex_queries: base /= 1.5
    - if very_complex: base /= 2
    - if session_inproc: base /= 2
    """

    def __init__(self):
        self._files_analyzed = 0

    def analyze(
        self,
        project_path: Path,
        include_sql_analysis: bool = True,
    ) -> LoadEstimationResult:
        """
        Analyze a project to estimate its concurrent user capacity.

        Args:
            project_path: Path to the project root
            include_sql_analysis: Whether to analyze SQL query complexity

        Returns:
            LoadEstimationResult with capacity estimation and recommendations
        """
        start_time = time.time()
        errors: List[str] = []
        self._files_analyzed = 0

        if not project_path.exists():
            return LoadEstimationResult(
                success=False,
                errors=[f"Project path does not exist: {project_path}"],
            )

        try:
            # Find configuration files
            config_files = list(project_path.rglob('web.config'))
            config_files.extend(project_path.rglob('app.config'))
            config_files.extend(project_path.rglob('appsettings.json'))

            # Find code files
            vb_files = list(project_path.rglob('*.vb'))
            cs_files = list(project_path.rglob('*.cs'))
            sql_files = list(project_path.rglob('*.sql')) if include_sql_analysis else []
            asp_files = list(project_path.rglob('*.asp'))
            asp_files.extend(project_path.rglob('*.aspx'))

            code_files = vb_files + cs_files + asp_files
            self._files_analyzed = len(config_files) + len(code_files) + len(sql_files)

            # 1. Parse connection pool configurations
            connection_pools: List[ConnectionPoolConfig] = []
            for config_file in config_files:
                try:
                    pools = self._parse_config_file(config_file)
                    connection_pools.extend(pools)
                except Exception as e:
                    errors.append(f"Error parsing {config_file}: {e}")

            # 2. Parse session state configuration
            session_config = self._parse_session_state(config_files)

            # 3. Count SqlConnection patterns
            using_block_count = 0
            total_sql_connections = 0
            open_count = 0
            close_count = 0

            for code_file in code_files:
                content = self._read_file_safe(code_file)
                if content:
                    using_block_count += self._count_using_blocks(content)
                    total_sql_connections += len(re.findall(r'SqlConnection|OleDbConnection|OdbcConnection', content, re.IGNORECASE))
                    open_count += len(re.findall(r'\.Open\s*\(', content))
                    close_count += len(re.findall(r'\.Close\s*\(', content))

            open_close_ratio = close_count / open_count if open_count > 0 else 0.0

            # 4. Analyze query complexity
            query_metrics = QueryComplexityMetrics()
            if include_sql_analysis:
                query_metrics = self._analyze_query_complexity(sql_files + code_files)

            # 5. Calculate session access patterns
            session_access_count = 0
            session_variables: set = set()
            for code_file in code_files:
                content = self._read_file_safe(code_file)
                if content:
                    access_count, variables = self._analyze_session_access(content)
                    session_access_count += access_count
                    session_variables.update(variables)

            # 6. Estimate capacity
            estimated_users, bottleneck, bottleneck_details = self._estimate_capacity(
                connection_pools,
                session_config,
                query_metrics,
                using_block_count,
                open_close_ratio,
            )

            # 7. Generate recommendations
            recommendations = self._generate_recommendations(
                connection_pools,
                session_config,
                query_metrics,
                using_block_count,
                open_close_ratio,
                estimated_users,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return LoadEstimationResult(
                success=True,
                connection_pools=connection_pools,
                total_sql_connections=total_sql_connections,
                using_block_count=using_block_count,
                open_close_ratio=round(open_close_ratio, 2),
                session_config=session_config,
                session_access_count=session_access_count,
                session_variable_count=len(session_variables),
                query_metrics=query_metrics,
                estimated_concurrent_users=estimated_users,
                capacity_bottleneck=bottleneck,
                bottleneck_details=bottleneck_details,
                recommendations=recommendations,
                files_analyzed=self._files_analyzed,
                duration_ms=duration_ms,
                errors=errors,
            )

        except Exception as e:
            logger.exception(f"Error analyzing load estimation: {e}")
            return LoadEstimationResult(
                success=False,
                errors=[str(e)],
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _read_file_safe(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def _parse_config_file(self, config_path: Path) -> List[ConnectionPoolConfig]:
        """Parse connection pool settings from config file."""
        pools = []

        if config_path.suffix.lower() == '.json':
            return self._parse_appsettings_json(config_path)

        content = self._read_file_safe(config_path)
        if not content:
            return pools

        try:
            root = ET.fromstring(content)

            # Find connectionStrings section
            conn_strings = root.find('.//connectionStrings')
            if conn_strings is not None:
                for add in conn_strings.findall('add'):
                    name = add.get('name', 'Unknown')
                    conn_str = add.get('connectionString', '')

                    pool_config = self._parse_connection_string(name, conn_str)
                    if pool_config:
                        pools.append(pool_config)

            # Also check appSettings for connection-related settings
            app_settings = root.find('.//appSettings')
            if app_settings is not None:
                for add in app_settings.findall('add'):
                    key = add.get('key', '')
                    value = add.get('value', '')
                    if 'connection' in key.lower() and '=' in value:
                        pool_config = self._parse_connection_string(key, value)
                        if pool_config:
                            pools.append(pool_config)

        except ET.ParseError as e:
            logger.warning(f"Failed to parse {config_path}: {e}")

        return pools

    def _parse_appsettings_json(self, config_path: Path) -> List[ConnectionPoolConfig]:
        """Parse connection pools from appsettings.json."""
        import json
        pools = []

        content = self._read_file_safe(config_path)
        if not content:
            return pools

        try:
            config = json.loads(content)
            conn_strings = config.get('ConnectionStrings', {})

            for name, conn_str in conn_strings.items():
                pool_config = self._parse_connection_string(name, conn_str)
                if pool_config:
                    pools.append(pool_config)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {config_path}: {e}")

        return pools

    def _parse_connection_string(self, name: str, conn_str: str) -> Optional[ConnectionPoolConfig]:
        """Parse a connection string to extract pool settings."""
        if not conn_str:
            return None

        # Extract common connection string parameters
        params = {}
        for part in conn_str.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key.strip().lower()] = value.strip()

        # Extract pool settings
        min_pool = DEFAULT_MIN_POOL_SIZE
        max_pool = DEFAULT_MAX_POOL_SIZE
        timeout = DEFAULT_CONNECTION_TIMEOUT

        for key, value in params.items():
            try:
                if key in ('min pool size', 'minpoolsize'):
                    min_pool = int(value)
                elif key in ('max pool size', 'maxpoolsize'):
                    max_pool = int(value)
                elif key in ('connection timeout', 'connect timeout', 'timeout'):
                    timeout = int(value)
            except ValueError:
                pass

        # Determine provider
        provider = 'Unknown'
        if any(k in params for k in ('server', 'data source')):
            if 'initial catalog' in params or 'database' in params:
                provider = 'SQL Server'
            elif 'provider' in params:
                provider = params['provider']

        return ConnectionPoolConfig(
            connection_string_name=name,
            min_pool_size=min_pool,
            max_pool_size=max_pool,
            connection_timeout=timeout,
            raw_connection_string=conn_str[:100] + '...' if len(conn_str) > 100 else conn_str,
        )

    def _parse_session_state(self, config_files: List[Path]) -> SessionStateConfig:
        """Parse session state configuration from web.config files."""
        session_config = SessionStateConfig()

        for config_path in config_files:
            if 'web.config' not in config_path.name.lower():
                continue

            content = self._read_file_safe(config_path)
            if not content:
                continue

            try:
                root = ET.fromstring(content)

                # Find sessionState element
                session_state = root.find('.//sessionState')
                if session_state is not None:
                    mode = session_state.get('mode', 'InProc')
                    timeout = session_state.get('timeout', str(DEFAULT_SESSION_TIMEOUT))
                    state_server = session_state.get('stateConnectionString', '')
                    sql_server = session_state.get('sqlConnectionString', '')

                    # Map mode string to enum
                    mode_mapping = {
                        'off': SessionMode.OFF,
                        'inproc': SessionMode.IN_PROC,
                        'stateserver': SessionMode.STATE_SERVER,
                        'sqlserver': SessionMode.SQL_SERVER,
                        'custom': SessionMode.CUSTOM,
                    }
                    session_mode = mode_mapping.get(mode.lower(), SessionMode.IN_PROC)

                    session_config = SessionStateConfig(
                        mode=session_mode,
                        timeout_minutes=int(timeout) if timeout.isdigit() else DEFAULT_SESSION_TIMEOUT,
                        state_server_address=state_server if state_server else None,
                        sql_connection_string=sql_server if sql_server else None,
                        cookieless=session_state.get('cookieless', 'false').lower() == 'true',
                    )
                    break  # Use first found

            except ET.ParseError:
                pass

        return session_config

    def _count_using_blocks(self, content: str) -> int:
        """Count proper Using blocks for database connections."""
        # VB.NET pattern: Using conn As New SqlConnection
        vb_pattern = r'Using\s+\w+\s+As\s+New\s+(?:Sql|OleDb|Odbc)Connection'
        # C# pattern: using (var conn = new SqlConnection
        cs_pattern = r'using\s*\(\s*(?:var\s+)?\w+\s*=\s*new\s+(?:Sql|OleDb|Odbc)Connection'

        vb_count = len(re.findall(vb_pattern, content, re.IGNORECASE))
        cs_count = len(re.findall(cs_pattern, content, re.IGNORECASE))

        return vb_count + cs_count

    def _analyze_query_complexity(self, files: List[Path]) -> QueryComplexityMetrics:
        """Analyze SQL query complexity across files."""
        metrics = QueryComplexityMetrics()

        total_queries = 0
        join_counts = []
        subquery_count = 0
        lock_hints = 0
        cursor_usage = 0
        temp_tables = 0

        for file_path in files:
            content = self._read_file_safe(file_path)
            if not content:
                continue

            # Find SQL queries (embedded in strings or standalone)
            sql_patterns = [
                r'SELECT\s+.+?\s+FROM',
                r'INSERT\s+INTO',
                r'UPDATE\s+\w+\s+SET',
                r'DELETE\s+FROM',
            ]

            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                total_queries += len(matches)

            # Count JOINs
            join_matches = re.findall(r'\bJOIN\b', content, re.IGNORECASE)
            join_counts.append(len(join_matches))

            # Count subqueries (nested SELECT)
            subquery_matches = re.findall(r'\(\s*SELECT\b', content, re.IGNORECASE)
            subquery_count += len(subquery_matches)

            # Count lock hints
            lock_matches = re.findall(r'WITH\s*\(\s*(?:NOLOCK|ROWLOCK|PAGELOCK|TABLOCK|UPDLOCK|XLOCK)', content, re.IGNORECASE)
            lock_hints += len(lock_matches)

            # Count cursor usage
            cursor_matches = re.findall(r'\bDECLARE\s+\w+\s+CURSOR\b', content, re.IGNORECASE)
            cursor_usage += len(cursor_matches)

            # Count temp tables
            temp_matches = re.findall(r'(?:INTO\s+)?#\w+', content)
            temp_tables += len(temp_matches)

        # Calculate averages
        avg_joins = sum(join_counts) / len(join_counts) if join_counts else 0
        max_joins = max(join_counts) if join_counts else 0

        metrics.total_queries = total_queries
        metrics.avg_joins_per_query = round(avg_joins, 2)
        metrics.max_joins_in_query = max_joins
        metrics.subquery_count = subquery_count
        metrics.uses_lock_hints = lock_hints > 0
        metrics.lock_hint_count = lock_hints
        metrics.uses_cursors = cursor_usage > 0
        metrics.cursor_count = cursor_usage
        metrics.uses_temp_tables = temp_tables > 0
        metrics.temp_table_count = temp_tables

        # Calculate complexity score (0-100)
        complexity_score = 0
        if avg_joins > 5:
            complexity_score += 30
        elif avg_joins > 3:
            complexity_score += 20
        elif avg_joins > 1:
            complexity_score += 10

        if subquery_count > 10:
            complexity_score += 25
        elif subquery_count > 5:
            complexity_score += 15
        elif subquery_count > 0:
            complexity_score += 5

        if cursor_usage > 5:
            complexity_score += 25
        elif cursor_usage > 0:
            complexity_score += 15

        if lock_hints > 10:
            complexity_score += 10
        elif lock_hints > 0:
            complexity_score += 5

        if temp_tables > 10:
            complexity_score += 10
        elif temp_tables > 0:
            complexity_score += 5

        metrics.complexity_score = min(100, complexity_score)

        return metrics

    def _analyze_session_access(self, content: str) -> Tuple[int, set]:
        """Analyze session variable access patterns."""
        variables = set()

        # Session("key") or Session["key"] patterns
        session_patterns = [
            r'Session\s*\(\s*["\'](\w+)["\']\s*\)',
            r'Session\s*\[\s*["\'](\w+)["\']\s*\]',
            r'HttpContext\.Current\.Session\s*\[\s*["\'](\w+)["\']\s*\]',
        ]

        access_count = 0
        for pattern in session_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            access_count += len(matches)
            variables.update(matches)

        return access_count, variables

    def _estimate_capacity(
        self,
        pools: List[ConnectionPoolConfig],
        session_config: SessionStateConfig,
        query_metrics: QueryComplexityMetrics,
        using_block_count: int,
        open_close_ratio: float,
    ) -> Tuple[int, CapacityBottleneck, str]:
        """
        Estimate concurrent user capacity.

        Formula:
        - base = max_pool_size * 0.8
        - if complex_queries: base /= 1.5
        - if very_complex: base /= 2
        - if session_inproc: base /= 2
        """
        # Get max pool size (use largest if multiple pools)
        if pools:
            max_pool = max(p.max_pool_size for p in pools)
        else:
            max_pool = DEFAULT_MAX_POOL_SIZE

        # Start with base capacity
        base_capacity = max_pool * 0.8
        bottleneck = CapacityBottleneck.NONE
        bottleneck_details = ""

        # Adjust for query complexity
        if query_metrics.complexity_score > 70:
            base_capacity /= 2
            bottleneck = CapacityBottleneck.QUERY_COMPLEXITY
            bottleneck_details = f"High query complexity (score: {query_metrics.complexity_score}). Consider query optimization."
        elif query_metrics.complexity_score > 40:
            base_capacity /= 1.5
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.QUERY_COMPLEXITY
                bottleneck_details = f"Moderate query complexity (score: {query_metrics.complexity_score})."

        # Adjust for cursor usage
        if query_metrics.uses_cursors and query_metrics.cursor_count > 5:
            base_capacity /= 1.5
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.CURSOR_USAGE
                bottleneck_details = f"Heavy cursor usage ({query_metrics.cursor_count} cursors). Consider set-based operations."

        # Adjust for session state
        if session_config.mode == SessionMode.IN_PROC:
            base_capacity /= 2
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.SESSION_STATE
                bottleneck_details = "InProc session state limits scalability. Consider StateServer or SQLServer mode."

        # Adjust for connection management quality
        if using_block_count == 0:
            # No Using blocks found - potential connection leak
            base_capacity /= 1.5
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.CONNECTION_POOL
                bottleneck_details = "No Using blocks detected for database connections. Potential connection leaks."
        elif open_close_ratio < 0.8:
            # Open/Close mismatch
            base_capacity /= 1.2
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.CONNECTION_POOL
                bottleneck_details = f"Open/Close ratio is {open_close_ratio:.2f}. Some connections may not be properly closed."

        # Adjust for pool size limits
        if max_pool < 50:
            base_capacity *= 0.8
            if bottleneck == CapacityBottleneck.NONE:
                bottleneck = CapacityBottleneck.POOL_SIZE
                bottleneck_details = f"Connection pool size ({max_pool}) is relatively small."

        estimated_users = max(1, int(base_capacity))

        return estimated_users, bottleneck, bottleneck_details

    def _generate_recommendations(
        self,
        pools: List[ConnectionPoolConfig],
        session_config: SessionStateConfig,
        query_metrics: QueryComplexityMetrics,
        using_block_count: int,
        open_close_ratio: float,
        estimated_users: int,
    ) -> List[str]:
        """Generate recommendations for improving capacity."""
        recommendations = []

        # Connection pool recommendations
        if pools:
            max_pool = max(p.max_pool_size for p in pools)
            if max_pool < 100:
                recommendations.append(
                    f"Consider increasing Max Pool Size from {max_pool} to at least 100 for better concurrency."
                )
        else:
            recommendations.append(
                "No connection pool configuration found. Add explicit pool settings in web.config."
            )

        # Connection management recommendations
        if using_block_count == 0:
            recommendations.append(
                "CRITICAL: No Using/using blocks for database connections detected. "
                "Implement proper connection disposal to prevent pool exhaustion."
            )
        elif open_close_ratio < 0.9:
            recommendations.append(
                f"Connection Open/Close ratio ({open_close_ratio:.2f}) suggests potential leaks. "
                "Review connection disposal patterns."
            )

        # Session state recommendations
        if session_config.mode == SessionMode.IN_PROC:
            recommendations.append(
                "InProc session state doesn't scale. Consider StateServer or SQL Server session state "
                "for load-balanced environments."
            )
        if session_config.timeout_minutes > 30:
            recommendations.append(
                f"Session timeout ({session_config.timeout_minutes} min) is high. "
                "Consider reducing to 20 minutes to free memory sooner."
            )

        # Query complexity recommendations
        if query_metrics.complexity_score > 60:
            recommendations.append(
                f"Query complexity score ({query_metrics.complexity_score}/100) is high. "
                "Consider query optimization and adding appropriate indexes."
            )
        if query_metrics.uses_cursors:
            recommendations.append(
                f"Found {query_metrics.cursor_count} cursor declarations. "
                "Replace with set-based operations where possible."
            )
        if query_metrics.subquery_count > 10:
            recommendations.append(
                f"High subquery count ({query_metrics.subquery_count}). "
                "Consider using CTEs or temp tables for complex queries."
            )

        # General recommendations based on capacity
        if estimated_users < 50:
            recommendations.append(
                "Estimated capacity is low. Consider architectural review before scaling."
            )
        elif estimated_users < 100:
            recommendations.append(
                "Moderate capacity. Monitor connection pool usage in production."
            )

        return recommendations

    def get_capacity_summary(self, result: LoadEstimationResult) -> Dict[str, Any]:
        """Get a summary of capacity estimation for display."""
        return {
            'estimated_concurrent_users': result.estimated_concurrent_users,
            'capacity_rating': self._get_capacity_rating(result.estimated_concurrent_users),
            'bottleneck': result.capacity_bottleneck.value if result.capacity_bottleneck else None,
            'bottleneck_details': result.bottleneck_details,
            'connection_pools': len(result.connection_pools),
            'session_mode': result.session_config.mode.value if result.session_config else None,
            'query_complexity_score': result.query_metrics.complexity_score if result.query_metrics else None,
            'recommendations_count': len(result.recommendations),
            'top_recommendations': result.recommendations[:3] if result.recommendations else [],
        }

    def _get_capacity_rating(self, users: int) -> str:
        """Get a human-readable capacity rating."""
        if users >= 200:
            return 'Excellent'
        elif users >= 100:
            return 'Good'
        elif users >= 50:
            return 'Moderate'
        elif users >= 20:
            return 'Limited'
        else:
            return 'Critical'

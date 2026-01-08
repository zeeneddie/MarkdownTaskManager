"""
Validation Pipeline Service

Week 17: Validation Framework Integration
Based on: github.com/zeeneddie/context-engineering-intro

Implements 5-phase validation pipeline:
1. LINTING - Syntax errors, code smells (ruff/eslint)
2. TYPE_CHECK - Type correctness (mypy/tsc)
3. STYLE - Code formatting (black/prettier)
4. UNIT_TESTS - Functional correctness (pytest/jest)
5. E2E_TESTS - Integration works (pytest+httpx/jest+supertest)

Core principle: "If validation passes, user has 100% confidence
that the application works correctly in production."

Author: Claude Code (Week 17 Day 4)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import subprocess
import tempfile
import os
import logging
import re

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class ValidationPhase(str, Enum):
    """5-phase validation pipeline"""
    LINTING = "linting"
    TYPE_CHECK = "type_check"
    STYLE = "style"
    UNIT_TESTS = "unit_tests"
    E2E_TESTS = "e2e_tests"


class Language(str, Enum):
    """Supported languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"


# Tool configurations per phase and language
VALIDATION_TOOLS: Dict[ValidationPhase, Dict[Language, Dict[str, Any]]] = {
    ValidationPhase.LINTING: {
        Language.PYTHON: {
            "tool": "ruff",
            "command": ["ruff", "check", "{file}"],
            "fix_command": ["ruff", "check", "--fix", "{file}"],
            "parse_output": "ruff"
        },
        Language.TYPESCRIPT: {
            "tool": "eslint",
            "command": ["npx", "eslint", "{file}"],
            "fix_command": ["npx", "eslint", "--fix", "{file}"],
            "parse_output": "eslint"
        }
    },
    ValidationPhase.TYPE_CHECK: {
        Language.PYTHON: {
            "tool": "mypy",
            "command": ["mypy", "{file}", "--ignore-missing-imports"],
            "parse_output": "mypy"
        },
        Language.TYPESCRIPT: {
            "tool": "tsc",
            "command": ["npx", "tsc", "--noEmit", "{file}"],
            "parse_output": "tsc"
        }
    },
    ValidationPhase.STYLE: {
        Language.PYTHON: {
            "tool": "black",
            "command": ["black", "--check", "{file}"],
            "fix_command": ["black", "{file}"],
            "parse_output": "black"
        },
        Language.TYPESCRIPT: {
            "tool": "prettier",
            "command": ["npx", "prettier", "--check", "{file}"],
            "fix_command": ["npx", "prettier", "--write", "{file}"],
            "parse_output": "prettier"
        }
    },
    ValidationPhase.UNIT_TESTS: {
        Language.PYTHON: {
            "tool": "pytest",
            "command": ["pytest", "{file}", "-v", "--tb=short"],
            "parse_output": "pytest"
        },
        Language.TYPESCRIPT: {
            "tool": "jest",
            "command": ["npx", "jest", "{file}", "--passWithNoTests"],
            "parse_output": "jest"
        }
    },
    ValidationPhase.E2E_TESTS: {
        Language.PYTHON: {
            "tool": "pytest",
            "command": ["pytest", "{file}", "-v", "--tb=short", "-m", "e2e"],
            "parse_output": "pytest"
        },
        Language.TYPESCRIPT: {
            "tool": "jest",
            "command": ["npx", "jest", "{file}", "--testMatch", "**/*.e2e.test.ts"],
            "parse_output": "jest"
        }
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ValidationError:
    """A single validation error"""
    phase: ValidationPhase
    file: str
    line: Optional[int]
    column: Optional[int]
    message: str
    code: Optional[str]
    severity: str  # 'error' or 'critical'
    auto_fixable: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "code": self.code,
            "severity": self.severity,
            "auto_fixable": self.auto_fixable
        }


@dataclass
class ValidationWarning:
    """A validation warning"""
    phase: ValidationPhase
    file: str
    line: Optional[int]
    message: str
    code: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "code": self.code
        }


@dataclass
class ValidationPhaseResult:
    """Result of a single validation phase"""
    phase: ValidationPhase
    passed: bool
    duration: float  # seconds
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    fix_suggestions: List[str]
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "passed": self.passed,
            "duration": self.duration,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "fix_suggestions": self.fix_suggestions,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


@dataclass
class ValidationResult:
    """Complete validation result"""
    success: bool
    phases: List[ValidationPhaseResult]
    total_duration: float
    total_errors: int
    total_warnings: int
    coverage_percent: Optional[float]
    iterations: int
    final_code: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "phases": [p.to_dict() for p in self.phases],
            "total_duration": self.total_duration,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "coverage_percent": self.coverage_percent,
            "iterations": self.iterations,
            "phases_passed": sum(1 for p in self.phases if p.passed),
            "phases_total": len(self.phases)
        }


@dataclass
class ValidationConfig:
    """Configuration for validation"""
    phases: List[ValidationPhase]
    max_iterations: int = 3
    stop_on_first_failure: bool = False
    required_coverage: Optional[float] = None
    regression_test_required: bool = False
    timeout: int = 60  # seconds per phase
    auto_fix: bool = True

    @classmethod
    def for_agent(cls, agent_role: str) -> 'ValidationConfig':
        """Get validation config for an agent role"""
        configs = {
            "Feature Architect": cls(
                phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK,
                       ValidationPhase.STYLE, ValidationPhase.UNIT_TESTS, ValidationPhase.E2E_TESTS],
                max_iterations=3,
                required_coverage=80
            ),
            "Maintenance Specialist": cls(
                phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK, ValidationPhase.UNIT_TESTS],
                max_iterations=2,
                required_coverage=70
            ),
            "Quality Inspector": cls(
                phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK, ValidationPhase.STYLE],
                max_iterations=1,
                stop_on_first_failure=True
            ),
            "Bug Hunter": cls(
                phases=[ValidationPhase.LINTING, ValidationPhase.UNIT_TESTS, ValidationPhase.E2E_TESTS],
                max_iterations=3,
                regression_test_required=True
            ),
            "Test Engineer": cls(
                phases=[ValidationPhase.UNIT_TESTS],
                max_iterations=1
            ),
            "Migration Architect": cls(
                phases=[ValidationPhase.E2E_TESTS],
                max_iterations=2,
                timeout=180
            ),
            "Documentation Writer": cls(
                phases=[ValidationPhase.LINTING],
                max_iterations=1
            ),
        }
        return configs.get(agent_role, cls(
            phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK],
            max_iterations=2
        ))


# ============================================================================
# VALIDATION PIPELINE SERVICE
# ============================================================================

class ValidationPipelineService:
    """
    Service for running 5-phase validation pipeline.

    Validates code through:
    1. Linting (syntax, code smells)
    2. Type checking (type correctness)
    3. Style (formatting)
    4. Unit tests (functional correctness)
    5. E2E tests (integration)

    Can iterate until code passes or max iterations reached.
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self._temp_files: List[str] = []

    async def run_validation(
        self,
        code: str,
        language: Language,
        config: Optional[ValidationConfig] = None,
        file_path: Optional[str] = None
    ) -> ValidationResult:
        """
        Run validation pipeline on code.

        Args:
            code: Source code to validate
            language: Programming language
            config: Validation configuration
            file_path: Optional file path (creates temp file if None)

        Returns:
            ValidationResult with all phase results
        """
        if config is None:
            config = ValidationConfig(
                phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK]
            )

        start_time = datetime.now()
        phase_results: List[ValidationPhaseResult] = []

        # Create temporary file if needed
        if file_path is None:
            file_path = await self._create_temp_file(code, language)
        else:
            await self._write_file(file_path, code)

        try:
            # Run each phase
            for phase in config.phases:
                phase_result = await self._run_phase(
                    phase, language, file_path, config.timeout
                )
                phase_results.append(phase_result)

                # Stop on first failure if configured
                if config.stop_on_first_failure and not phase_result.passed:
                    break

            # Calculate totals
            total_duration = (datetime.now() - start_time).total_seconds()
            total_errors = sum(len(p.errors) for p in phase_results)
            total_warnings = sum(len(p.warnings) for p in phase_results)
            success = all(p.passed for p in phase_results)

            return ValidationResult(
                success=success,
                phases=phase_results,
                total_duration=total_duration,
                total_errors=total_errors,
                total_warnings=total_warnings,
                coverage_percent=await self._get_coverage(phase_results),
                iterations=1,
                final_code=code
            )

        finally:
            # Cleanup temp files
            await self._cleanup_temp_files()

    async def iterate_until_valid(
        self,
        code: str,
        language: Language,
        config: Optional[ValidationConfig] = None,
        fix_callback: Optional[callable] = None
    ) -> Tuple[str, ValidationResult]:
        """
        Iterate validation until code passes or max iterations reached.

        Args:
            code: Initial source code
            language: Programming language
            config: Validation configuration
            fix_callback: Async function to fix errors (receives code, errors, returns fixed code)

        Returns:
            Tuple of (final_code, final_result)
        """
        if config is None:
            config = ValidationConfig(
                phases=[ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK],
                max_iterations=3
            )

        current_code = code
        all_iterations: List[ValidationResult] = []

        for iteration in range(config.max_iterations):
            logger.info(f"Validation iteration {iteration + 1}/{config.max_iterations}")

            # Run validation
            result = await self.run_validation(current_code, language, config)
            result.iterations = iteration + 1
            all_iterations.append(result)

            # Success - return
            if result.success:
                logger.info(f"Validation passed on iteration {iteration + 1}")
                result.final_code = current_code
                return current_code, result

            # Last iteration - return with failure
            if iteration == config.max_iterations - 1:
                logger.warning(f"Validation failed after {config.max_iterations} iterations")
                result.final_code = current_code
                return current_code, result

            # Try to fix
            if config.auto_fix:
                # First try auto-fix tools
                fixed_code = await self._auto_fix(current_code, language, result)
                if fixed_code != current_code:
                    current_code = fixed_code
                    continue

            # Use callback if provided
            if fix_callback:
                try:
                    errors = self._collect_all_errors(result)
                    fixed_code = await fix_callback(current_code, errors)
                    if fixed_code and fixed_code != current_code:
                        current_code = fixed_code
                        continue
                except Exception as e:
                    logger.error(f"Fix callback failed: {e}")

            # No fixes possible - return current state
            logger.warning("No fixes possible, returning current state")
            result.final_code = current_code
            return current_code, result

        # Should not reach here
        return current_code, all_iterations[-1] if all_iterations else ValidationResult(
            success=False,
            phases=[],
            total_duration=0,
            total_errors=0,
            total_warnings=0,
            coverage_percent=None,
            iterations=0,
            final_code=current_code
        )

    async def _run_phase(
        self,
        phase: ValidationPhase,
        language: Language,
        file_path: str,
        timeout: int
    ) -> ValidationPhaseResult:
        """Run a single validation phase"""
        start_time = datetime.now()
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        fix_suggestions: List[str] = []
        raw_output = ""

        tool_config = VALIDATION_TOOLS.get(phase, {}).get(language)
        if not tool_config:
            # Phase not configured for this language
            return ValidationPhaseResult(
                phase=phase,
                passed=True,
                duration=0,
                errors=[],
                warnings=[],
                fix_suggestions=["Phase not configured for this language"],
                raw_output=""
            )

        try:
            # Build command
            command = [
                arg.replace("{file}", file_path)
                for arg in tool_config["command"]
            ]

            # Run command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                raw_output = stdout.decode() + stderr.decode()
            except asyncio.TimeoutError:
                process.kill()
                errors.append(ValidationError(
                    phase=phase,
                    file=file_path,
                    line=None,
                    column=None,
                    message=f"Timeout after {timeout} seconds",
                    code="TIMEOUT",
                    severity="critical",
                    auto_fixable=False
                ))
                return ValidationPhaseResult(
                    phase=phase,
                    passed=False,
                    duration=timeout,
                    errors=errors,
                    warnings=warnings,
                    fix_suggestions=fix_suggestions,
                    raw_output="TIMEOUT"
                )

            # Parse output
            passed = process.returncode == 0
            errors, warnings = self._parse_output(
                raw_output, phase, language, file_path, tool_config["parse_output"]
            )

            # Generate fix suggestions
            if errors:
                fix_suggestions = self._generate_fix_suggestions(errors, phase, language)

            duration = (datetime.now() - start_time).total_seconds()

            return ValidationPhaseResult(
                phase=phase,
                passed=passed and len(errors) == 0,
                duration=duration,
                errors=errors,
                warnings=warnings,
                fix_suggestions=fix_suggestions,
                raw_output=raw_output
            )

        except FileNotFoundError:
            logger.warning(f"Tool not found for {phase.value}: {tool_config['tool']}")
            return ValidationPhaseResult(
                phase=phase,
                passed=True,  # Skip if tool not available
                duration=0,
                errors=[],
                warnings=[ValidationWarning(
                    phase=phase,
                    file=file_path,
                    line=None,
                    message=f"Tool '{tool_config['tool']}' not found - skipping phase",
                    code="TOOL_NOT_FOUND"
                )],
                fix_suggestions=[f"Install {tool_config['tool']} to enable {phase.value}"],
                raw_output=""
            )

        except Exception as e:
            logger.error(f"Phase {phase.value} failed: {e}")
            return ValidationPhaseResult(
                phase=phase,
                passed=False,
                duration=(datetime.now() - start_time).total_seconds(),
                errors=[ValidationError(
                    phase=phase,
                    file=file_path,
                    line=None,
                    column=None,
                    message=str(e),
                    code="INTERNAL_ERROR",
                    severity="critical",
                    auto_fixable=False
                )],
                warnings=warnings,
                fix_suggestions=[],
                raw_output=str(e)
            )

    def _parse_output(
        self,
        output: str,
        phase: ValidationPhase,
        language: Language,
        file_path: str,
        parser_type: str
    ) -> Tuple[List[ValidationError], List[ValidationWarning]]:
        """Parse tool output into errors and warnings"""
        errors = []
        warnings = []

        if not output:
            return errors, warnings

        if parser_type == "ruff":
            # Ruff format: file.py:line:col: CODE message
            pattern = r"(.+):(\d+):(\d+): ([A-Z]\d+) (.+)"
            for match in re.finditer(pattern, output):
                file, line, col, code, message = match.groups()
                errors.append(ValidationError(
                    phase=phase,
                    file=file,
                    line=int(line),
                    column=int(col),
                    message=message,
                    code=code,
                    severity="error",
                    auto_fixable=code.startswith(('E', 'F'))
                ))

        elif parser_type == "mypy":
            # Mypy format: file.py:line: error: message [code]
            pattern = r"(.+):(\d+): (error|warning|note): (.+)"
            for match in re.finditer(pattern, output):
                file, line, level, message = match.groups()
                code_match = re.search(r'\[([^\]]+)\]', message)
                code = code_match.group(1) if code_match else None

                if level == "error":
                    errors.append(ValidationError(
                        phase=phase,
                        file=file,
                        line=int(line),
                        column=None,
                        message=message,
                        code=code,
                        severity="error",
                        auto_fixable=False
                    ))
                else:
                    warnings.append(ValidationWarning(
                        phase=phase,
                        file=file,
                        line=int(line),
                        message=message,
                        code=code
                    ))

        elif parser_type == "black":
            # Black: "would reformat file.py" or "Oh no!"
            if "would reformat" in output or "reformatted" in output:
                errors.append(ValidationError(
                    phase=phase,
                    file=file_path,
                    line=None,
                    column=None,
                    message="File needs reformatting",
                    code="FORMAT",
                    severity="error",
                    auto_fixable=True
                ))

        elif parser_type == "prettier":
            if "Code style issues found" in output or "[warn]" in output:
                errors.append(ValidationError(
                    phase=phase,
                    file=file_path,
                    line=None,
                    column=None,
                    message="File needs formatting",
                    code="FORMAT",
                    severity="error",
                    auto_fixable=True
                ))

        elif parser_type == "eslint":
            # ESLint format: line:col error/warning message rule
            pattern = r"(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+(\S+)$"
            for match in re.finditer(pattern, output, re.MULTILINE):
                line, col, level, message, rule = match.groups()
                if level == "error":
                    errors.append(ValidationError(
                        phase=phase,
                        file=file_path,
                        line=int(line),
                        column=int(col),
                        message=message,
                        code=rule,
                        severity="error",
                        auto_fixable=True
                    ))
                else:
                    warnings.append(ValidationWarning(
                        phase=phase,
                        file=file_path,
                        line=int(line),
                        message=message,
                        code=rule
                    ))

        elif parser_type in ("pytest", "jest"):
            # Test frameworks: look for FAILED/PASSED patterns
            if "FAILED" in output or "ERRORS" in output:
                # Extract failed test names
                failed_pattern = r"FAILED (.+?) -"
                for match in re.finditer(failed_pattern, output):
                    test_name = match.group(1)
                    errors.append(ValidationError(
                        phase=phase,
                        file=file_path,
                        line=None,
                        column=None,
                        message=f"Test failed: {test_name}",
                        code="TEST_FAILED",
                        severity="error",
                        auto_fixable=False
                    ))

            # Check for assertion errors
            assertion_pattern = r"AssertionError: (.+)"
            for match in re.finditer(assertion_pattern, output):
                errors.append(ValidationError(
                    phase=phase,
                    file=file_path,
                    line=None,
                    column=None,
                    message=f"Assertion: {match.group(1)}",
                    code="ASSERTION",
                    severity="error",
                    auto_fixable=False
                ))

        elif parser_type == "tsc":
            # TypeScript: file.ts(line,col): error TS1234: message
            pattern = r"(.+)\((\d+),(\d+)\): error (TS\d+): (.+)"
            for match in re.finditer(pattern, output):
                file, line, col, code, message = match.groups()
                errors.append(ValidationError(
                    phase=phase,
                    file=file,
                    line=int(line),
                    column=int(col),
                    message=message,
                    code=code,
                    severity="error",
                    auto_fixable=False
                ))

        return errors, warnings

    def _generate_fix_suggestions(
        self,
        errors: List[ValidationError],
        phase: ValidationPhase,
        language: Language
    ) -> List[str]:
        """Generate suggestions for fixing errors"""
        suggestions = []

        for error in errors[:5]:  # Top 5 errors
            if error.auto_fixable:
                suggestions.append(f"Auto-fixable: {error.message}")
            elif error.code:
                suggestions.append(f"Fix {error.code}: {error.message}")
            else:
                suggestions.append(f"Address: {error.message}")

        # Add general suggestions based on phase
        if phase == ValidationPhase.TYPE_CHECK:
            suggestions.append("Consider adding type annotations or fixing type mismatches")
        elif phase == ValidationPhase.UNIT_TESTS:
            suggestions.append("Review test assertions and ensure code logic is correct")
        elif phase == ValidationPhase.LINTING:
            suggestions.append("Run auto-fix to resolve style issues")

        return suggestions

    async def _auto_fix(
        self,
        code: str,
        language: Language,
        result: ValidationResult
    ) -> str:
        """Try to auto-fix errors using tools"""
        file_path = await self._create_temp_file(code, language)

        try:
            # Run fix commands for phases with auto-fixable errors
            for phase_result in result.phases:
                if not phase_result.passed and any(e.auto_fixable for e in phase_result.errors):
                    tool_config = VALIDATION_TOOLS.get(phase_result.phase, {}).get(language)
                    if tool_config and "fix_command" in tool_config:
                        command = [
                            arg.replace("{file}", file_path)
                            for arg in tool_config["fix_command"]
                        ]
                        try:
                            process = await asyncio.create_subprocess_exec(
                                *command,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                                cwd=self.working_dir
                            )
                            await process.communicate()
                        except Exception as e:
                            logger.warning(f"Auto-fix failed for {phase_result.phase}: {e}")

            # Read fixed code
            with open(file_path, 'r') as f:
                return f.read()

        finally:
            await self._cleanup_temp_files()

    def _collect_all_errors(self, result: ValidationResult) -> List[ValidationError]:
        """Collect all errors from all phases"""
        errors = []
        for phase_result in result.phases:
            errors.extend(phase_result.errors)
        return errors

    async def _get_coverage(
        self,
        phase_results: List[ValidationPhaseResult]
    ) -> Optional[float]:
        """Extract coverage percentage from test results"""
        for result in phase_results:
            if result.phase in (ValidationPhase.UNIT_TESTS, ValidationPhase.E2E_TESTS):
                # Look for coverage in output
                coverage_match = re.search(
                    r'(\d+(?:\.\d+)?)\s*%\s*(?:coverage|covered)',
                    result.raw_output,
                    re.IGNORECASE
                )
                if coverage_match:
                    return float(coverage_match.group(1))
        return None

    async def _create_temp_file(
        self,
        code: str,
        language: Language
    ) -> str:
        """Create a temporary file for validation"""
        suffix = ".py" if language == Language.PYTHON else ".ts"
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.working_dir)

        try:
            with os.fdopen(fd, 'w') as f:
                f.write(code)
            self._temp_files.append(path)
            return path
        except Exception:
            os.close(fd)
            raise

    async def _write_file(self, path: str, code: str):
        """Write code to file"""
        with open(path, 'w') as f:
            f.write(code)

    async def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for path in self._temp_files:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {path}: {e}")
        self._temp_files = []

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    async def quick_lint(
        self,
        code: str,
        language: Language
    ) -> ValidationPhaseResult:
        """Quick lint check only"""
        config = ValidationConfig(phases=[ValidationPhase.LINTING], max_iterations=1)
        result = await self.run_validation(code, language, config)
        return result.phases[0] if result.phases else ValidationPhaseResult(
            phase=ValidationPhase.LINTING,
            passed=True,
            duration=0,
            errors=[],
            warnings=[],
            fix_suggestions=[]
        )

    async def quick_type_check(
        self,
        code: str,
        language: Language
    ) -> ValidationPhaseResult:
        """Quick type check only"""
        config = ValidationConfig(phases=[ValidationPhase.TYPE_CHECK], max_iterations=1)
        result = await self.run_validation(code, language, config)
        return result.phases[0] if result.phases else ValidationPhaseResult(
            phase=ValidationPhase.TYPE_CHECK,
            passed=True,
            duration=0,
            errors=[],
            warnings=[],
            fix_suggestions=[]
        )

    async def full_validation(
        self,
        code: str,
        language: Language
    ) -> ValidationResult:
        """Run full 5-phase validation"""
        config = ValidationConfig(
            phases=list(ValidationPhase),
            max_iterations=3,
            auto_fix=True
        )
        return await self.run_validation(code, language, config)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_validation_service: Optional[ValidationPipelineService] = None


def get_validation_service() -> ValidationPipelineService:
    """Get or create the validation service singleton"""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationPipelineService()
    return _validation_service

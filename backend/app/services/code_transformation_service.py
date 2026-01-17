"""
Code Transformation Service

Combines lightweight regex rewrites with sqlines/ora2pg integrations to
perform VB.NET→C#, VB.NET→Python, and T-SQL→PL/pgSQL conversions.
Tracks diffs/statistics, exposes async APIs, and keeps backups for rollback.
"""

from __future__ import annotations

import asyncio
import difflib
import logging
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, Iterable, List, Optional, Pattern, Tuple, Union

from app.services.ora2pg_wrapper_service import Ora2PgWrapperService
from app.services.sqlines_wrapper_service import (
    DatabasePlatform,
    SQLinesWrapperService,
)

logger = logging.getLogger(__name__)

Replacement = Union[str, Callable[[re.Match], str]]


class TransformationDirection(str, Enum):
    VBNET_TO_CSHARP = "vbnet_to_csharp"
    VBNET_TO_PYTHON = "vbnet_to_python"
    TSQL_TO_PLPGSQL = "tsql_to_plpgsql"


@dataclass
class TransformationRule:
    name: str
    pattern: str
    replacement: Replacement
    description: str
    directions: List[TransformationDirection]
    category: str = "general"
    flags: int = re.MULTILINE
    priority: int = 100
    compiled: Pattern[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.compiled = re.compile(self.pattern, self.flags)


@dataclass
class TransformationRequest:
    source_path: str
    direction: TransformationDirection
    target_path: Optional[str] = None
    encoding: str = "utf-8"
    dry_run: bool = False
    include_cli_tools: bool = True
    generate_backup: bool = True
    custom_rules: Optional[List[TransformationRule]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformationResult:
    success: bool
    source_path: str
    target_path: str
    direction: TransformationDirection
    lines_changed: int
    patterns_applied: Dict[str, int]
    diff: str
    errors: List[str]
    warnings: List[str]
    backup_path: Optional[str] = None
    cli_used: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformationStatistics:
    files_processed: int = 0
    lines_changed: int = 0
    rules_applied: int = 0
    cli_invocations: int = 0
    rollbacks: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_processed": self.files_processed,
            "lines_changed": self.lines_changed,
            "rules_applied": self.rules_applied,
            "cli_invocations": self.cli_invocations,
            "rollbacks": self.rollbacks,
            "uptime_seconds": int((datetime.now(timezone.utc) - self.start_time).total_seconds()),
        }


VB_TO_CSHARP_TYPES = {"integer": "int", "long": "long", "double": "double", "decimal": "decimal", "boolean": "bool", "string": "string", "datetime": "DateTime"}
VB_TO_PY_TYPES = {"integer": "int", "long": "int", "double": "float", "decimal": "float", "boolean": "bool", "string": "str", "datetime": "datetime.datetime"}
SQL_TYPE_MAP = {"nvarchar": "text", "varchar": "text", "bit": "boolean", "datetime": "timestamp", "smalldatetime": "timestamp", "money": "numeric", "uniqueidentifier": "uuid"}


class CodeTransformationService:
    """Async transformer with diffing, stats, CLI hooks, and rollback support."""

    def __init__(self) -> None:
        self.sqlines = SQLinesWrapperService()
        self.ora2pg = Ora2PgWrapperService()
        self.rules = self._build_rule_registry()
        self.stats = TransformationStatistics()
        self.backup_root = Path(".mtm_transform_backups")
        self.backup_root.mkdir(exist_ok=True)
        self._rollback_registry: Dict[str, List[Path]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def _build_rule_registry(self) -> Dict[TransformationDirection, List[TransformationRule]]:
        registry: Dict[TransformationDirection, List[TransformationRule]] = defaultdict(list)

        def add(rule: TransformationRule) -> None:
            for direction in rule.directions:
                registry[direction].append(rule)

        def vb_dim_cs(match: re.Match) -> str:
            name = match.group("name")
            vb_type = match.group("type").lower()
            value = match.group("value")
            cs_type = VB_TO_CSHARP_TYPES.get(vb_type, "var")
            suffix = f" = {value.strip()}" if value else ""
            return f"{cs_type} {name}{suffix};"

        def vb_dim_py(match: re.Match) -> str:
            name = match.group("name").lower()
            vb_type = match.group("type").lower()
            value = match.group("value")
            py_type = VB_TO_PY_TYPES.get(vb_type, "typing.Any")
            if value:
                return f"{name}: {py_type} = {value.strip()}"
            return f"{name}: {py_type} = None"

        def vb_method_cs(match: re.Match) -> str:
            visibility = match.group("visibility").lower()
            member = match.group("member").lower()
            name = match.group("name")
            params = match.group("params") or ""
            rettype = match.group("rettype")
            cs_visibility = {
                "public": "public",
                "private": "private",
                "protected": "protected",
                "friend": "internal",
            }.get(visibility, "public")
            cs_return = "void"
            if member == "function" and rettype:
                cs_return = VB_TO_CSHARP_TYPES.get(rettype.lower(), rettype)
            return f"{cs_visibility} {cs_return} {name}({self._params_to_csharp(params)})\n{{"

        def vb_method_py(match: re.Match) -> str:
            name = match.group("name").lower()
            member = match.group("member").lower()
            params = self._params_to_python(match.group("params") or "")
            suffix = ""
            if member == "function" and match.group("rettype"):
                suffix = f" -> {VB_TO_PY_TYPES.get(match.group('rettype').lower(), 'typing.Any')}"
            method_name = "__init__" if name == "new" else name
            return f"def {method_name}(self{params}){suffix}:"

        def vb_if_cs(match: re.Match) -> str:
            condition = (
                match.group("condition")
                .replace("AndAlso", "&&")
                .replace("OrElse", "||")
                .replace("Not ", "!")
            )
            return f"if ({condition.strip()})\n{{"

        def vb_if_py(match: re.Match) -> str:
            clause = match.group("clause").lower()
            condition = (
                match.group("condition")
                .replace("AndAlso", "and")
                .replace("OrElse", "or")
                .replace("Not ", "not ")
            )
            keyword = "elif" if clause == "elseif" else clause
            return f"{keyword} {condition.strip()}:"

        def tsql_proc(match: re.Match) -> str:
            name = match.group("name").lower()
            params = self._convert_tsql_params(match.group("params") or "")
            body = match.group("body").strip()
            body = body.replace("PRINT", "RAISE NOTICE")
            return (
                f"CREATE OR REPLACE FUNCTION {name}({params})\n"
                "RETURNS void AS $$\nBEGIN\n"
                f"{body}\nEND;\n$$ LANGUAGE plpgsql;"
            )

        cs_data = [
            ("vb_imports", r"^\s*Imports\s+(?P<ns>[\w\.]+)", lambda m: f"using {m.group('ns')};", "Imports"),
            ("vb_class", r"^\s*(Public|Private|Friend)\s+Class\s+(?P<name>\w+)", lambda m: f"public class {m.group('name')}\n{{", "Class decl"),
            ("vb_end", r"^\s*End\s+(Class|Sub|Function|If)", "}", "Close blocks"),
            (
                "vb_method",
                r"^\s*(?P<visibility>Public|Private|Protected|Friend)\s+(?P<member>Sub|Function)\s+(?P<name>\w+)\((?P<params>[^)]*)\)(?:\s+As\s+(?P<rettype>\w+))?",
                vb_method_cs,
                "Method signature",
            ),
            ("vb_dim", r"\bDim\s+(?P<name>\w+)\s+As\s+(?P<type>\w+)(?:\s*=\s*(?P<value>.+))?", vb_dim_cs, "Variable"),
            ("vb_if", r"^\s*If\s+(?P<condition>.+?)\s+Then", vb_if_cs, "If statement"),
            ("vb_else_if", r"^\s*ElseIf\s+(?P<condition>.+?)\s+Then", lambda m: f"else if ({m.group('condition').strip()})\n{{", "ElseIf"),
            ("vb_else", r"^\s*Else\s*$", "else\n{", "Else"),
            ("vb_literals", r"\b(True|False|Nothing)\b", lambda m: {"True": "true", "False": "false", "Nothing": "null"}[m.group(1)], "Literals"),
        ]

        py_data = [
            ("vb_imports_py", r"^\s*Imports\s+(?P<ns>[\w\.]+)", lambda m: f"import {m.group('ns').lower()}", "Imports"),
            ("vb_class_py", r"^\s*(Public|Private|Friend)\s+Class\s+(?P<name>\w+)", lambda m: f"class {m.group('name')}:\n    pass", "Class"),
            (
                "vb_method_py",
                r"^\s*(Public|Private|Protected|Friend)\s+(?P<member>Sub|Function)\s+(?P<name>\w+)\((?P<params>[^)]*)\)(?:\s+As\s+(?P<rettype>\w+))?",
                vb_method_py,
                "Method",
            ),
            ("vb_dim_py", r"\bDim\s+(?P<name>\w+)\s+As\s+(?P<type>\w+)(?:\s*=\s*(?P<value>.+))?", vb_dim_py, "Variable"),
            ("vb_if_py", r"^\s*(?P<clause>If|ElseIf|Else)\s+(?P<condition>.+?)(?:\s+Then)?$", vb_if_py, "If"),
            ("vb_console_py", r"Console\.WriteLine\((?P<value>.+?)\)", lambda m: f"print({m.group('value')})", "Console"),
            ("vb_end_py", r"^\s*End\s+(Class|Sub|Function|If)", "", "Remove End"),
            ("vb_literals_py", r"\b(True|False|Nothing)\b", lambda m: {"True": "True", "False": "False", "Nothing": "None"}[m.group(1)], "Literals"),
        ]

        tsql_data = [
            ("tsql_brackets", r"\[(?P<name>[^\]]+)\]", lambda m: f'"{m.group("name").lower()}"', "Identifiers"),
            ("tsql_go", r"^\s*GO\s*$", "", "Batch", re.MULTILINE),
            ("tsql_getdate", r"\bGETDATE\s*\(\s*\)", "CURRENT_TIMESTAMP", "Datetime"),
            ("tsql_isnull", r"\bISNULL\s*\(", "COALESCE(", "Null handling"),
            ("tsql_len", r"\bLEN\s*\(", "LENGTH(", "Length"),
            ("tsql_identity", r"\bINT\s+IDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)", "SERIAL", "Identity"),
            ("tsql_types", r"\b(?P<type>nvarchar|varchar|bit|datetime|smalldatetime|money|uniqueidentifier)\b", lambda m: SQL_TYPE_MAP.get(m.group("type").lower(), m.group("type")), "Types", re.IGNORECASE),
            ("tsql_vars", r"@(?P<name>\w+)", lambda m: m.group("name").lower(), "Variables"),
            ("tsql_print", r"\bPRINT\s+(?P<message>.+)", lambda m: f'RAISE NOTICE {m.group("message")};', "Print"),
            (
                "tsql_proc",
                r"CREATE\s+PROCEDURE\s+(?P<name>\w+)\s*(?P<params>\([^\)]*\)|.*?)\s+AS\s+BEGIN(?P<body>[\s\S]+?)END",
                tsql_proc,
                "Procedure",
                re.IGNORECASE | re.DOTALL,
            ),
        ]

        for name, pattern, repl, desc, *extra in cs_data:
            add(
                TransformationRule(
                    name=name,
                    pattern=pattern,
                    replacement=repl,
                    description=desc,
                    directions=[TransformationDirection.VBNET_TO_CSHARP],
                )
            )

        for name, pattern, repl, desc, *extra in py_data:
            add(
                TransformationRule(
                    name=name,
                    pattern=pattern,
                    replacement=repl,
                    description=desc,
                    directions=[TransformationDirection.VBNET_TO_PYTHON],
                )
            )

        for name, pattern, repl, desc, *maybe_flag in tsql_data:
            flags = maybe_flag[0] if maybe_flag else re.MULTILINE
            add(
                TransformationRule(
                    name=name,
                    pattern=pattern,
                    replacement=repl,
                    description=desc,
                    directions=[TransformationDirection.TSQL_TO_PLPGSQL],
                    flags=flags,
                )
            )

        return registry

    def _parse_vb_params(self, params: str) -> List[Tuple[str, str]]:
        result = []
        for chunk in params.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            match = re.match(r"(?:ByVal|ByRef)?\s*(?P<name>\w+)\s+As\s+(?P<type>[\w\.]+)", chunk, re.IGNORECASE)
            if match:
                result.append((match.group("name"), match.group("type")))
        return result

    def _params_to_csharp(self, params: str) -> str:
        return ", ".join(
            f"{VB_TO_CSHARP_TYPES.get(vtype.lower(), vtype)} {name}"
            for name, vtype in self._parse_vb_params(params)
        )

    def _params_to_python(self, params: str) -> str:
        return "".join(
            f", {name.lower()}: {VB_TO_PY_TYPES.get(vtype.lower(), 'typing.Any')}"
            for name, vtype in self._parse_vb_params(params)
        )

    def _convert_tsql_params(self, params: str) -> str:
        params = params.strip().strip("()")
        if not params:
            return ""
        converted = []
        for chunk in params.split(","):
            chunk = chunk.strip()
            match = re.match(r"@(?P<name>\w+)\s+(?P<type>\w+)(?:\s*=\s*(?P<default>[\w']+))?", chunk, re.IGNORECASE)
            if not match:
                converted.append(chunk)
                continue
            name = match.group("name").lower()
            sql_type = match.group("type").lower()
            mapped = SQL_TYPE_MAP.get(sql_type, sql_type)
            default = match.group("default")
            if default:
                converted.append(f"{name} {mapped} DEFAULT {default}")
            else:
                converted.append(f"{name} {mapped}")
        return ", ".join(converted)

    async def apply_rule(self, rule: TransformationRule, text: str) -> Tuple[str, int]:
        def _apply() -> Tuple[str, int]:
            return rule.compiled.subn(rule.replacement, text)

        return await asyncio.to_thread(_apply)

    def _select_rules(self, direction: TransformationDirection, custom: Optional[List[TransformationRule]]) -> List[TransformationRule]:
        return custom if custom else self.rules.get(direction, [])

    def _generate_diff(self, before: str, after: str, src: Path, dst: Path) -> str:
        diff = difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile=str(src), tofile=str(dst), lineterm="")
        diff_lines = list(diff)
        if len(diff_lines) > 400:
            diff_lines = diff_lines[:400] + ["... diff trimmed ..."]
        return "\n".join(diff_lines)

    def _lines_changed(self, diff_text: str) -> int:
        return sum(1 for line in diff_text.splitlines() if line.startswith(("+", "-")))

    async def _run_sqlines_cli(self, content: str) -> Optional[str]:
        if not self.sqlines.sqlines_path:
            return None

        def _execute() -> Optional[str]:
            with TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                input_path = tmp_path / "input.sql"
                output_path = tmp_path / "output.sql"
                input_path.write_text(content, encoding="utf-8")
                cmd = [
                    self.sqlines.sqlines_path,
                    "-s=sqlserver",
                    "-t=postgresql",
                    f"-in={input_path}",
                    f"-out={output_path}",
                ]
                try:
                    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
                except Exception as exc:
                    logger.warning("SQLines CLI failed: %s", exc)
                    return None
                return output_path.read_text(encoding="utf-8") if output_path.exists() else None

        output = await asyncio.to_thread(_execute)
        if output:
            self.stats.cli_invocations += 1
        return output

    async def _collect_sqlines_report(self, file_path: Path) -> Optional[Dict[str, Any]]:
        if not file_path.exists():
            return None

        def _analyze() -> Any:
            return self.sqlines.analyze_directory(
                directory=str(file_path.parent),
                source_platform=DatabasePlatform.SQL_SERVER,
                target_platforms=[DatabasePlatform.POSTGRESQL],
                file_extensions=[file_path.suffix or ".sql"],
            )

        try:
            result = await asyncio.to_thread(_analyze)
            return result.to_dict()
        except Exception as exc:
            logger.debug("SQLines analysis skipped: %s", exc)
            return None

    async def _collect_ora2pg_report(self, file_path: Path) -> Optional[Dict[str, Any]]:
        if not file_path.exists():
            return None
        try:
            result = await self.ora2pg.analyze_files([file_path])
            return self.ora2pg.to_dict(result)
        except Exception as exc:
            logger.debug("Ora2Pg analysis skipped: %s", exc)
            return None

    async def _read_file(self, path: Path, encoding: str) -> str:
        return await asyncio.to_thread(path.read_text, encoding, "ignore")

    async def _write_file(self, path: Path, content: str, encoding: str) -> None:
        await asyncio.to_thread(path.write_text, content, encoding)

    def _backup(self, path: Path) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / path.name
        shutil.copy2(path, backup_path)
        self._rollback_registry[str(path)].append(backup_path)
        return backup_path

    async def transform_file(self, request: TransformationRequest) -> TransformationResult:
        start = datetime.now(timezone.utc)
        source = Path(request.source_path)
        target = Path(request.target_path) if request.target_path else source
        errors: List[str] = []
        warnings: List[str] = []
        metadata: Dict[str, Any] = {}
        cli_used: Optional[str] = None

        if not source.exists():
            msg = f"Source file {source} does not exist"
            return TransformationResult(
                success=False,
                source_path=str(source),
                target_path=str(target),
                direction=request.direction,
                lines_changed=0,
                patterns_applied={},
                diff="",
                errors=[msg],
                warnings=[],
            )

        original = await self._read_file(source, request.encoding)
        transformed = original

        if request.direction == TransformationDirection.TSQL_TO_PLPGSQL and request.include_cli_tools:
            cli_output = await self._run_sqlines_cli(original)
            if cli_output:
                transformed = cli_output
                cli_used = "sqlines"
            elif self.sqlines.sqlines_path:
                warnings.append("SQLines CLI available but returned no output")

        applied: Dict[str, int] = {}
        for rule in self._select_rules(request.direction, request.custom_rules):
            transformed, count = await self.apply_rule(rule, transformed)
            if count:
                applied[rule.name] = applied.get(rule.name, 0) + count

        if transformed == original:
            duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            return TransformationResult(
                success=True,
                source_path=str(source),
                target_path=str(target),
                direction=request.direction,
                lines_changed=0,
                patterns_applied=applied,
                diff="",
                errors=[],
                warnings=["No changes applied"],
                duration_ms=duration,
            )

        diff_text = self._generate_diff(original, transformed, source, target)
        lines_changed = self._lines_changed(diff_text)

        backup_path = None
        if request.generate_backup and not request.dry_run and source.exists():
            backup_path = self._backup(source)

        if not request.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            await self._write_file(target, transformed, request.encoding)
        else:
            warnings.append("Dry run enabled; file not written")

        if request.direction == TransformationDirection.TSQL_TO_PLPGSQL:
            sqlines_report = await self._collect_sqlines_report(target)
            if sqlines_report:
                metadata["sqlines_report"] = sqlines_report
            ora2pg_report = await self._collect_ora2pg_report(target)
            if ora2pg_report:
                metadata["ora2pg_report"] = ora2pg_report

        self.stats.files_processed += 1
        self.stats.lines_changed += lines_changed
        self.stats.rules_applied += sum(applied.values())

        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return TransformationResult(
            success=True,
            source_path=str(source),
            target_path=str(target),
            direction=request.direction,
            lines_changed=lines_changed,
            patterns_applied=applied,
            diff=diff_text,
            errors=errors,
            warnings=warnings,
            backup_path=str(backup_path) if backup_path else None,
            cli_used=cli_used,
            duration_ms=duration,
            metadata=metadata,
        )

    async def batch_transform(self, requests: Iterable[TransformationRequest]) -> List[TransformationResult]:
        results: List[TransformationResult] = []
        for request in requests:
            results.append(await self.transform_file(request))
        return results

    async def transform_directory(
        self,
        directory: str,
        direction: TransformationDirection,
        glob: str = "**/*",
        include_cli_tools: bool = True,
        dry_run: bool = False,
    ) -> List[TransformationResult]:
        root = Path(directory)
        if not root.exists():
            logger.error("Directory %s does not exist", directory)
            return []

        extension_map = {
            TransformationDirection.VBNET_TO_CSHARP: (".vb", ".bas"),
            TransformationDirection.VBNET_TO_PYTHON: (".vb", ".bas"),
            TransformationDirection.TSQL_TO_PLPGSQL: (".sql", ".tsql"),
        }
        extensions = extension_map.get(direction, (".vb", ".sql"))

        requests = [
            TransformationRequest(
                source_path=str(path),
                direction=direction,
                include_cli_tools=include_cli_tools,
                dry_run=dry_run,
            )
            for path in root.glob(glob)
            if path.is_file() and path.suffix.lower() in extensions
        ]
        return await self.batch_transform(requests)

    async def rollback_file(self, target_path: str) -> bool:
        async with self._lock:
            backups = self._rollback_registry.get(target_path)
            if not backups:
                return False
            backup = backups.pop()
            try:
                await asyncio.to_thread(shutil.copy2, backup, target_path)
                self.stats.rollbacks += 1
                return True
            except Exception as exc:
                logger.error("Rollback failed for %s: %s", target_path, exc)
                return False

    async def rollback_directory(self, directory: str) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for path in list(self._rollback_registry.keys()):
            if path.startswith(directory):
                results[path] = await self.rollback_file(path)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats.to_dict()

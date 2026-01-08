"""
HCI-CRS Agenda Analysis - Compare Standalone vs Existing Components

Analyzes /opt/projecten/hci-crs/src/EPD/WEB/Agenda2/Default.aspx.vb
with both extraction approaches.

Usage:
    cd backend
    python -m tests.services.extraction.analyze_hci_agenda
"""
import asyncio
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
import re
import importlib.util

# ============================================================================
# CONFIGURATION
# ============================================================================

HCI_AGENDA_FILES = [
    "/opt/projecten/hci-crs/src/EPD/WEB/Agenda2/Default.aspx.vb",  # VB.NET
    "/opt/projecten/hci-crs/src/EPD/WEB/Afspraken/Agenda.asp",      # Classic ASP
]

# ============================================================================
# STANDALONE EXTRACTION (VB.NET adapted)
# ============================================================================

@dataclass
class CodeSymbol:
    name: str
    type: str  # class, method, property, enum
    line_start: int
    line_end: int
    docstring: str
    parent: str = ""

@dataclass
class BusinessRule:
    id: str
    condition: str
    action: str
    source_lines: tuple
    rule_type: str  # validation, authorization, calculation, workflow
    confidence: float
    natural_language: str

@dataclass
class NFR:
    id: str
    category: str
    description: str
    metric: str
    source_text: str

@dataclass
class StandaloneResult:
    source_file: str
    lines_of_code: int
    symbols: List[CodeSymbol]
    business_rules: List[BusinessRule]
    nfrs: List[NFR]


def parse_vbnet_structure(source: str) -> List[CodeSymbol]:
    """Parse VB.NET code structure."""
    symbols = []
    lines = source.split('\n')

    current_class = ""
    in_region = ""

    # Patterns for VB.NET
    class_pattern = re.compile(r'^\s*(Partial\s+)?(Class|Module)\s+(\w+)', re.IGNORECASE)
    sub_pattern = re.compile(r'^\s*(Protected|Private|Public|Friend)?\s*(Shared)?\s*Sub\s+(\w+)', re.IGNORECASE)
    function_pattern = re.compile(r'^\s*(Protected|Private|Public|Friend)?\s*(Shared)?\s*Function\s+(\w+)', re.IGNORECASE)
    property_pattern = re.compile(r'^\s*(Protected|Private|Public|Friend)?\s*(Shared)?\s*(ReadOnly|WriteOnly)?\s*Property\s+(\w+)', re.IGNORECASE)
    enum_pattern = re.compile(r'^\s*(Protected|Private|Public)?\s*Enum\s+(\w+)', re.IGNORECASE)
    region_pattern = re.compile(r'^\s*#Region\s+"([^"]+)"', re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        # Track regions
        region_match = region_pattern.match(line)
        if region_match:
            in_region = region_match.group(1)
        if '#End Region' in line:
            in_region = ""

        # Class/Module
        class_match = class_pattern.match(line)
        if class_match:
            current_class = class_match.group(3)
            symbols.append(CodeSymbol(
                name=current_class,
                type="class",
                line_start=i,
                line_end=i,
                docstring=in_region,
                parent=""
            ))

        # Sub
        sub_match = sub_pattern.match(line)
        if sub_match:
            symbols.append(CodeSymbol(
                name=sub_match.group(3),
                type="method",
                line_start=i,
                line_end=i,
                docstring=in_region,
                parent=current_class
            ))

        # Function
        func_match = function_pattern.match(line)
        if func_match:
            symbols.append(CodeSymbol(
                name=func_match.group(3),
                type="function",
                line_start=i,
                line_end=i,
                docstring=in_region,
                parent=current_class
            ))

        # Property
        prop_match = property_pattern.match(line)
        if prop_match:
            symbols.append(CodeSymbol(
                name=prop_match.group(4),
                type="property",
                line_start=i,
                line_end=i,
                docstring=in_region,
                parent=current_class
            ))

        # Enum
        enum_match = enum_pattern.match(line)
        if enum_match:
            symbols.append(CodeSymbol(
                name=enum_match.group(2),
                type="enum",
                line_start=i,
                line_end=i,
                docstring="",
                parent=current_class
            ))

    return symbols


def extract_vbnet_business_rules(source: str) -> List[BusinessRule]:
    """Extract business rules from VB.NET/VBScript code."""
    rules = []
    lines = source.split('\n')
    rule_id = 0

    # Patterns for VB.NET/VBScript business rules
    patterns = [
        # If-Then validation
        (r'If\s+(.+?)\s+Then', 'validation', 0.85),
        # Permission checks
        (r'(CanView|CanEdit|CanDelete|CanAdd|HasPermission|IsAllowed|intCanView|intCanEdit)', 'authorization', 0.9),
        # Date/time validations
        (r'(StartTime|EndTime|StartDate|EndDate|Duration|Interval|datStart|datEnd|DatumVanaf|DatumTot)', 'scheduling', 0.8),
        # Status checks
        (r'(Status|State)\s*(=|<>|Is)\s*', 'workflow', 0.85),
        # Select Case (business logic branching)
        (r'(Select\s+Case|Case\s+\d+|Case\s+Else)', 'branching', 0.9),
        # Numeric thresholds
        (r'(\w+)\s*(>=|<=|>|<|=)\s*(\d+)', 'threshold', 0.8),
        # Response.Redirect (workflow)
        (r'Response\.Redirect\s*\(', 'navigation', 0.75),
        # Error handling
        (r'(Throw|RaiseEvent|MsgBox|Alert|Err\.)', 'error_handling', 0.7),
        # Database operations
        (r'(rst\.|Execute|Connection|Recordset)', 'data_access', 0.8),
        # Session/Request handling
        (r'(Session\(|Request\(|Request\.Form)', 'state_management', 0.75),
    ]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("'"):
            continue

        for pattern, rule_type, confidence in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                rule_id += 1

                # Extract condition and action
                if 'If ' in line and ' Then' in line:
                    condition = re.search(r'If\s+(.+?)\s+Then', line, re.IGNORECASE)
                    condition_text = condition.group(1) if condition else match.group(0)

                    # Look for action on same line or next line
                    action = ""
                    if 'Then' in line:
                        after_then = line.split('Then', 1)
                        if len(after_then) > 1 and after_then[1].strip():
                            action = after_then[1].strip()
                        elif i < len(lines):
                            action = lines[i].strip()
                else:
                    condition_text = match.group(0)
                    action = stripped

                # Generate natural language
                nl = f"IF {condition_text} THEN {action[:50]}..."

                rules.append(BusinessRule(
                    id=f"BR-{rule_id:03d}",
                    condition=condition_text,
                    action=action[:100] if action else "continue",
                    source_lines=(i, i),
                    rule_type=rule_type,
                    confidence=confidence,
                    natural_language=nl
                ))
                break  # Only match first pattern per line

    return rules


def extract_vbnet_nfrs(source: str) -> List[NFR]:
    """Detect NFRs in VB.NET code."""
    nfrs = []
    nfr_id = 0

    # NFR indicators
    indicators = {
        'performance': [
            (r'Cache', 'Caching implemented for performance'),
            (r'Async|Await', 'Asynchronous processing for responsiveness'),
            (r'Thread|BackgroundWorker', 'Multi-threading for performance'),
        ],
        'security': [
            (r'CanView|CanEdit|Permission|Authorize', 'Access control implemented'),
            (r'Encrypt|Hash|Secure', 'Data security measures'),
            (r'Session|LoggedIn|Authenticate', 'Authentication required'),
        ],
        'usability': [
            (r'MsgBox|Alert|Message', 'User feedback mechanisms'),
            (r'Redirect|Navigate', 'User navigation handling'),
            (r'Validation|Required|Validate', 'Input validation for users'),
        ],
        'reliability': [
            (r'Try|Catch|Finally', 'Error handling for reliability'),
            (r'Log|Trace|Debug', 'Logging for diagnostics'),
            (r'Rollback|Transaction', 'Transaction handling'),
        ],
        'maintainability': [
            (r'#Region', 'Code organization with regions'),
            (r'Const|ReadOnly', 'Constants for maintainability'),
            (r'Enum', 'Enumerations for type safety'),
        ],
    }

    for category, patterns in indicators.items():
        for pattern, description in patterns:
            matches = re.findall(pattern, source, re.IGNORECASE)
            if matches:
                nfr_id += 1
                nfrs.append(NFR(
                    id=f"NFR-{nfr_id:03d}",
                    category=category,
                    description=description,
                    metric=f"{len(matches)} occurrences",
                    source_text=f"Pattern: {pattern}"
                ))

    return nfrs


def run_standalone_extraction(file_path: str) -> StandaloneResult:
    """Run standalone extraction on VB.NET file."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        source = f.read()

    lines_of_code = len(source.split('\n'))
    symbols = parse_vbnet_structure(source)
    rules = extract_vbnet_business_rules(source)
    nfrs = extract_vbnet_nfrs(source)

    return StandaloneResult(
        source_file=file_path,
        lines_of_code=lines_of_code,
        symbols=symbols,
        business_rules=rules,
        nfrs=nfrs
    )


# ============================================================================
# EXISTING COMPONENT EXTRACTION
# ============================================================================

def load_existing_components():
    """Load existing extraction components."""
    base_path = Path(__file__).parent.parent.parent.parent

    # Load BusinessRuleExtractor
    spec = importlib.util.spec_from_file_location(
        "business_rule_extractor",
        str(base_path / "app" / "services" / "static_analysis" / "business_rule_extractor.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["business_rule_extractor"] = module
    spec.loader.exec_module(module)

    return module.BusinessRuleExtractor


async def run_component_extraction(file_path: str) -> Dict[str, Any]:
    """Run extraction using existing components."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        source = f.read()

    BusinessRuleExtractor = load_existing_components()
    extractor = BusinessRuleExtractor()

    rules = await extractor.extract_from_file(file_path, source)

    return {
        "source_file": file_path,
        "lines_of_code": len(source.split('\n')),
        "business_rules": rules,
        "rules_by_type": {}
    }


# ============================================================================
# MAIN COMPARISON
# ============================================================================

async def analyze_file(file_path: str) -> Dict[str, Any]:
    """Analyze a single file with both extractors."""
    print("\n" + "=" * 80)
    print(f"ANALYZING: {Path(file_path).name}")
    print("=" * 80)

    if not Path(file_path).exists():
        print(f"ERROR: Bestand niet gevonden: {file_path}")
        return None

    # Standalone extraction
    standalone = run_standalone_extraction(file_path)

    print(f"\nLines of code: {standalone.lines_of_code}")
    print(f"Code symbols: {len(standalone.symbols)}")
    print(f"Business rules: {len(standalone.business_rules)}")
    print(f"NFRs: {len(standalone.nfrs)}")

    # Group symbols by type
    symbol_types = {}
    for s in standalone.symbols:
        symbol_types[s.type] = symbol_types.get(s.type, 0) + 1
    print(f"\nSymbols by type: {symbol_types}")

    # Group rules by type
    rule_types = {}
    for r in standalone.business_rules:
        rule_types[r.rule_type] = rule_types.get(r.rule_type, 0) + 1
    print(f"Business rules by type: {rule_types}")

    # Show sample rules by category
    print("\n--- AUTHORIZATION RULES ---")
    auth_rules = [r for r in standalone.business_rules if r.rule_type == 'authorization']
    for r in auth_rules[:5]:
        print(f"  Line {r.source_lines[0]}: {r.natural_language[:70]}...")

    print("\n--- WORKFLOW/STATUS RULES ---")
    workflow_rules = [r for r in standalone.business_rules if r.rule_type in ('workflow', 'branching')]
    for r in workflow_rules[:8]:
        print(f"  Line {r.source_lines[0]}: {r.natural_language[:70]}...")

    print("\n--- SCHEDULING RULES ---")
    sched_rules = [r for r in standalone.business_rules if r.rule_type == 'scheduling']
    for r in sched_rules[:5]:
        print(f"  Line {r.source_lines[0]}: {r.natural_language[:70]}...")

    print("\n--- DATA ACCESS RULES ---")
    data_rules = [r for r in standalone.business_rules if r.rule_type == 'data_access']
    for r in data_rules[:5]:
        print(f"  Line {r.source_lines[0]}: {r.natural_language[:70]}...")

    # Show NFRs
    print("\n--- NON-FUNCTIONAL REQUIREMENTS ---")
    for nfr in standalone.nfrs:
        print(f"  {nfr.id}: [{nfr.category}] {nfr.description} ({nfr.metric})")

    # Existing component extraction
    try:
        component_result = await run_component_extraction(file_path)
        comp_rules = len(component_result.get('business_rules', []))
    except Exception:
        comp_rules = 0

    return {
        'file': file_path,
        'standalone': standalone,
        'component_rules': comp_rules,
        'rule_types': rule_types,
    }


async def main():
    print("=" * 80)
    print("HCI-CRS AGENDA ANALYSIS - EXTRACTIE VERGELIJKING")
    print("=" * 80)

    results = []
    for file_path in HCI_AGENDA_FILES:
        result = await analyze_file(file_path)
        if result:
            results.append(result)

    # Final comparison
    print("\n" + "=" * 80)
    print("TOTAAL OVERZICHT - ALLE AGENDA BESTANDEN")
    print("=" * 80)

    print(f"\n{'Bestand':<50} {'LOC':>8} {'Symbols':>10} {'Rules':>10} {'NFRs':>8}")
    print("-" * 86)

    total_loc = 0
    total_symbols = 0
    total_rules = 0
    total_nfrs = 0
    all_rule_types = {}

    for r in results:
        standalone = r['standalone']
        filename = Path(r['file']).name
        print(f"{filename:<50} {standalone.lines_of_code:>8} {len(standalone.symbols):>10} {len(standalone.business_rules):>10} {len(standalone.nfrs):>8}")

        total_loc += standalone.lines_of_code
        total_symbols += len(standalone.symbols)
        total_rules += len(standalone.business_rules)
        total_nfrs += len(standalone.nfrs)

        for rt, count in r['rule_types'].items():
            all_rule_types[rt] = all_rule_types.get(rt, 0) + count

    print("-" * 86)
    print(f"{'TOTAAL':<50} {total_loc:>8} {total_symbols:>10} {total_rules:>10} {total_nfrs:>8}")

    print("\n--- BUSINESS RULES PER TYPE (ALLE BESTANDEN) ---")
    for rt, count in sorted(all_rule_types.items(), key=lambda x: -x[1]):
        print(f"  {rt:<20}: {count:>5}")

    print("\n" + "=" * 80)
    print("CONCLUSIE")
    print("=" * 80)
    print(f"""
De HCI-CRS Agenda module bevat:
- {total_loc} regels code over {len(results)} bestanden
- {total_symbols} code symbolen (classes, methods, properties)
- {total_rules} business rules gedetecteerd
- {total_nfrs} non-functional requirements

Belangrijkste rule types:
- validation: {all_rule_types.get('validation', 0)} regels (IF-THEN logica)
- branching: {all_rule_types.get('branching', 0)} regels (Select Case logica)
- authorization: {all_rule_types.get('authorization', 0)} regels (toegangscontrole)
- scheduling: {all_rule_types.get('scheduling', 0)} regels (datum/tijd logica)
- data_access: {all_rule_types.get('data_access', 0)} regels (database operaties)
""")


if __name__ == "__main__":
    asyncio.run(main())

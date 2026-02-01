#!/bin/bash
# micro-decompose.sh - PRD Micro-Deliverable Decomposition Engine
# Part of Fase 32E: Quality Harness
# Version 1.0
#
# Purpose: Break PRD requirements into the smallest possible testable units.
#          Each micro-deliverable has: ID, acceptance criteria, expected tests,
#          dependencies, and category.
#
# Usage:
#   source mq/workflows/common/micro-decompose.sh
#   decompose_prd <prd_file> <output_file> <context_dir>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Decompose PRD into micro-deliverables
# Arguments:
#   $1 - Path to PRD file
#   $2 - Output path for micro-deliverables.json
#   $3 - Context directory (project root)
# Returns:
#   0 on success, 1 on failure
#######################################
decompose_prd() {
    local prd_file="$1"
    local output_file="$2"
    local context_dir="$3"

    if [[ ! -f "${prd_file}" ]]; then
        echo "DECOMPOSE: Error: PRD file not found: ${prd_file}" >&2
        return 1
    fi

    echo ""
    echo "================================================================"
    echo "  MICRO-DELIVERABLE DECOMPOSITION"
    echo "  PRD: ${prd_file}"
    echo "================================================================"
    echo ""

    # Build decomposition prompt
    local prd_content
    prd_content=$(cat "${prd_file}")

    local decomposition_prompt
    decomposition_prompt=$(build_decomposition_prompt "${prd_content}")

    # Run Claude Code for decomposition
    echo "DECOMPOSE: Analyzing PRD and generating micro-deliverables..."
    local result
    result=$(cd "${context_dir}" && claude -p "${decomposition_prompt}" --output-format json 2>/dev/null)

    # Extract JSON from result
    local json_result
    json_result=$(echo "${result}" | grep -o '\{.*\}' | python3 -c "
import sys, json
data = sys.stdin.read()
# Find the outermost JSON object that contains micro_deliverables
try:
    parsed = json.loads(data)
    if 'micro_deliverables' in parsed:
        print(json.dumps(parsed, indent=2))
    else:
        print(data)
except:
    print(data)
" 2>/dev/null)

    if [[ -z "${json_result}" ]]; then
        echo "DECOMPOSE: Error: Could not parse decomposition result" >&2
        return 1
    fi

    # Validate structure
    local md_count
    md_count=$(echo "${json_result}" | jq '.micro_deliverables | length' 2>/dev/null || echo "0")

    if [[ ${md_count} -eq 0 ]]; then
        echo "DECOMPOSE: Error: No micro-deliverables generated" >&2
        return 1
    fi

    # Validate no circular dependencies
    if ! validate_dependencies "${json_result}"; then
        echo "DECOMPOSE: Error: Circular dependencies detected" >&2
        return 1
    fi

    # Write output
    local output_dir
    output_dir=$(dirname "${output_file}")
    mkdir -p "${output_dir}"
    echo "${json_result}" > "${output_file}"

    echo ""
    echo "DECOMPOSE: Generated ${md_count} micro-deliverables"
    echo "DECOMPOSE: Output: ${output_file}"
    echo ""

    # Print summary
    echo "DECOMPOSE: Summary:"
    echo "${json_result}" | jq -r '.micro_deliverables[] | "  \(.id): \(.title) [\(.category)] complexity=\(.estimated_complexity)"'

    echo ""

    # Print dependency graph
    echo "DECOMPOSE: Dependency graph:"
    echo "${json_result}" | jq -r '.micro_deliverables[] | select(.dependencies | length > 0) | "  \(.id) depends on: \(.dependencies | join(", "))"'

    local independent
    independent=$(echo "${json_result}" | jq '[.micro_deliverables[] | select(.dependencies | length == 0)] | length')
    echo "  ${independent} micro-deliverables have no dependencies (can start immediately)"

    echo ""
    return 0
}

#######################################
# Build decomposition prompt
#######################################
build_decomposition_prompt() {
    local prd_content="$1"

    cat <<PROMPT_EOF
## PRD Micro-Deliverable Decomposition

Je bent een ervaren Product Manager die PRD requirements opbreekt in de kleinst
mogelijke toetsbare eenheden (micro-deliverables).

### Regels voor Decomposition
1. Een micro-deliverable is NOOIT groter dan 1 component/functie/endpoint
2. Elk criterium moet in <5 minuten handmatig verifieerbaar zijn
3. Elke eenheid moet onafhankelijk testbaar zijn (met mocks voor dependencies)
4. Maximaal 3 acceptatiecriteria per micro-deliverable
5. Bij twijfel: opsplitsen in kleinere eenheden
6. Neem ALLE requirements mee, ook non-functional (security, performance, accessibility)
7. Geef dependencies aan waar nodig (MD-003 hangt af van MD-001)

### Categories
- functional: Gebruikersfunctionaliteit
- api: API endpoint/contract
- data: Database/schema wijziging
- security: Security requirement
- performance: Performance requirement
- ui: User interface element
- integration: Integratie met extern systeem
- documentation: Documentatie requirement

### PRD Content
${prd_content}

### Output
Antwoord UITSLUITEND in dit JSON formaat (geen andere tekst):
{
  "prd_source": "bestandsnaam of titel",
  "decomposed_at": "ISO timestamp",
  "total_count": 0,
  "micro_deliverables": [
    {
      "id": "MD-001",
      "prd_requirement_id": "REQ-001 of section naam",
      "title": "Korte beschrijving van wat opgeleverd moet worden",
      "acceptance_criteria": [
        "Criterium 1 (concreet, toetsbaar)",
        "Criterium 2",
        "Criterium 3"
      ],
      "expected_tests": [
        "test_naam_1",
        "test_naam_2"
      ],
      "dependencies": [],
      "category": "functional|api|data|security|performance|ui|integration|documentation",
      "estimated_complexity": "low|medium|high",
      "security_relevant": false,
      "performance_relevant": false
    }
  ]
}
PROMPT_EOF
}

#######################################
# Validate no circular dependencies
# Arguments:
#   $1 - JSON with micro_deliverables
# Returns:
#   0 if valid, 1 if circular
#######################################
validate_dependencies() {
    local json="$1"

    # Use Python for topological sort / cycle detection
    python3 -c "
import json, sys

data = json.loads('''${json}''')
mds = data.get('micro_deliverables', [])

# Build adjacency list
graph = {}
for md in mds:
    md_id = md['id']
    graph[md_id] = md.get('dependencies', [])

# Detect cycles using DFS
WHITE, GRAY, BLACK = 0, 1, 2
color = {node: WHITE for node in graph}

def has_cycle(node):
    color[node] = GRAY
    for dep in graph.get(node, []):
        if dep not in color:
            continue  # Unknown dependency, skip
        if color[dep] == GRAY:
            return True  # Back edge = cycle
        if color[dep] == WHITE and has_cycle(dep):
            return True
    color[node] = BLACK
    return False

for node in graph:
    if color[node] == WHITE:
        if has_cycle(node):
            print('CYCLE_DETECTED')
            sys.exit(1)

print('NO_CYCLES')
sys.exit(0)
" 2>/dev/null

    return $?
}

#######################################
# Get next micro-deliverable to work on
# (first with all dependencies completed)
# Arguments:
#   $1 - Path to micro-deliverables.json
#   $2 - Path to acceptance registry DB
#   $3 - Sprint ID
# Returns:
#   Micro-deliverable ID on stdout, 1 if none available
#######################################
get_next_micro_deliverable() {
    local deliverables_file="$1"
    local registry_db="$2"
    local sprint_id="$3"

    if [[ ! -f "${deliverables_file}" ]]; then
        return 1
    fi

    # Get list of already accepted deliverables
    local accepted_ids="[]"
    if [[ -f "${registry_db}" ]]; then
        accepted_ids=$(sqlite3 -json "${registry_db}" \
            "SELECT micro_deliverable_id FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'" 2>/dev/null | \
            jq '[.[].micro_deliverable_id]' 2>/dev/null || echo "[]")
    fi

    # Find first deliverable whose dependencies are all accepted
    python3 -c "
import json, sys

with open('${deliverables_file}') as f:
    data = json.load(f)

accepted = json.loads('${accepted_ids}')
mds = data.get('micro_deliverables', [])

for md in mds:
    md_id = md['id']
    if md_id in accepted:
        continue  # Already done
    deps = md.get('dependencies', [])
    if all(d in accepted for d in deps):
        print(md_id)
        sys.exit(0)

# No available deliverable
sys.exit(1)
" 2>/dev/null
}

#######################################
# Get micro-deliverable count and progress
# Arguments:
#   $1 - Path to micro-deliverables.json
#   $2 - Path to acceptance registry DB
#   $3 - Sprint ID
# Returns:
#   JSON with progress info
#######################################
get_decomposition_progress() {
    local deliverables_file="$1"
    local registry_db="$2"
    local sprint_id="$3"

    local total=0
    local accepted=0

    if [[ -f "${deliverables_file}" ]]; then
        total=$(jq '.micro_deliverables | length' "${deliverables_file}" 2>/dev/null || echo "0")
    fi

    if [[ -f "${registry_db}" ]]; then
        accepted=$(sqlite3 "${registry_db}" \
            "SELECT COUNT(*) FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'" 2>/dev/null || echo "0")
    fi

    local remaining=$((total - accepted))
    local percent=0
    if [[ ${total} -gt 0 ]]; then
        percent=$((accepted * 100 / total))
    fi

    cat <<JSON
{
    "total": ${total},
    "accepted": ${accepted},
    "remaining": ${remaining},
    "percent_complete": ${percent}
}
JSON
}

#######################################
# Export functions for sourcing
#######################################
export -f decompose_prd
export -f build_decomposition_prompt
export -f validate_dependencies
export -f get_next_micro_deliverable
export -f get_decomposition_progress

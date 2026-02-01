#!/bin/bash
# pm-acceptance-gate.sh - PM Agent Acceptance Gate for MarQed.ai Quality Harness
# Part of Fase 32E: Quality Harness
# Version 1.0
#
# Purpose: Independent PM review of micro-deliverables against PRD criteria.
#          The PM Gate is NOT the builder - it's a separate Claude Code invocation
#          that reviews the diff/output against acceptance criteria.
#
# Usage:
#   source mq/workflows/common/pm-acceptance-gate.sh
#   pm_acceptance_review <micro_deliverable_id> <deliverables_file> <context_dir>

# Load common functions if not already loaded
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Constants
PM_MAX_RETRIES=3
PM_CONFIDENCE_THRESHOLD=0.8
PM_PROMPT_TEMPLATE="${SCRIPT_DIR}/../prompts/pm-review.md"

#######################################
# Run PM Acceptance Gate on a micro-deliverable
# Arguments:
#   $1 - Micro-deliverable ID (e.g., "MD-001")
#   $2 - Path to micro-deliverables.json
#   $3 - Context directory (project root)
#   $4 - Path to acceptance registry DB
# Returns:
#   0 if ACCEPT, 1 if REJECT, 2 if ESCALATED
#######################################
pm_acceptance_review() {
    local md_id="$1"
    local deliverables_file="$2"
    local context_dir="$3"
    local registry_db="${4:-${context_dir}/.marqed/acceptance-registry.db}"

    if [[ ! -f "${deliverables_file}" ]]; then
        echo "PM_GATE: Error: Deliverables file not found: ${deliverables_file}" >&2
        return 1
    fi

    # Extract micro-deliverable spec
    local md_spec
    md_spec=$(jq -r ".micro_deliverables[] | select(.id == \"${md_id}\")" "${deliverables_file}")

    if [[ -z "${md_spec}" || "${md_spec}" == "null" ]]; then
        echo "PM_GATE: Error: Micro-deliverable ${md_id} not found" >&2
        return 1
    fi

    local md_title
    md_title=$(echo "${md_spec}" | jq -r '.title')
    local md_criteria
    md_criteria=$(echo "${md_spec}" | jq -r '.acceptance_criteria | join("\n- ")')
    local md_prd_id
    md_prd_id=$(echo "${md_spec}" | jq -r '.prd_requirement_id')

    echo ""
    echo "================================================================"
    echo "  PM ACCEPTANCE GATE"
    echo "  Micro-Deliverable: ${md_id} — ${md_title}"
    echo "  PRD Requirement:   ${md_prd_id}"
    echo "================================================================"
    echo ""

    # Get git diff for review
    local git_diff
    git_diff=$(cd "${context_dir}" && git diff HEAD~1 --stat --patch 2>/dev/null || echo "No git diff available")

    # Get test output if available
    local test_output="No test output available"
    if [[ -f "${context_dir}/.marqed/test-output.txt" ]]; then
        test_output=$(cat "${context_dir}/.marqed/test-output.txt" | head -100)
    fi

    # Build the PM review prompt
    local review_prompt
    review_prompt=$(build_pm_prompt "${md_id}" "${md_title}" "${md_criteria}" "${git_diff}" "${test_output}")

    # Run PM review via Claude Code (non-interactive)
    local pm_result
    local retry_count=0

    while [[ ${retry_count} -lt ${PM_MAX_RETRIES} ]]; do
        echo "PM_GATE: Review attempt $((retry_count + 1))/${PM_MAX_RETRIES}..."

        pm_result=$(run_pm_review "${review_prompt}" "${context_dir}")

        if [[ $? -ne 0 ]]; then
            echo "PM_GATE: Claude invocation failed, retrying..." >&2
            ((retry_count++))
            continue
        fi

        # Parse verdict
        local verdict
        verdict=$(echo "${pm_result}" | jq -r '.verdict' 2>/dev/null)
        local confidence
        confidence=$(echo "${pm_result}" | jq -r '.confidence' 2>/dev/null)
        local feedback
        feedback=$(echo "${pm_result}" | jq -r '.feedback' 2>/dev/null)

        # Validate parsed result
        if [[ -z "${verdict}" || "${verdict}" == "null" ]]; then
            echo "PM_GATE: Could not parse verdict, retrying..." >&2
            ((retry_count++))
            continue
        fi

        # Log the review
        log_pm_review "${registry_db}" "${md_id}" "${verdict}" "${confidence}" "${feedback}" "${retry_count}"

        # Check confidence threshold
        if [[ "${verdict}" == "ACCEPT" ]]; then
            local confidence_check
            confidence_check=$(echo "${confidence} >= ${PM_CONFIDENCE_THRESHOLD}" | bc -l 2>/dev/null || echo "1")

            if [[ "${confidence_check}" == "1" ]]; then
                echo ""
                echo "PM_GATE: ACCEPT (confidence: ${confidence})"
                echo "PM_GATE: ${feedback}"
                echo ""
                return 0
            else
                echo "PM_GATE: ACCEPT but low confidence (${confidence} < ${PM_CONFIDENCE_THRESHOLD})"
                echo "PM_GATE: Requesting additional validation..."
                ((retry_count++))
                continue
            fi
        fi

        if [[ "${verdict}" == "REJECT" ]]; then
            echo ""
            echo "PM_GATE: REJECT (attempt $((retry_count + 1)))"
            echo "PM_GATE: Feedback: ${feedback}"
            echo ""

            # Store feedback for the build agent
            store_pm_feedback "${context_dir}" "${md_id}" "${feedback}" "${retry_count}"

            ((retry_count++))

            if [[ ${retry_count} -ge ${PM_MAX_RETRIES} ]]; then
                echo "PM_GATE: Max retries reached (${PM_MAX_RETRIES}). ESCALATING."
                log_pm_review "${registry_db}" "${md_id}" "ESCALATED" "0" "Max retries reached" "${retry_count}"
                return 2
            fi

            # Return REJECT so the loop can send the agent back to work
            return 1
        fi

        # Unknown verdict
        echo "PM_GATE: Unknown verdict: ${verdict}, retrying..." >&2
        ((retry_count++))
    done

    # All retries exhausted
    echo "PM_GATE: ESCALATED — all retries exhausted"
    return 2
}

#######################################
# Build PM review prompt
#######################################
build_pm_prompt() {
    local md_id="$1"
    local md_title="$2"
    local md_criteria="$3"
    local git_diff="$4"
    local test_output="$5"

    cat <<PROMPT_EOF
## PM Acceptance Review

Je bent een Product Manager die beoordeelt of een opgeleverde wijziging voldoet
aan de gestelde acceptatiecriteria. Je bent NIET de bouwer — je bent de reviewer.
Wees kritisch maar eerlijk.

### Micro-Deliverable
- ID: ${md_id}
- Titel: ${md_title}
- Acceptatiecriteria:
- ${md_criteria}

### Wijzigingen (git diff)
\`\`\`
${git_diff}
\`\`\`

### Test Output
\`\`\`
${test_output}
\`\`\`

### Beoordeling
Geef per acceptatiecriterium:
- VOLDOET / VOLDOET NIET / ONDUIDELIJK
- Korte onderbouwing (1 zin)

### Verdict
Antwoord UITSLUITEND in dit JSON formaat (geen andere tekst):
{
  "verdict": "ACCEPT of REJECT",
  "criteria_results": [
    {"criterion": "...", "status": "VOLDOET/VOLDOET_NIET/ONDUIDELIJK", "reasoning": "..."}
  ],
  "feedback": "Samenvatting in 1-2 zinnen",
  "confidence": 0.0 tot 1.0,
  "improvements": ["suggestie 1", "suggestie 2"]
}
PROMPT_EOF
}

#######################################
# Run PM review via Claude Code
# Arguments:
#   $1 - Review prompt
#   $2 - Context directory
# Returns:
#   JSON result on stdout
#######################################
run_pm_review() {
    local prompt="$1"
    local context_dir="$2"

    # Write prompt to temp file
    local prompt_file
    prompt_file=$(mktemp "${context_dir}/.marqed/pm-review-XXXXXX.md")
    echo "${prompt}" > "${prompt_file}"

    # Run Claude Code in print mode (non-interactive)
    local result
    result=$(cd "${context_dir}" && claude -p "$(cat "${prompt_file}")" --output-format json 2>/dev/null)

    # Clean up
    rm -f "${prompt_file}"

    # Try to extract JSON from result
    local json_result
    json_result=$(echo "${result}" | grep -o '{.*}' | tail -1)

    if [[ -n "${json_result}" ]]; then
        echo "${json_result}"
        return 0
    fi

    echo '{"verdict": null, "error": "Could not parse PM response"}' >&2
    return 1
}

#######################################
# Store PM feedback for the build agent
#######################################
store_pm_feedback() {
    local context_dir="$1"
    local md_id="$2"
    local feedback="$3"
    local retry_count="$4"

    local feedback_dir="${context_dir}/.marqed/pm-feedback"
    mkdir -p "${feedback_dir}"

    local feedback_file="${feedback_dir}/${md_id}-retry${retry_count}.md"

    cat > "${feedback_file}" <<EOF
# PM Feedback — ${md_id} (Retry ${retry_count})

**Datum:** $(date '+%Y-%m-%d %H:%M')
**Verdict:** REJECT

## Feedback
${feedback}

## Actie vereist
Pas de implementatie aan op basis van bovenstaande feedback en dien opnieuw in.
EOF

    echo "PM_GATE: Feedback opgeslagen: ${feedback_file}"
}

#######################################
# Log PM review to acceptance registry
#######################################
log_pm_review() {
    local registry_db="$1"
    local md_id="$2"
    local verdict="$3"
    local confidence="$4"
    local feedback="$5"
    local retry_count="$6"

    # Ensure DB exists
    ensure_registry_db "${registry_db}"

    sqlite3 "${registry_db}" <<SQL
INSERT OR REPLACE INTO pm_reviews (
    micro_deliverable_id, verdict, confidence, feedback, retry_count, reviewed_at
) VALUES (
    '${md_id}', '${verdict}', ${confidence:-0}, '$(echo "${feedback}" | sed "s/'/''/g")', ${retry_count}, datetime('now')
);
SQL
}

#######################################
# Ensure acceptance registry DB exists
#######################################
ensure_registry_db() {
    local db_path="$1"
    local db_dir
    db_dir=$(dirname "${db_path}")
    mkdir -p "${db_dir}"

    if [[ ! -f "${db_path}" ]]; then
        sqlite3 "${db_path}" <<SQL
CREATE TABLE IF NOT EXISTS acceptance_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL,
    micro_deliverable_id TEXT NOT NULL,
    prd_requirement_id TEXT NOT NULL,
    title TEXT NOT NULL,
    pm_verdict TEXT CHECK(pm_verdict IN ('ACCEPT', 'REJECT', 'ESCALATED')),
    pm_confidence REAL,
    pm_feedback TEXT,
    pm_retries INTEGER DEFAULT 0,
    qa_code_quality_score REAL,
    qa_security_findings INTEGER DEFAULT 0,
    qa_security_highest_severity TEXT,
    qa_test_pass_rate REAL,
    qa_line_coverage REAL,
    qa_branch_coverage REAL,
    qa_performance_status TEXT CHECK(qa_performance_status IN ('PASS', 'WARN', 'FAIL')),
    contract_status TEXT CHECK(contract_status IN ('PASS', 'FAIL', 'N/A')),
    dependency_impact TEXT CHECK(dependency_impact IN ('LOW', 'MEDIUM', 'HIGH')),
    affected_modules TEXT,
    regression_tests_run INTEGER,
    regression_tests_passed INTEGER,
    regression_duration_seconds REAL,
    git_commit TEXT,
    files_changed TEXT,
    tests_added TEXT,
    accepted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pm_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    micro_deliverable_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    confidence REAL,
    feedback TEXT,
    retry_count INTEGER DEFAULT 0,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    micro_deliverable_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    score REAL,
    details TEXT,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regression_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL,
    trigger_deliverable_id TEXT NOT NULL,
    trigger_type TEXT CHECK(trigger_type IN ('progressive', 'sprint_completion', 'cross_sprint')),
    tests_run INTEGER,
    tests_passed INTEGER,
    tests_failed INTEGER,
    failures TEXT,
    duration_seconds REAL,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sprint_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL UNIQUE,
    total_deliverables INTEGER,
    accepted_deliverables INTEGER,
    total_coverage REAL,
    total_tests INTEGER,
    security_findings_resolved INTEGER,
    performance_regressions INTEGER,
    contract_breaks INTEGER,
    dead_code_removed INTEGER,
    report_markdown TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registry_sprint ON acceptance_registry(sprint_id);
CREATE INDEX IF NOT EXISTS idx_registry_md ON acceptance_registry(micro_deliverable_id);
CREATE INDEX IF NOT EXISTS idx_pm_reviews_md ON pm_reviews(micro_deliverable_id);
CREATE INDEX IF NOT EXISTS idx_qa_reviews_md ON qa_reviews(micro_deliverable_id);
CREATE INDEX IF NOT EXISTS idx_regression_sprint ON regression_history(sprint_id);
SQL
        echo "PM_GATE: Acceptance registry DB initialized: ${db_path}"
    fi
}

#######################################
# Register accepted micro-deliverable
# Called after PM + QA + Regression all pass
#######################################
register_acceptance() {
    local registry_db="$1"
    local sprint_id="$2"
    local md_id="$3"
    local prd_req_id="$4"
    local title="$5"
    local pm_confidence="$6"
    local qa_scores="$7"  # JSON with qa results
    local git_commit="$8"
    local files_changed="$9"
    local tests_added="${10}"

    ensure_registry_db "${registry_db}"

    # Parse QA scores
    local code_quality
    code_quality=$(echo "${qa_scores}" | jq -r '.code_quality_score // 0')
    local security_findings
    security_findings=$(echo "${qa_scores}" | jq -r '.security_findings // 0')
    local test_pass_rate
    test_pass_rate=$(echo "${qa_scores}" | jq -r '.test_pass_rate // 0')
    local line_coverage
    line_coverage=$(echo "${qa_scores}" | jq -r '.line_coverage // 0')
    local branch_coverage
    branch_coverage=$(echo "${qa_scores}" | jq -r '.branch_coverage // 0')
    local perf_status
    perf_status=$(echo "${qa_scores}" | jq -r '.performance_status // "PASS"')

    sqlite3 "${registry_db}" <<SQL
INSERT INTO acceptance_registry (
    sprint_id, micro_deliverable_id, prd_requirement_id, title,
    pm_verdict, pm_confidence,
    qa_code_quality_score, qa_security_findings, qa_test_pass_rate,
    qa_line_coverage, qa_branch_coverage, qa_performance_status,
    git_commit, files_changed, tests_added, accepted_at
) VALUES (
    '${sprint_id}', '${md_id}', '${prd_req_id}', '$(echo "${title}" | sed "s/'/''/g")',
    'ACCEPT', ${pm_confidence},
    ${code_quality}, ${security_findings}, ${test_pass_rate},
    ${line_coverage}, ${branch_coverage}, '${perf_status}',
    '${git_commit}', '$(echo "${files_changed}" | sed "s/'/''/g")',
    '$(echo "${tests_added}" | sed "s/'/''/g")', datetime('now')
);
SQL

    echo "PM_GATE: Micro-deliverable ${md_id} registered as ACCEPTED"
}

#######################################
# Get all accepted test names for regression
#######################################
get_accepted_tests() {
    local registry_db="$1"
    local sprint_id="$2"

    if [[ ! -f "${registry_db}" ]]; then
        echo "[]"
        return
    fi

    sqlite3 -json "${registry_db}" \
        "SELECT tests_added FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'" 2>/dev/null | \
        jq -r '.[].tests_added' | jq -s 'map(fromjson? // []) | add // []'
}

#######################################
# Export functions for sourcing
#######################################
export -f pm_acceptance_review
export -f build_pm_prompt
export -f run_pm_review
export -f store_pm_feedback
export -f log_pm_review
export -f ensure_registry_db
export -f register_acceptance
export -f get_accepted_tests

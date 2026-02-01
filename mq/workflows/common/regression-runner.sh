#!/bin/bash
# regression-runner.sh - Progressive Regression Runner for MarQed.ai Quality Harness
# Part of Fase 32E: Quality Harness
# Version 1.0
#
# Purpose: After each accepted micro-deliverable, run ALL previously accepted tests.
#          At sprint end, run full regression across all sprints.
#
# Usage:
#   source mq/workflows/common/regression-runner.sh
#   run_progressive_regression <registry_db> <sprint_id> <trigger_md_id> <context_dir>
#   run_sprint_regression <registry_db> <sprint_id> <context_dir>
#   generate_sprint_report <registry_db> <sprint_id> <context_dir> <prd_file>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Run progressive regression after accepting a micro-deliverable
# Arguments:
#   $1 - Path to acceptance registry DB
#   $2 - Sprint ID
#   $3 - Trigger micro-deliverable ID (the one just accepted)
#   $4 - Context directory (project root)
# Returns:
#   0 if all pass, 1 if regression detected
#######################################
run_progressive_regression() {
    local registry_db="$1"
    local sprint_id="$2"
    local trigger_md_id="$3"
    local context_dir="$4"

    echo ""
    echo "================================================================"
    echo "  PROGRESSIVE REGRESSION"
    echo "  Trigger: ${trigger_md_id} accepted"
    echo "  Sprint:  ${sprint_id}"
    echo "================================================================"
    echo ""

    if [[ ! -f "${registry_db}" ]]; then
        echo "REGRESSION: No registry DB found, skipping"
        return 0
    fi

    # Get all accepted test names from this sprint
    local accepted_tests
    accepted_tests=$(sqlite3 "${registry_db}" \
        "SELECT tests_added FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT' AND tests_added IS NOT NULL" 2>/dev/null)

    if [[ -z "${accepted_tests}" ]]; then
        echo "REGRESSION: No accepted tests found for sprint ${sprint_id}"
        return 0
    fi

    # Flatten all test names
    local all_tests
    all_tests=$(echo "${accepted_tests}" | python3 -c "
import sys, json
tests = set()
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            parsed = json.loads(line)
            if isinstance(parsed, list):
                tests.update(parsed)
        except:
            pass
for t in sorted(tests):
    print(t)
" 2>/dev/null)

    local test_count
    test_count=$(echo "${all_tests}" | grep -c . || echo "0")

    echo "REGRESSION: Running ${test_count} accumulated tests..."

    # Run the tests
    local start_time
    start_time=$(date +%s)

    local test_result
    local tests_passed=0
    local tests_failed=0
    local failures=""

    if [[ ${test_count} -gt 0 ]] && command -v pytest &>/dev/null; then
        # Build pytest expression from test names
        local pytest_args=""
        while IFS= read -r test_name; do
            if [[ -n "${test_name}" ]]; then
                pytest_args="${pytest_args} -k ${test_name}"
            fi
        done <<< "${all_tests}"

        # Run pytest with all accumulated test names
        test_result=$(cd "${context_dir}" && python -m pytest ${pytest_args} --tb=short -q 2>&1 || echo "")

        tests_passed=$(echo "${test_result}" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        tests_failed=$(echo "${test_result}" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

        # Capture failure details
        if [[ ${tests_failed} -gt 0 ]]; then
            failures=$(echo "${test_result}" | grep "FAILED" | head -20)
        fi
    else
        # Fallback: run full test suite
        test_result=$(cd "${context_dir}" && python -m pytest --tb=short -q 2>&1 || echo "")
        tests_passed=$(echo "${test_result}" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        tests_failed=$(echo "${test_result}" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Log regression result
    log_regression "${registry_db}" "${sprint_id}" "${trigger_md_id}" "progressive" \
        "${test_count}" "${tests_passed}" "${tests_failed}" "${failures}" "${duration}"

    echo ""
    echo "REGRESSION: Results: ${tests_passed} passed, ${tests_failed} failed (${duration}s)"

    if [[ ${tests_failed} -gt 0 ]]; then
        echo ""
        echo "================================================================"
        echo "  REGRESSION FAILURE — HARD STOP"
        echo "  ${tests_failed} previously passing tests now FAIL"
        echo "  Fix regression before continuing to next deliverable"
        echo "================================================================"
        echo ""
        echo "Failed tests:"
        echo "${failures}"
        echo ""

        # Save regression failure details
        local failure_file="${context_dir}/.marqed/regression-failure-${trigger_md_id}.txt"
        echo "Regression failure triggered by: ${trigger_md_id}" > "${failure_file}"
        echo "Date: $(date '+%Y-%m-%d %H:%M')" >> "${failure_file}"
        echo "Tests failed: ${tests_failed}" >> "${failure_file}"
        echo "" >> "${failure_file}"
        echo "${test_result}" >> "${failure_file}"

        return 1
    fi

    echo "REGRESSION: All ${tests_passed} tests still passing"
    echo ""
    return 0
}

#######################################
# Run full sprint regression (at sprint end)
# Arguments:
#   $1 - Path to acceptance registry DB
#   $2 - Sprint ID
#   $3 - Context directory
# Returns:
#   0 if all pass, 1 if failures
#######################################
run_sprint_regression() {
    local registry_db="$1"
    local sprint_id="$2"
    local context_dir="$3"

    echo ""
    echo "================================================================"
    echo "  SPRINT COMPLETION REGRESSION"
    echo "  Sprint: ${sprint_id}"
    echo "  Running FULL project test suite"
    echo "================================================================"
    echo ""

    local start_time
    start_time=$(date +%s)

    # Run the complete test suite
    local test_result
    test_result=$(cd "${context_dir}" && python -m pytest --tb=short -q 2>&1 || echo "")

    local tests_passed
    tests_passed=$(echo "${test_result}" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
    local tests_failed
    tests_failed=$(echo "${test_result}" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
    local tests_total=$((tests_passed + tests_failed))

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    local failures=""
    if [[ ${tests_failed} -gt 0 ]]; then
        failures=$(echo "${test_result}" | grep "FAILED" | head -50)
    fi

    # Log sprint regression
    log_regression "${registry_db}" "${sprint_id}" "SPRINT_COMPLETION" "sprint_completion" \
        "${tests_total}" "${tests_passed}" "${tests_failed}" "${failures}" "${duration}"

    echo "SPRINT REGRESSION: ${tests_passed}/${tests_total} passed (${duration}s)"

    # Run coverage report
    echo ""
    echo "--- Coverage Report ---"
    local coverage_result
    if command -v coverage &>/dev/null; then
        coverage_result=$(cd "${context_dir}" && python -m pytest --cov --cov-report=term-missing -q 2>&1 | tail -30 || echo "Coverage not available")
        echo "${coverage_result}"

        # Extract total coverage
        local total_coverage
        total_coverage=$(echo "${coverage_result}" | grep "TOTAL" | grep -oE '[0-9]+%' | head -1 | tr -d '%' || echo "0")
        echo ""
        echo "Total project coverage: ${total_coverage}%"

        if [[ ${total_coverage} -lt 80 ]]; then
            echo "WARNING: Coverage below 80% minimum (${total_coverage}%)"
        elif [[ ${total_coverage} -lt 95 ]]; then
            echo "INFO: Coverage below 95% target (${total_coverage}%)"
        else
            echo "EXCELLENT: Coverage meets 95% target"
        fi
    fi

    if [[ ${tests_failed} -gt 0 ]]; then
        echo ""
        echo "SPRINT REGRESSION: FAILED — ${tests_failed} tests failing"
        return 1
    fi

    echo ""
    echo "SPRINT REGRESSION: ALL PASSED"
    return 0
}

#######################################
# Generate sprint acceptance report
# Arguments:
#   $1 - Path to acceptance registry DB
#   $2 - Sprint ID
#   $3 - Context directory
#   $4 - Path to PRD file (for traceability)
# Returns:
#   Path to generated report
#######################################
generate_sprint_report() {
    local registry_db="$1"
    local sprint_id="$2"
    local context_dir="$3"
    local prd_file="$4"

    local report_dir="${context_dir}/.marqed/reports"
    mkdir -p "${report_dir}"
    local report_file="${report_dir}/sprint-report-${sprint_id}.md"

    echo "REPORT: Generating sprint acceptance report..."

    # Gather statistics
    local total_deliverables
    total_deliverables=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM acceptance_registry WHERE sprint_id = '${sprint_id}'" 2>/dev/null || echo "0")
    local accepted_deliverables
    accepted_deliverables=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'" 2>/dev/null || echo "0")

    # Coverage
    local avg_coverage
    avg_coverage=$(sqlite3 "${registry_db}" \
        "SELECT ROUND(AVG(qa_line_coverage), 1) FROM acceptance_registry WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'" 2>/dev/null || echo "0")

    # Security
    local total_security_findings
    total_security_findings=$(sqlite3 "${registry_db}" \
        "SELECT SUM(qa_security_findings) FROM acceptance_registry WHERE sprint_id = '${sprint_id}'" 2>/dev/null || echo "0")

    # Regression history
    local total_progressive_runs
    total_progressive_runs=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM regression_history WHERE sprint_id = '${sprint_id}' AND trigger_type = 'progressive'" 2>/dev/null || echo "0")
    local total_test_executions
    total_test_executions=$(sqlite3 "${registry_db}" \
        "SELECT SUM(tests_run) FROM regression_history WHERE sprint_id = '${sprint_id}'" 2>/dev/null || echo "0")

    # PM review stats
    local total_pm_reviews
    total_pm_reviews=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM pm_reviews" 2>/dev/null || echo "0")
    local total_pm_rejects
    total_pm_rejects=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM pm_reviews WHERE verdict = 'REJECT'" 2>/dev/null || echo "0")

    # QA review stats
    local total_qa_failures
    total_qa_failures=$(sqlite3 "${registry_db}" \
        "SELECT COUNT(*) FROM qa_reviews WHERE status = 'FAIL'" 2>/dev/null || echo "0")

    # Traceability matrix
    local traceability
    traceability=$(sqlite3 -separator '|' "${registry_db}" \
        "SELECT prd_requirement_id, GROUP_CONCAT(micro_deliverable_id, ', '), COUNT(*), ROUND(AVG(qa_line_coverage), 1)
         FROM acceptance_registry
         WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'
         GROUP BY prd_requirement_id" 2>/dev/null || echo "")

    # Build report
    cat > "${report_file}" <<REPORT
# Sprint Acceptance Report — ${sprint_id}

**Generated:** $(date '+%Y-%m-%d %H:%M')
**PRD:** ${prd_file}

---

## Summary

| Metric | Value |
|--------|-------|
| Micro-deliverables total | ${total_deliverables} |
| Micro-deliverables accepted | ${accepted_deliverables} |
| Average line coverage | ${avg_coverage}% |
| Coverage target | 80% min / 95% target |
| Security findings (total resolved) | ${total_security_findings} |
| Progressive regression runs | ${total_progressive_runs} |
| Total test executions | ${total_test_executions} |
| PM reviews total | ${total_pm_reviews} |
| PM rejects (caught issues) | ${total_pm_rejects} |
| QA failures (caught issues) | ${total_qa_failures} |

## Traceability Matrix

| PRD Requirement | Micro-Deliverables | Count | Avg Coverage |
|-----------------|-------------------|-------|-------------|
REPORT

    # Add traceability rows
    if [[ -n "${traceability}" ]]; then
        while IFS='|' read -r req_id mds count coverage; do
            echo "| ${req_id} | ${mds} | ${count} | ${coverage}% |" >> "${report_file}"
        done <<< "${traceability}"
    else
        echo "| (no data) | - | 0 | - |" >> "${report_file}"
    fi

    cat >> "${report_file}" <<REPORT

## Deliverable Details

REPORT

    # Add per-deliverable details
    local deliverable_details
    deliverable_details=$(sqlite3 -separator '|' "${registry_db}" \
        "SELECT micro_deliverable_id, title, qa_line_coverage, qa_code_quality_score, qa_security_findings, qa_performance_status, accepted_at
         FROM acceptance_registry
         WHERE sprint_id = '${sprint_id}' AND pm_verdict = 'ACCEPT'
         ORDER BY accepted_at" 2>/dev/null || echo "")

    echo "| ID | Title | Coverage | Code Quality | Security | Performance | Accepted |" >> "${report_file}"
    echo "|----|-------|----------|-------------|----------|-------------|----------|" >> "${report_file}"

    if [[ -n "${deliverable_details}" ]]; then
        while IFS='|' read -r md_id title coverage cq_score sec_findings perf_status accepted_at; do
            echo "| ${md_id} | ${title} | ${coverage}% | ${cq_score}/10 | ${sec_findings} findings | ${perf_status} | ${accepted_at} |" >> "${report_file}"
        done <<< "${deliverable_details}"
    fi

    cat >> "${report_file}" <<REPORT

## Regression History

| Run | Trigger | Type | Tests | Passed | Failed | Duration |
|-----|---------|------|-------|--------|--------|----------|
REPORT

    local regression_details
    regression_details=$(sqlite3 -separator '|' "${registry_db}" \
        "SELECT ROW_NUMBER() OVER (ORDER BY run_at), trigger_deliverable_id, trigger_type, tests_run, tests_passed, tests_failed, duration_seconds
         FROM regression_history
         WHERE sprint_id = '${sprint_id}'
         ORDER BY run_at" 2>/dev/null || echo "")

    if [[ -n "${regression_details}" ]]; then
        while IFS='|' read -r num trigger type tests_run passed failed duration; do
            echo "| ${num} | ${trigger} | ${type} | ${tests_run} | ${passed} | ${failed} | ${duration}s |" >> "${report_file}"
        done <<< "${regression_details}"
    fi

    cat >> "${report_file}" <<REPORT

---

## Quality Assessment

REPORT

    # Assessment based on metrics
    if [[ ${accepted_deliverables} -eq ${total_deliverables} ]]; then
        echo "- All micro-deliverables accepted" >> "${report_file}"
    else
        echo "- WARNING: ${total_deliverables} - ${accepted_deliverables} = $((total_deliverables - accepted_deliverables)) deliverables NOT accepted" >> "${report_file}"
    fi

    local avg_cov_int
    avg_cov_int=$(printf "%.0f" "${avg_coverage}" 2>/dev/null || echo "0")
    if [[ ${avg_cov_int} -ge 95 ]]; then
        echo "- Coverage: EXCELLENT (${avg_coverage}% >= 95% target)" >> "${report_file}"
    elif [[ ${avg_cov_int} -ge 80 ]]; then
        echo "- Coverage: ACCEPTABLE (${avg_coverage}% >= 80% minimum, below 95% target)" >> "${report_file}"
    else
        echo "- Coverage: BELOW MINIMUM (${avg_coverage}% < 80%)" >> "${report_file}"
    fi

    echo "" >> "${report_file}"
    echo "---" >> "${report_file}"
    echo "*Generated by Fase 32E Quality Harness*" >> "${report_file}"

    # Save report reference in DB
    sqlite3 "${registry_db}" <<SQL
INSERT OR REPLACE INTO sprint_reports (
    sprint_id, total_deliverables, accepted_deliverables,
    total_coverage, total_tests, security_findings_resolved,
    report_markdown, created_at
) VALUES (
    '${sprint_id}', ${total_deliverables}, ${accepted_deliverables},
    ${avg_coverage}, ${total_test_executions:-0}, ${total_security_findings},
    '$(cat "${report_file}" | sed "s/'/''/g")', datetime('now')
);
SQL

    echo "REPORT: Sprint report generated: ${report_file}"
    echo "${report_file}"
}

#######################################
# Log regression result
#######################################
log_regression() {
    local registry_db="$1"
    local sprint_id="$2"
    local trigger_md_id="$3"
    local trigger_type="$4"
    local tests_run="$5"
    local tests_passed="$6"
    local tests_failed="$7"
    local failures="$8"
    local duration="$9"

    if [[ ! -f "${registry_db}" ]]; then
        return 0
    fi

    sqlite3 "${registry_db}" <<SQL
INSERT INTO regression_history (
    sprint_id, trigger_deliverable_id, trigger_type,
    tests_run, tests_passed, tests_failed, failures, duration_seconds, run_at
) VALUES (
    '${sprint_id}', '${trigger_md_id}', '${trigger_type}',
    ${tests_run:-0}, ${tests_passed:-0}, ${tests_failed:-0},
    '$(echo "${failures}" | sed "s/'/''/g")', ${duration:-0}, datetime('now')
);
SQL
}

#######################################
# Export functions for sourcing
#######################################
export -f run_progressive_regression
export -f run_sprint_regression
export -f generate_sprint_report
export -f log_regression

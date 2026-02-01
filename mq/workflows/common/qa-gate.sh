#!/bin/bash
# qa-gate.sh - QA Agent Quality Gate for MarQed.ai Quality Harness
# Part of Fase 32E: Quality Harness
# Version 1.0
#
# Purpose: Automated quality assurance on 4 axes:
#   1. Code Quality (linting, complexity, dead code)
#   2. Security (CWE scan, dependency audit, credential check)
#   3. Tests + Coverage (pass rate, line/branch coverage)
#   4. Performance (response time, memory, N+1 queries)
#
# Plus additional checks:
#   5. Contract Verification (API/DB backward compatibility)
#   6. Dependency Impact Scan (blast radius analysis)
#   7. Dead Code Detection
#
# Usage:
#   source mq/workflows/common/qa-gate.sh
#   qa_full_gate <context_dir> <registry_db> <micro_deliverable_id>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Thresholds
QA_PYLINT_MIN=7.0
QA_PYLINT_TARGET=9.0
QA_COMPLEXITY_MAX=15
QA_COMPLEXITY_TARGET=10
QA_COVERAGE_MIN=80
QA_COVERAGE_TARGET=95
QA_BRANCH_COVERAGE_MIN=70
QA_BRANCH_COVERAGE_TARGET=85
QA_PERF_WARN_THRESHOLD=10   # % degradation
QA_PERF_FAIL_THRESHOLD=20   # % degradation
QA_IMPACT_MEDIUM_THRESHOLD=4
QA_IMPACT_HIGH_THRESHOLD=10

#######################################
# Run full QA gate on a micro-deliverable
# Arguments:
#   $1 - Context directory (project root)
#   $2 - Path to acceptance registry DB
#   $3 - Micro-deliverable ID
# Returns:
#   0 if all PASS, 1 if any FAIL
#######################################
qa_full_gate() {
    local context_dir="$1"
    local registry_db="$2"
    local md_id="$3"

    echo ""
    echo "================================================================"
    echo "  QA QUALITY GATE"
    echo "  Micro-Deliverable: ${md_id}"
    echo "================================================================"
    echo ""

    local overall_pass=0
    local qa_results="{}"

    # 1. Code Quality
    echo "--- [1/7] Code Quality Check ---"
    local cq_result
    cq_result=$(qa_check_code_quality "${context_dir}")
    local cq_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson cq "${cq_result}" '. + {code_quality: $cq}')
    if [[ ${cq_status} -ne 0 ]]; then
        echo "QA_GATE: Code Quality FAIL"
        overall_pass=1
    else
        echo "QA_GATE: Code Quality PASS"
    fi
    echo ""

    # 2. Security
    echo "--- [2/7] Security Check ---"
    local sec_result
    sec_result=$(qa_check_security "${context_dir}")
    local sec_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson sec "${sec_result}" '. + {security: $sec}')
    if [[ ${sec_status} -ne 0 ]]; then
        echo "QA_GATE: Security FAIL — HARD STOP"
        log_qa_review "${registry_db}" "${md_id}" "security" "FAIL" "0" "$(echo "${sec_result}" | jq -r '.details')"
        return 1  # Hard stop on security failure
    else
        echo "QA_GATE: Security PASS"
    fi
    echo ""

    # 3. Tests + Coverage
    echo "--- [3/7] Tests + Coverage Check ---"
    local test_result
    test_result=$(qa_check_tests_coverage "${context_dir}")
    local test_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson t "${test_result}" '. + {tests: $t}')
    if [[ ${test_status} -ne 0 ]]; then
        echo "QA_GATE: Tests/Coverage FAIL"
        overall_pass=1
    else
        echo "QA_GATE: Tests/Coverage PASS"
    fi
    echo ""

    # 4. Performance
    echo "--- [4/7] Performance Check ---"
    local perf_result
    perf_result=$(qa_check_performance "${context_dir}")
    local perf_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson p "${perf_result}" '. + {performance: $p}')
    if [[ ${perf_status} -eq 2 ]]; then
        echo "QA_GATE: Performance FAIL (>20% degradation)"
        overall_pass=1
    elif [[ ${perf_status} -eq 1 ]]; then
        echo "QA_GATE: Performance WARN (10-20% degradation)"
        # WARN does not block
    else
        echo "QA_GATE: Performance PASS"
    fi
    echo ""

    # 5. Contract Verification
    echo "--- [5/7] Contract Verification ---"
    local contract_result
    contract_result=$(qa_check_contracts "${context_dir}")
    local contract_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson c "${contract_result}" '. + {contracts: $c}')
    if [[ ${contract_status} -ne 0 ]]; then
        echo "QA_GATE: Contract Verification FAIL — breaking change detected"
        overall_pass=1
    else
        echo "QA_GATE: Contract Verification PASS"
    fi
    echo ""

    # 6. Dependency Impact Scan
    echo "--- [6/7] Dependency Impact Scan ---"
    local impact_result
    impact_result=$(qa_check_dependency_impact "${context_dir}")
    local impact_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson i "${impact_result}" '. + {impact: $i}')
    local impact_level
    impact_level=$(echo "${impact_result}" | jq -r '.level')
    echo "QA_GATE: Dependency Impact: ${impact_level}"
    if [[ "${impact_level}" == "HIGH" ]]; then
        echo "QA_GATE: HIGH impact — extra regression scope recommended"
    fi
    echo ""

    # 7. Dead Code Detection
    echo "--- [7/7] Dead Code Detection ---"
    local dead_result
    dead_result=$(qa_check_dead_code "${context_dir}")
    local dead_status=$?
    qa_results=$(echo "${qa_results}" | jq --argjson d "${dead_result}" '. + {dead_code: $d}')
    local dead_count
    dead_count=$(echo "${dead_result}" | jq -r '.count')
    if [[ ${dead_count} -gt 0 ]]; then
        echo "QA_GATE: Dead code detected: ${dead_count} items (WARN)"
    else
        echo "QA_GATE: No dead code detected"
    fi
    echo ""

    # Log all results
    log_qa_review "${registry_db}" "${md_id}" "full_gate" \
        "$([ ${overall_pass} -eq 0 ] && echo 'PASS' || echo 'FAIL')" \
        "0" "$(echo "${qa_results}" | jq -c '.')"

    # Store results for the registry
    echo "${qa_results}" > "${context_dir}/.marqed/qa-results-${md_id}.json"

    echo "================================================================"
    if [[ ${overall_pass} -eq 0 ]]; then
        echo "  QA GATE: ALL CHECKS PASSED"
    else
        echo "  QA GATE: FAILED — see details above"
    fi
    echo "================================================================"
    echo ""

    return ${overall_pass}
}

#######################################
# 1. Code Quality Check
#######################################
qa_check_code_quality() {
    local context_dir="$1"
    local result='{"status": "PASS", "score": 0, "details": {}}'

    # Get changed Python files
    local changed_files
    changed_files=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' || echo "")

    if [[ -z "${changed_files}" ]]; then
        echo '{"status": "PASS", "score": 10.0, "details": {"message": "No Python files changed"}}'
        return 0
    fi

    local overall_score=10.0
    local issues=0

    # Run pylint if available
    if command -v pylint &>/dev/null; then
        local pylint_output
        pylint_output=$(cd "${context_dir}" && echo "${changed_files}" | xargs pylint --output-format=json 2>/dev/null || echo "[]")

        local pylint_score
        pylint_score=$(cd "${context_dir}" && echo "${changed_files}" | xargs pylint 2>/dev/null | grep "rated at" | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "${QA_PYLINT_MIN}")

        overall_score="${pylint_score:-${QA_PYLINT_MIN}}"

        local error_count
        error_count=$(echo "${pylint_output}" | jq 'map(select(.type == "error")) | length' 2>/dev/null || echo "0")
        issues=$((issues + error_count))
    fi

    # Run complexity check if radon available
    local complexity_max=0
    if command -v radon &>/dev/null; then
        complexity_max=$(cd "${context_dir}" && echo "${changed_files}" | xargs radon cc -n C -s 2>/dev/null | grep -oE '\([0-9]+\)' | tr -d '()' | sort -rn | head -1 || echo "0")
    fi

    # Check for dead imports (basic check)
    local dead_imports=0
    if command -v autoflake &>/dev/null; then
        dead_imports=$(cd "${context_dir}" && echo "${changed_files}" | xargs autoflake --check 2>/dev/null | grep -c "unused" || echo "0")
    fi

    # Build result
    local score_ok
    score_ok=$(echo "${overall_score} >= ${QA_PYLINT_MIN}" | bc -l 2>/dev/null || echo "1")
    local complexity_ok
    complexity_ok=$([[ ${complexity_max} -le ${QA_COMPLEXITY_MAX} ]] && echo "1" || echo "0")

    local status="PASS"
    if [[ "${score_ok}" == "0" || "${complexity_ok}" == "0" ]]; then
        status="FAIL"
    fi

    cat <<JSON
{
    "status": "${status}",
    "score": ${overall_score},
    "details": {
        "pylint_score": ${overall_score},
        "pylint_min": ${QA_PYLINT_MIN},
        "pylint_target": ${QA_PYLINT_TARGET},
        "max_complexity": ${complexity_max},
        "complexity_limit": ${QA_COMPLEXITY_MAX},
        "dead_imports": ${dead_imports},
        "error_count": ${issues},
        "files_checked": $(echo "${changed_files}" | wc -l | tr -d ' ')
    }
}
JSON

    [[ "${status}" == "PASS" ]] && return 0 || return 1
}

#######################################
# 2. Security Check
#######################################
qa_check_security() {
    local context_dir="$1"
    local findings=0
    local highest_severity="NONE"
    local details=""

    # Get changed files
    local changed_files
    changed_files=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null || echo "")

    if [[ -z "${changed_files}" ]]; then
        echo '{"status": "PASS", "findings": 0, "highest_severity": "NONE", "details": "No files changed"}'
        return 0
    fi

    # Run bandit if available (Python security)
    if command -v bandit &>/dev/null; then
        local bandit_output
        bandit_output=$(cd "${context_dir}" && echo "${changed_files}" | grep '\.py$' | xargs bandit -f json 2>/dev/null || echo '{"results": []}')

        local bandit_high
        bandit_high=$(echo "${bandit_output}" | jq '[.results[] | select(.issue_severity == "HIGH")] | length' 2>/dev/null || echo "0")
        local bandit_medium
        bandit_medium=$(echo "${bandit_output}" | jq '[.results[] | select(.issue_severity == "MEDIUM")] | length' 2>/dev/null || echo "0")

        findings=$((findings + bandit_high + bandit_medium))

        if [[ ${bandit_high} -gt 0 ]]; then
            highest_severity="HIGH"
        elif [[ ${bandit_medium} -gt 0 && "${highest_severity}" != "HIGH" ]]; then
            highest_severity="MEDIUM"
        fi
    fi

    # Check for hardcoded credentials (basic patterns)
    local cred_patterns="(password|secret|api_key|token|credential)\\s*=\\s*['\"][^'\"]+['\"]"
    local cred_findings
    cred_findings=$(cd "${context_dir}" && echo "${changed_files}" | xargs grep -iEn "${cred_patterns}" 2>/dev/null | grep -v "test" | grep -v "#" | wc -l | tr -d ' ')

    if [[ ${cred_findings} -gt 0 ]]; then
        findings=$((findings + cred_findings))
        highest_severity="CRITICAL"
        details="Hardcoded credentials detected in ${cred_findings} locations"
    fi

    # Check for SQL injection patterns
    local sqli_patterns="(execute|cursor\.execute|raw_sql).*(%s|format|f\")"
    local sqli_findings
    sqli_findings=$(cd "${context_dir}" && echo "${changed_files}" | grep '\.py$' | xargs grep -iEn "${sqli_patterns}" 2>/dev/null | wc -l | tr -d ' ')

    if [[ ${sqli_findings} -gt 0 ]]; then
        findings=$((findings + sqli_findings))
        [[ "${highest_severity}" != "CRITICAL" ]] && highest_severity="HIGH"
    fi

    # Run safety check if available (dependency vulnerabilities)
    if command -v safety &>/dev/null && [[ -f "${context_dir}/requirements.txt" ]]; then
        local safety_output
        safety_output=$(cd "${context_dir}" && safety check --json 2>/dev/null || echo "[]")
        local safety_findings
        safety_findings=$(echo "${safety_output}" | jq 'length' 2>/dev/null || echo "0")
        findings=$((findings + safety_findings))
    fi

    local status="PASS"
    if [[ "${highest_severity}" == "CRITICAL" || "${highest_severity}" == "HIGH" ]]; then
        status="FAIL"
    fi

    cat <<JSON
{
    "status": "${status}",
    "findings": ${findings},
    "highest_severity": "${highest_severity}",
    "details": "${details}",
    "checks": {
        "bandit": true,
        "credential_scan": true,
        "sqli_scan": true,
        "dependency_audit": $(command -v safety &>/dev/null && echo "true" || echo "false")
    }
}
JSON

    [[ "${status}" == "PASS" ]] && return 0 || return 1
}

#######################################
# 3. Tests + Coverage Check
#######################################
qa_check_tests_coverage() {
    local context_dir="$1"

    # Get changed files for targeted coverage
    local changed_files
    changed_files=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' || echo "")

    local test_pass_rate=100
    local line_coverage=0
    local branch_coverage=0
    local tests_total=0
    local tests_passed=0
    local tests_failed=0

    # Run pytest with coverage if available
    if command -v pytest &>/dev/null; then
        local pytest_output
        pytest_output=$(cd "${context_dir}" && python -m pytest --tb=short -q 2>&1 || echo "")

        # Parse test results
        tests_passed=$(echo "${pytest_output}" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        tests_failed=$(echo "${pytest_output}" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
        tests_total=$((tests_passed + tests_failed))

        if [[ ${tests_total} -gt 0 ]]; then
            test_pass_rate=$((tests_passed * 100 / tests_total))
        fi

        # Save test output for PM gate
        echo "${pytest_output}" > "${context_dir}/.marqed/test-output.txt"

        # Run coverage if available
        if command -v coverage &>/dev/null && [[ -n "${changed_files}" ]]; then
            local coverage_output
            coverage_output=$(cd "${context_dir}" && python -m pytest --cov --cov-report=json --cov-report=term -q 2>&1 || echo "")

            if [[ -f "${context_dir}/coverage.json" ]]; then
                line_coverage=$(jq -r '.totals.percent_covered' "${context_dir}/coverage.json" 2>/dev/null || echo "0")
                # Branch coverage from coverage report
                branch_coverage=$(jq -r '.totals.percent_covered_branches // 0' "${context_dir}/coverage.json" 2>/dev/null || echo "0")
            fi
        fi
    fi

    # Determine status
    local status="PASS"
    if [[ ${test_pass_rate} -lt 100 ]]; then
        status="FAIL"
    fi

    local coverage_int
    coverage_int=$(printf "%.0f" "${line_coverage}" 2>/dev/null || echo "0")
    if [[ ${coverage_int} -lt ${QA_COVERAGE_MIN} ]]; then
        status="FAIL"
    fi

    cat <<JSON
{
    "status": "${status}",
    "test_pass_rate": ${test_pass_rate},
    "line_coverage": ${line_coverage},
    "branch_coverage": ${branch_coverage},
    "coverage_min": ${QA_COVERAGE_MIN},
    "coverage_target": ${QA_COVERAGE_TARGET},
    "tests": {
        "total": ${tests_total},
        "passed": ${tests_passed},
        "failed": ${tests_failed}
    },
    "details": {
        "files_measured": $(echo "${changed_files}" | wc -l | tr -d ' ')
    }
}
JSON

    [[ "${status}" == "PASS" ]] && return 0 || return 1
}

#######################################
# 4. Performance Check
#######################################
qa_check_performance() {
    local context_dir="$1"

    local baseline_file="${context_dir}/.marqed/performance-baseline.json"
    local status="PASS"
    local degradation=0

    # Run pytest-benchmark if available
    if command -v pytest &>/dev/null && [[ -d "${context_dir}/tests/benchmarks" ]]; then
        local bench_output
        bench_output=$(cd "${context_dir}" && python -m pytest tests/benchmarks/ --benchmark-json=.marqed/benchmark-current.json -q 2>&1 || echo "")

        # Compare with baseline if exists
        if [[ -f "${baseline_file}" && -f "${context_dir}/.marqed/benchmark-current.json" ]]; then
            local baseline_mean
            baseline_mean=$(jq -r '.benchmarks[0].stats.mean // 0' "${baseline_file}" 2>/dev/null)
            local current_mean
            current_mean=$(jq -r '.benchmarks[0].stats.mean // 0' "${context_dir}/.marqed/benchmark-current.json" 2>/dev/null)

            if [[ "${baseline_mean}" != "0" && "${current_mean}" != "0" ]]; then
                degradation=$(echo "scale=1; (${current_mean} - ${baseline_mean}) / ${baseline_mean} * 100" | bc -l 2>/dev/null || echo "0")
            fi
        fi
    fi

    # Determine status based on degradation
    local deg_int
    deg_int=$(printf "%.0f" "${degradation}" 2>/dev/null || echo "0")

    if [[ ${deg_int} -gt ${QA_PERF_FAIL_THRESHOLD} ]]; then
        status="FAIL"
    elif [[ ${deg_int} -gt ${QA_PERF_WARN_THRESHOLD} ]]; then
        status="WARN"
    fi

    cat <<JSON
{
    "status": "${status}",
    "degradation_percent": ${degradation},
    "warn_threshold": ${QA_PERF_WARN_THRESHOLD},
    "fail_threshold": ${QA_PERF_FAIL_THRESHOLD},
    "baseline_exists": $([ -f "${baseline_file}" ] && echo "true" || echo "false")
}
JSON

    if [[ "${status}" == "FAIL" ]]; then return 2; fi
    if [[ "${status}" == "WARN" ]]; then return 1; fi
    return 0
}

#######################################
# 5. Contract Verification
#######################################
qa_check_contracts() {
    local context_dir="$1"
    local status="PASS"
    local breaking_changes=0

    # Check for changed API route files
    local api_changes
    api_changes=$(cd "${context_dir}" && git diff HEAD~1 --name-only 2>/dev/null | grep -E '(api/|routes/|endpoints/)' | wc -l | tr -d ' ')

    # Check for removed endpoints (basic pattern)
    if [[ ${api_changes} -gt 0 ]]; then
        local removed_routes
        removed_routes=$(cd "${context_dir}" && git diff HEAD~1 2>/dev/null | grep '^-.*@(app|router)\.(get|post|put|delete|patch)' | wc -l | tr -d ' ')

        if [[ ${removed_routes} -gt 0 ]]; then
            breaking_changes=$((breaking_changes + removed_routes))
        fi
    fi

    # Check for DB migration files
    local migration_changes
    migration_changes=$(cd "${context_dir}" && git diff HEAD~1 --name-only 2>/dev/null | grep -E '(migration|alembic)' | wc -l | tr -d ' ')

    # Check if migrations have downgrade
    if [[ ${migration_changes} -gt 0 ]]; then
        local new_migrations
        new_migrations=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=A 2>/dev/null | grep -E '(migration|alembic)' || echo "")

        for migration in ${new_migrations}; do
            if [[ -f "${context_dir}/${migration}" ]]; then
                if ! grep -q "def downgrade" "${context_dir}/${migration}" 2>/dev/null; then
                    echo "QA_GATE: Migration without downgrade: ${migration}"
                    breaking_changes=$((breaking_changes + 1))
                fi
            fi
        done
    fi

    if [[ ${breaking_changes} -gt 0 ]]; then
        status="FAIL"
    fi

    cat <<JSON
{
    "status": "${status}",
    "breaking_changes": ${breaking_changes},
    "api_files_changed": ${api_changes},
    "migration_files_changed": ${migration_changes}
}
JSON

    [[ "${status}" == "PASS" ]] && return 0 || return 1
}

#######################################
# 6. Dependency Impact Scan
#######################################
qa_check_dependency_impact() {
    local context_dir="$1"

    # Get changed modules
    local changed_files
    changed_files=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null || echo "")

    local affected_modules=0
    local affected_list="[]"

    # For each changed file, find importers
    for file in ${changed_files}; do
        if [[ "${file}" == *.py ]]; then
            local module_name
            module_name=$(echo "${file}" | sed 's|/|.|g' | sed 's|\.py$||')

            # Count files that import this module
            local importers
            importers=$(cd "${context_dir}" && grep -rl "import.*${module_name##*.}" --include="*.py" 2>/dev/null | grep -v "${file}" | wc -l | tr -d ' ')
            affected_modules=$((affected_modules + importers))
        fi
    done

    # Determine impact level
    local level="LOW"
    if [[ ${affected_modules} -ge ${QA_IMPACT_HIGH_THRESHOLD} ]]; then
        level="HIGH"
    elif [[ ${affected_modules} -ge ${QA_IMPACT_MEDIUM_THRESHOLD} ]]; then
        level="MEDIUM"
    fi

    cat <<JSON
{
    "level": "${level}",
    "affected_modules": ${affected_modules},
    "thresholds": {
        "medium": ${QA_IMPACT_MEDIUM_THRESHOLD},
        "high": ${QA_IMPACT_HIGH_THRESHOLD}
    }
}
JSON

    return 0
}

#######################################
# 7. Dead Code Detection
#######################################
qa_check_dead_code() {
    local context_dir="$1"
    local dead_count=0
    local dead_items="[]"

    # Check for unused imports with autoflake
    if command -v autoflake &>/dev/null; then
        local changed_py
        changed_py=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' || echo "")

        if [[ -n "${changed_py}" ]]; then
            dead_count=$(cd "${context_dir}" && echo "${changed_py}" | xargs autoflake --check 2>&1 | grep -c "unused" || echo "0")
        fi
    fi

    # Check for unused functions with vulture (if available)
    if command -v vulture &>/dev/null; then
        local vulture_count
        vulture_count=$(cd "${context_dir}" && git diff HEAD~1 --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' | xargs vulture --min-confidence 80 2>/dev/null | wc -l | tr -d ' ')
        dead_count=$((dead_count + vulture_count))
    fi

    cat <<JSON
{
    "count": ${dead_count},
    "status": "$([ ${dead_count} -eq 0 ] && echo 'CLEAN' || echo 'WARN')"
}
JSON

    return 0
}

#######################################
# Log QA review to acceptance registry
#######################################
log_qa_review() {
    local registry_db="$1"
    local md_id="$2"
    local check_type="$3"
    local status="$4"
    local score="$5"
    local details="$6"

    if [[ ! -f "${registry_db}" ]]; then
        return 0
    fi

    sqlite3 "${registry_db}" <<SQL
INSERT INTO qa_reviews (
    micro_deliverable_id, check_type, status, score, details, reviewed_at
) VALUES (
    '${md_id}', '${check_type}', '${status}', ${score:-0},
    '$(echo "${details}" | sed "s/'/''/g")', datetime('now')
);
SQL
}

#######################################
# Generate QA summary scores for registry
# Returns JSON with aggregated scores
#######################################
qa_get_summary_scores() {
    local context_dir="$1"
    local md_id="$2"

    local results_file="${context_dir}/.marqed/qa-results-${md_id}.json"

    if [[ ! -f "${results_file}" ]]; then
        echo '{"code_quality_score": 0, "security_findings": 0, "test_pass_rate": 0, "line_coverage": 0, "branch_coverage": 0, "performance_status": "PASS"}'
        return
    fi

    jq '{
        code_quality_score: (.code_quality.score // 0),
        security_findings: (.security.findings // 0),
        test_pass_rate: (.tests.test_pass_rate // 0),
        line_coverage: (.tests.line_coverage // 0),
        branch_coverage: (.tests.branch_coverage // 0),
        performance_status: (.performance.status // "PASS")
    }' "${results_file}"
}

#######################################
# Export functions for sourcing
#######################################
export -f qa_full_gate
export -f qa_check_code_quality
export -f qa_check_security
export -f qa_check_tests_coverage
export -f qa_check_performance
export -f qa_check_contracts
export -f qa_check_dependency_impact
export -f qa_check_dead_code
export -f log_qa_review
export -f qa_get_summary_scores

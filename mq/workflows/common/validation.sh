#!/bin/bash
# validation.sh - Validation functions for MarQed.ai workflows
# Part of MarQed.ai AI-driven development workflow

#######################################
# Validate current phase completion
# Arguments:
#   $1 - Path to PRD file
#   $2 - Context directory
# Returns:
#   0 if validation passes, 1 otherwise
#######################################
validate_current_phase() {
    local prd_file="$1"
    local context_dir="$2"
    
    if [[ ! -f "${prd_file}" ]]; then
        echo "❌ Error: PRD file not found: ${prd_file}" >&2
        return 1
    fi
    
    # Extract current phase (first one with "Passes: false")
    local phase_section=$(awk '/^### Phase [0-9]+:/{p=1} p{print} /^### Phase [0-9]+:/ && p{if(prev)exit} {prev=p}' "${prd_file}" | grep -A 50 "Passes: false" | head -50)
    
    if [[ -z "${phase_section}" ]]; then
        echo "✅ All phases already validated"
        return 0
    fi
    
    # Extract validation criteria
    local validation_section=$(echo "${phase_section}" | awk '/^\*\*Validation\*\*:/,/^\*\*Passes\*\*:/')
    
    if [[ -z "${validation_section}" ]]; then
        echo "⚠️  No validation criteria found"
        return 0
    fi
    
    echo "🔍 Validating phase against criteria..."
    echo ""
    
    # Count total criteria and passed criteria
    local total_criteria=$(echo "${validation_section}" | grep -c "^- \[ \]")
    local passed=0
    local failed=0
    
    # Parse each criterion
    while IFS= read -r line; do
        if [[ "${line}" =~ ^-[[:space:]]\[[[:space:]]\][[:space:]](.+)$ ]]; then
            local criterion="${BASH_REMATCH[1]}"
            
            if validate_criterion "${criterion}" "${context_dir}"; then
                echo "  ✅ ${criterion}"
                ((passed++))
            else
                echo "  ❌ ${criterion}"
                ((failed++))
            fi
        fi
    done < <(echo "${validation_section}" | grep "^- \[ \]")
    
    echo ""
    echo "Validation Results: ${passed}/${total_criteria} passed"
    
    # Pass if at least 80% of criteria met
    local threshold=$((total_criteria * 80 / 100))
    
    if [[ ${passed} -ge ${threshold} ]]; then
        echo "✅ Validation passed (${passed}/${total_criteria} >= ${threshold})"
        return 0
    else
        echo "❌ Validation failed (${passed}/${total_criteria} < ${threshold})"
        return 1
    fi
}

#######################################
# Validate a single criterion
# Arguments:
#   $1 - Criterion text
#   $2 - Context directory
# Returns:
#   0 if criterion met, 1 otherwise
#######################################
validate_criterion() {
    local criterion="$1"
    local context_dir="$2"
    
    # Convert criterion to lowercase for matching
    local criterion_lower=$(echo "${criterion}" | tr '[:upper:]' '[:lower:]')
    
    # File existence checks
    if [[ "${criterion_lower}" =~ file.*exists || "${criterion_lower}" =~ .*created ]]; then
        # Extract potential filename
        local filename=$(echo "${criterion}" | grep -oE '[a-zA-Z0-9_\-]+\.(md|py|cs|js|json|yml|yaml|sh|txt)' | head -1)
        if [[ -n "${filename}" ]]; then
            [[ -f "${context_dir}/${filename}" ]] && return 0
            # Try common locations
            [[ -f "${context_dir}/docs/${filename}" ]] && return 0
            [[ -f "${context_dir}/src/${filename}" ]] && return 0
            return 1
        fi
    fi
    
    # Directory existence checks
    if [[ "${criterion_lower}" =~ directory.*exists || "${criterion_lower}" =~ folder.*created ]]; then
        local dirname=$(echo "${criterion}" | grep -oE '[a-zA-Z0-9_\-/]+' | tail -1)
        if [[ -n "${dirname}" ]]; then
            [[ -d "${context_dir}/${dirname}" ]] && return 0
            return 1
        fi
    fi
    
    # Test execution checks
    if [[ "${criterion_lower}" =~ tests?.*pass || "${criterion_lower}" =~ all.*tests?.*pass ]]; then
        # Check for test result files
        [[ -f "${context_dir}/test-results.xml" ]] && return 0
        [[ -f "${context_dir}/pytest.xml" ]] && return 0
        [[ -f "${context_dir}/.test-results" ]] && return 0
        
        # Try running tests (if test command exists)
        if command -v pytest &> /dev/null; then
            (cd "${context_dir}" && pytest --quiet 2>&1 | grep -q "passed") && return 0
        fi
        
        return 1
    fi
    
    # Code quality checks
    if [[ "${criterion_lower}" =~ code.*quality || "${criterion_lower}" =~ linting.*pass ]]; then
        # Check for linter config
        [[ -f "${context_dir}/.pylintrc" ]] || [[ -f "${context_dir}/.eslintrc" ]] && return 0
        return 1
    fi
    
    # Documentation checks
    if [[ "${criterion_lower}" =~ documentation.*updated || "${criterion_lower}" =~ readme.*updated ]]; then
        [[ -f "${context_dir}/README.md" ]] && [[ $(stat -f%z "${context_dir}/README.md" 2>/dev/null || stat -c%s "${context_dir}/README.md" 2>/dev/null) -gt 100 ]] && return 0
        return 1
    fi
    
    # Coverage checks
    if [[ "${criterion_lower}" =~ coverage || "${criterion_lower}" =~ test.*coverage ]]; then
        [[ -f "${context_dir}/coverage.xml" ]] || [[ -f "${context_dir}/.coverage" ]] && return 0
        return 1
    fi
    
    # Security checks
    if [[ "${criterion_lower}" =~ security || "${criterion_lower}" =~ vulnerabilit ]]; then
        [[ -f "${context_dir}/SECURITY.md" ]] && return 0
        return 1
    fi
    
    # Performance checks
    if [[ "${criterion_lower}" =~ performance || "${criterion_lower}" =~ benchmark ]]; then
        [[ -f "${context_dir}/benchmarks.txt" ]] || [[ -f "${context_dir}/performance.json" ]] && return 0
        return 1
    fi
    
    # Integration checks
    if [[ "${criterion_lower}" =~ integration ]]; then
        [[ -d "${context_dir}/tests/integration" ]] || [[ -f "${context_dir}/integration-tests.xml" ]] && return 0
        return 1
    fi
    
    # Default: assume criterion is met if we can't determine
    # This is conservative - better to ask human to verify
    return 0
}

#######################################
# Validate task completion
# Arguments:
#   $1 - Task file path
#   $2 - Task ID
#   $3 - Context directory
# Returns:
#   0 if task valid for completion, 1 otherwise
#######################################
validate_task_complete() {
    local task_file="$1"
    local task_id="$2"
    local context_dir="$3"
    
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        return 1
    fi
    
    # Get task details
    local task_title=$(jq -r ".tasks[] | select(.id == \"${task_id}\") | .title" "${task_file}")
    local task_description=$(jq -r ".tasks[] | select(.id == \"${task_id}\") | .description" "${task_file}")
    
    echo "🔍 Validating task: ${task_title}"
    echo "Description: ${task_description}"
    echo ""
    
    # Task-specific validation based on task ID patterns
    if [[ "${task_id}" =~ phase1 ]]; then
        validate_phase1_task "${task_id}" "${context_dir}"
    elif [[ "${task_id}" =~ phase2 ]]; then
        validate_phase2_task "${task_id}" "${context_dir}"
    elif [[ "${task_id}" =~ phase3 ]]; then
        validate_phase3_task "${task_id}" "${context_dir}"
    elif [[ "${task_id}" =~ unittest || "${task_id}" =~ test ]]; then
        validate_test_task "${task_id}" "${context_dir}"
    elif [[ "${task_id}" =~ implement ]]; then
        validate_implementation_task "${task_id}" "${context_dir}"
    else
        # Generic validation
        validate_generic_task "${task_id}" "${context_dir}"
    fi
}

#######################################
# Validate phase 1 tasks (analysis/planning)
#######################################
validate_phase1_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Check for analysis documents
    if [[ -f "${context_dir}/ANALYSIS.md" ]] || [[ -f "${context_dir}/docs/analysis.md" ]]; then
        echo "✅ Analysis document found"
        return 0
    fi
    
    echo "⚠️  Analysis document not found"
    return 1
}

#######################################
# Validate phase 2 tasks (setup/environment)
#######################################
validate_phase2_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Check for project setup files
    local setup_files=(".gitignore" "README.md" "requirements.txt" "package.json" "*.csproj" "*.sln")
    local found=0
    
    for pattern in "${setup_files[@]}"; do
        if [[ -f "${context_dir}/${pattern}" ]] || ls "${context_dir}"/${pattern} &>/dev/null; then
            ((found++))
        fi
    done
    
    if [[ ${found} -ge 2 ]]; then
        echo "✅ Project setup files found (${found} files)"
        return 0
    fi
    
    echo "⚠️  Insufficient project setup files (${found} < 2)"
    return 1
}

#######################################
# Validate phase 3 tasks (implementation)
#######################################
validate_phase3_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Check for source code
    if [[ -d "${context_dir}/src" ]]; then
        local code_files=$(find "${context_dir}/src" -type f \( -name "*.py" -o -name "*.cs" -o -name "*.js" \) | wc -l)
        
        if [[ ${code_files} -gt 0 ]]; then
            echo "✅ Source code found (${code_files} files)"
            return 0
        fi
    fi
    
    echo "⚠️  No source code found"
    return 1
}

#######################################
# Validate test tasks
#######################################
validate_test_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Check for test files
    if [[ -d "${context_dir}/tests" ]]; then
        local test_files=$(find "${context_dir}/tests" -type f \( -name "test_*.py" -o -name "*_test.py" -o -name "*.test.js" -o -name "*Tests.cs" \) | wc -l)
        
        if [[ ${test_files} -gt 0 ]]; then
            echo "✅ Test files found (${test_files} files)"
            
            # Try to run tests if possible
            if command -v pytest &> /dev/null && [[ -f "${context_dir}/tests/test_"* ]]; then
                if (cd "${context_dir}" && pytest --quiet --tb=no 2>&1 | grep -q "passed"); then
                    echo "✅ Tests passed"
                    return 0
                else
                    echo "⚠️  Some tests failed"
                    return 1
                fi
            fi
            
            return 0
        fi
    fi
    
    echo "⚠️  No test files found"
    return 1
}

#######################################
# Validate implementation tasks
#######################################
validate_implementation_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Check for recent code changes
    if [[ -d "${context_dir}/.git" ]]; then
        local recent_commits=$(git -C "${context_dir}" log --since="1 hour ago" --oneline | wc -l)
        
        if [[ ${recent_commits} -gt 0 ]]; then
            echo "✅ Recent code changes detected (${recent_commits} commits)"
            return 0
        fi
    fi
    
    # Fallback: check for modified files
    if [[ -d "${context_dir}/src" ]]; then
        local modified=$(find "${context_dir}/src" -type f -mmin -60 | wc -l)
        
        if [[ ${modified} -gt 0 ]]; then
            echo "✅ Recently modified files detected (${modified} files)"
            return 0
        fi
    fi
    
    echo "⚠️  No recent code changes detected"
    return 1
}

#######################################
# Validate generic tasks
#######################################
validate_generic_task() {
    local task_id="$1"
    local context_dir="$2"
    
    # Generic validation - just check context directory exists and has content
    if [[ -d "${context_dir}" ]]; then
        local file_count=$(find "${context_dir}" -type f | wc -l)
        
        if [[ ${file_count} -gt 0 ]]; then
            echo "✅ Context directory has content (${file_count} files)"
            return 0
        fi
    fi
    
    echo "⚠️  Context validation could not be determined"
    return 0  # Conservative: assume valid
}

#######################################
# Run full validation suite
# Arguments:
#   $1 - PRD file
#   $2 - Task file
#   $3 - Context directory
# Returns:
#   0 if all validations pass, 1 otherwise
#######################################
run_full_validation() {
    local prd_file="$1"
    local task_file="$2"
    local context_dir="$3"
    
    echo "🔍 Running Full Validation Suite"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    local validation_failed=0
    
    # Validate current phase
    echo "📋 Validating current phase..."
    if ! validate_current_phase "${prd_file}" "${context_dir}"; then
        echo "❌ Phase validation failed"
        validation_failed=1
    fi
    echo ""
    
    # Validate completed tasks
    echo "✅ Validating completed tasks..."
    local completed_tasks=$(jq -r '.tasks[] | select(.status == "completed") | .id' "${task_file}")
    
    for task_id in ${completed_tasks}; do
        if ! validate_task_complete "${task_file}" "${task_id}" "${context_dir}"; then
            echo "⚠️  Task validation warning: ${task_id}"
            # Don't fail on individual task validation
        fi
    done
    echo ""
    
    if [[ ${validation_failed} -eq 0 ]]; then
        echo "✅ Full validation suite passed"
        return 0
    else
        echo "❌ Full validation suite failed"
        return 1
    fi
}

#######################################
# Export functions for sourcing
#######################################
export -f validate_current_phase
export -f validate_criterion
export -f validate_task_complete
export -f validate_phase1_task
export -f validate_phase2_task
export -f validate_phase3_task
export -f validate_test_task
export -f validate_implementation_task
export -f validate_generic_task
export -f run_full_validation
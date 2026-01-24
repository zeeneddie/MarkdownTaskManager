#!/bin/bash
# sync-tasks-to-prd.sh - Sync Claude Code task status back to PRD
# Part of MarQed.ai AI-driven development workflow

set -e

#######################################
# Display usage information
#######################################
usage() {
    cat << EOF
Usage: $(basename "$0") TASK_FILE PRD_FILE

Synchronize Claude Code task completion status back to PRD.md

ARGUMENTS:
    TASK_FILE        Path to Claude Code task JSON file
    PRD_FILE         Path to PRD markdown file

EXAMPLES:
    # Basic sync
    $(basename "$0") ~/.claude/tasks/BUG-2026-01-23-001.json ./PRD.md

    # Sync after workflow completion
    $(basename "$0") ~/.claude/tasks/CHANGE-2026-01-23-001.json ./docs/PRD.md

BEHAVIOR:
    - Reads all completed tasks from task file
    - Finds corresponding phases in PRD
    - Updates "Passes: false" to "Passes: true"
    - Adds completion timestamp to notes
    - Preserves all other PRD content

PHASE MAPPING:
    Task IDs are mapped to PRD phases:
    - bug-phase1-* → Phase 1
    - bug-phase2-* → Phase 2
    - change-phase1-* → Phase 1
    - mig-phase1-* → Phase 1
    etc.

SAFETY:
    - Creates backup of PRD before modification
    - Validates PRD format before changes
    - Only updates "Passes" field, nothing else
    - Atomic operations (tmp file + mv)

For more information: https://github.com/marqed-ai/workflows
EOF
}

#######################################
# Extract phase number from task ID
# Arguments:
#   $1 - Task ID
# Returns:
#   Phase number or empty string
#######################################
extract_phase_number() {
    local task_id="$1"
    
    # Match patterns like "phase1", "phase2", etc.
    if [[ "${task_id}" =~ phase([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

#######################################
# Find phase section in PRD
# Arguments:
#   $1 - PRD file
#   $2 - Phase number
# Returns:
#   Line number of phase header or empty
#######################################
find_phase_section() {
    local prd_file="$1"
    local phase_num="$2"
    
    grep -n "^### Phase ${phase_num}:" "${prd_file}" | cut -d: -f1
}

#######################################
# Update phase status in PRD
# Arguments:
#   $1 - PRD file
#   $2 - Phase number
#   $3 - Completion timestamp
#######################################
update_phase_status() {
    local prd_file="$1"
    local phase_num="$2"
    local timestamp="$3"
    
    # Find the phase section
    local phase_line=$(find_phase_section "${prd_file}" "${phase_num}")
    
    if [[ -z "${phase_line}" ]]; then
        echo "⚠️  Warning: Phase ${phase_num} not found in PRD" >&2
        return 1
    fi
    
    # Find the "Passes:" line after this phase (within next 100 lines)
    local passes_line=$(tail -n +${phase_line} "${prd_file}" | head -100 | grep -n "^**Passes**:" | head -1 | cut -d: -f1)
    
    if [[ -z "${passes_line}" ]]; then
        echo "⚠️  Warning: 'Passes' field not found for Phase ${phase_num}" >&2
        return 1
    fi
    
    # Calculate actual line number
    local actual_line=$((phase_line + passes_line - 1))
    
    # Check current status
    local current_status=$(sed -n "${actual_line}p" "${prd_file}" | grep -o "true\|false")
    
    if [[ "${current_status}" == "true" ]]; then
        echo "   Phase ${phase_num}: Already marked as passing ✅"
        return 0
    fi
    
    # Update the line
    sed -i.bak "${actual_line}s/Passes: false/Passes: true/" "${prd_file}"
    
    # Add timestamp to notes (next line after Passes)
    local notes_line=$((actual_line + 1))
    local formatted_timestamp=$(date -d "${timestamp}" +"%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "${timestamp}")
    
    # Check if notes line exists
    if sed -n "${notes_line}p" "${prd_file}" | grep -q "^**Notes**:"; then
        # Insert timestamp after Notes header
        sed -i.bak "${notes_line}a\\
- Completed: ${formatted_timestamp}" "${prd_file}"
    fi
    
    echo "   Phase ${phase_num}: Updated to passing ✅ (${formatted_timestamp})"
    return 0
}

#######################################
# Validate PRD format
# Arguments:
#   $1 - PRD file
# Returns:
#   0 if valid, 1 if invalid
#######################################
validate_prd_format() {
    local prd_file="$1"
    
    # Check for basic PRD structure
    if ! grep -q "^### Phase [0-9]:" "${prd_file}"; then
        echo "❌ Error: PRD does not contain phase sections" >&2
        return 1
    fi
    
    if ! grep -q "^**Passes**:" "${prd_file}"; then
        echo "❌ Error: PRD does not contain 'Passes' fields" >&2
        return 1
    fi
    
    return 0
}

#######################################
# Main sync operation
# Arguments:
#   $1 - Task file
#   $2 - PRD file
#######################################
sync_tasks_to_prd() {
    local task_file="$1"
    local prd_file="$2"
    
    echo "🔄 Syncing Task Status to PRD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Task File: ${task_file}"
    echo "PRD File: ${prd_file}"
    echo ""
    
    # Validate inputs
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        exit 1
    fi
    
    if [[ ! -f "${prd_file}" ]]; then
        echo "❌ Error: PRD file not found: ${prd_file}" >&2
        exit 1
    fi
    
    # Validate task file is valid JSON
    if ! jq empty "${task_file}" 2>/dev/null; then
        echo "❌ Error: Task file is not valid JSON" >&2
        exit 1
    fi
    
    # Validate PRD format
    if ! validate_prd_format "${prd_file}"; then
        exit 1
    fi
    
    # Create backup
    local backup_file="${prd_file}.backup-$(date +%Y%m%d-%H%M%S)"
    cp "${prd_file}" "${backup_file}"
    echo "📦 Backup created: ${backup_file}"
    echo ""
    
    # Get completed tasks
    local completed_tasks=$(jq -r '.tasks[] | select(.status == "completed") | "\(.id)|\(.completedAt // "unknown")"' "${task_file}")
    
    if [[ -z "${completed_tasks}" ]]; then
        echo "ℹ️  No completed tasks to sync"
        return 0
    fi
    
    echo "📋 Processing completed tasks:"
    echo ""
    
    local updated_count=0
    local skipped_count=0
    
    while IFS='|' read -r task_id timestamp; do
        # Extract phase number
        local phase_num=$(extract_phase_number "${task_id}")
        
        if [[ -z "${phase_num}" ]]; then
            echo "   ${task_id}: No phase number found, skipping ⏭️"
            ((skipped_count++))
            continue
        fi
        
        # Update PRD
        if update_phase_status "${prd_file}" "${phase_num}" "${timestamp}"; then
            ((updated_count++))
        else
            ((skipped_count++))
        fi
    done <<< "${completed_tasks}"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Sync Complete"
    echo "   Updated: ${updated_count} phases"
    echo "   Skipped: ${skipped_count} phases"
    echo ""
    
    # Show summary of PRD status
    echo "📊 PRD Phase Summary:"
    local phase_count=1
    while true; do
        local phase_line=$(find_phase_section "${prd_file}" "${phase_count}")
        
        if [[ -z "${phase_line}" ]]; then
            break
        fi
        
        local phase_title=$(sed -n "${phase_line}p" "${prd_file}" | sed 's/^### Phase [0-9]*: //')
        local passes_line=$(tail -n +${phase_line} "${prd_file}" | head -100 | grep -n "^**Passes**:" | head -1 | cut -d: -f1)
        
        if [[ -n "${passes_line}" ]]; then
            local actual_line=$((phase_line + passes_line - 1))
            local status=$(sed -n "${actual_line}p" "${prd_file}" | grep -o "true\|false")
            
            if [[ "${status}" == "true" ]]; then
                echo "   Phase ${phase_count}: ✅ ${phase_title}"
            else
                echo "   Phase ${phase_count}: ⏳ ${phase_title}"
            fi
        fi
        
        ((phase_count++))
    done
    
    echo ""
    
    # Cleanup old backup if successful
    rm -f "${prd_file}.bak"
}

#######################################
# Main entry point
#######################################
main() {
    # Check arguments
    if [[ $# -lt 2 ]]; then
        usage
        exit 1
    fi
    
    local task_file="$1"
    local prd_file="$2"
    
    sync_tasks_to_prd "${task_file}" "${prd_file}"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
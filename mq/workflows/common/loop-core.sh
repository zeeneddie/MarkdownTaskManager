#!/bin/bash
# loop-core.sh - Core loop functions for MarQed.ai workflows
# Version 2.1 - With checkpointing, error recovery, and diagnostics

#######################################
# Check if all tasks are completed
#######################################
check_tasks_complete() {
    local task_file="$1"
    
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        return 1
    fi
    
    local pending=$(jq '[.tasks[] | select(.status == "pending" or .status == "in_progress")] | length' "${task_file}")
    
    [[ ${pending} -eq 0 ]]
}

#######################################
# Get next available task
#######################################
get_next_task() {
    local task_file="$1"
    
    if [[ ! -f "${task_file}" ]]; then
        return 1
    fi
    
    # Get first pending task without blockers
    jq -r '.tasks[] | select(.status == "pending") | 
           select(.dependencies == [] or 
                  all(.dependencies[]; . as $dep | 
                      any($dep; IN(.tasks[] | select(.status == "completed") | .id)))) | 
           .title' "${task_file}" | head -1
}

#######################################
# Get current phase number
#######################################
get_current_phase_number() {
    local task_file="$1"
    
    # Get phase of first non-completed task
    jq -r '.tasks[] | select(.status != "completed") | .phase' "${task_file}" | head -1
}

#######################################
# Update PRD phase status
#######################################
update_prd_phase_status() {
    local prd_file="$1"
    local phase_number="$2"
    local passes="$3"
    
    if [[ ! -f "${prd_file}" ]]; then
        echo "⚠️  Warning: PRD file not found: ${prd_file}"
        return 1
    fi
    
    # Update phase validation status in PRD
    # This is a simplified version - actual implementation may need more sophistication
    sed -i "s/Phase ${phase_number}.*Passes: false/Phase ${phase_number} - Passes: ${passes}/" "${prd_file}"
}

#######################################
# Sync tasks back to PRD
#######################################
sync_tasks_to_prd() {
    local task_file="$1"
    local prd_file="$2"
    
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        return 1
    fi
    
    if [[ ! -f "${prd_file}" ]]; then
        echo "⚠️  Warning: PRD file not found: ${prd_file}"
        return 1
    fi
    
    echo "Syncing task status back to PRD..."
    
    # Extract completed phases
    local completed_phases=$(jq -r '.tasks[] | select(.status == "completed") | .phase' "${task_file}" | sort -u)
    
    # Mark phases as complete in PRD
    for phase in ${completed_phases}; do
        update_prd_phase_status "${prd_file}" "${phase}" "true"
    done
    
    echo "✅ PRD updated with task completion status"
}

#######################################
# Spawn parallel Claude Code sessions
#######################################
spawn_parallel_sessions() {
    local id="$1"
    local context_dir1="$2"
    local context_dir2="$3"
    local prompt_file="$4"
    local num_parallel="$5"
    local log_file="$6"
    
    echo "🔀 Spawning ${num_parallel} parallel sessions..."
    
    local pids=()
    
    for i in $(seq 1 ${num_parallel}); do
        local session_log="${log_file%.log}-session-${i}.log"
        
        echo "  Starting session ${i}..."
        
        # Run Claude Code in background
        claude-code \
            --task-list "${id}" \
            --context "${context_dir1}" \
            --context "${context_dir2}" \
            --prompt "$(cat ${prompt_file})" \
            > "${session_log}" 2>&1 &
        
        pids+=($!)
    done
    
    echo "  Waiting for all sessions to complete..."
    
    # Wait for all background jobs
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait ${pid}; then
            failed=$((failed + 1))
        fi
    done
    
    if [[ ${failed} -gt 0 ]]; then
        echo "⚠️  ${failed} parallel sessions failed"
        return 1
    fi
    
    echo "✅ All parallel sessions completed successfully"
    return 0
}

#######################################
# Save workflow checkpoint
#######################################
save_checkpoint() {
    local workflow_id="$1"
    local current_phase="$2"
    local state_dir="${HOME}/.marqed/state/${workflow_id}"
    
    mkdir -p "${state_dir}/checkpoint"
    
    # Save current phase
    echo "${current_phase}" > "${state_dir}/last_completed_phase.txt"
    
    # Save iteration number (from global scope if available)
    if [[ -n "${iteration}" ]]; then
        echo "${iteration}" > "${state_dir}/last_iteration.txt"
    fi
    
    # Copy results
    if [[ -d "${HOME}/.marqed/results/${workflow_id}" ]]; then
        rsync -a --delete \
            "${HOME}/.marqed/results/${workflow_id}/" \
            "${state_dir}/checkpoint/results/" \
            2>/dev/null || true
    fi
    
    # Copy task file
    if [[ -f "${HOME}/.claude/tasks/${workflow_id}.json" ]]; then
        cp "${HOME}/.claude/tasks/${workflow_id}.json" \
           "${state_dir}/checkpoint/tasks.json"
    fi
    
    # Copy logs
    if [[ -d "${HOME}/.marqed/logs/${workflow_id}" ]]; then
        rsync -a --delete \
            "${HOME}/.marqed/logs/${workflow_id}/" \
            "${state_dir}/checkpoint/logs/" \
            2>/dev/null || true
    fi
    
    # Save timestamp
    date -Iseconds > "${state_dir}/checkpoint/timestamp.txt"
    
    echo "💾 Checkpoint saved (phase: ${current_phase})"
}

#######################################
# Load workflow checkpoint
#######################################
load_checkpoint() {
    local workflow_id="$1"
    local state_dir="${HOME}/.marqed/state/${workflow_id}"
    
    if [[ ! -f "${state_dir}/last_completed_phase.txt" ]]; then
        return 1
    fi
    
    echo "🔄 Checkpoint found!"
    
    local last_phase=$(cat "${state_dir}/last_completed_phase.txt")
    local last_iteration=0
    local checkpoint_time="unknown"
    
    if [[ -f "${state_dir}/last_iteration.txt" ]]; then
        last_iteration=$(cat "${state_dir}/last_iteration.txt")
    fi
    
    if [[ -f "${state_dir}/checkpoint/timestamp.txt" ]]; then
        checkpoint_time=$(cat "${state_dir}/checkpoint/timestamp.txt")
    fi
    
    echo "   Last completed phase: ${last_phase}"
    echo "   Last iteration: ${last_iteration}"
    echo "   Checkpoint time: ${checkpoint_time}"
    echo ""
    
    # Calculate time since checkpoint
    if [[ "${checkpoint_time}" != "unknown" ]]; then
        local checkpoint_epoch=$(date -d "${checkpoint_time}" +%s 2>/dev/null || echo 0)
        local current_epoch=$(date +%s)
        local elapsed=$((current_epoch - checkpoint_epoch))
        local hours=$((elapsed / 3600))
        local mins=$(((elapsed % 3600) / 60))
        
        echo "   Time since checkpoint: ${hours}h ${mins}m ago"
        echo ""
    fi
    
    read -p "Resume from checkpoint? (y/n): " resume
    
    if [[ "${resume}" != "y" ]]; then
        echo "Starting fresh..."
        return 1
    fi
    
    # Restore results
    if [[ -d "${state_dir}/checkpoint/results" ]]; then
        mkdir -p "${HOME}/.marqed/results/${workflow_id}"
        rsync -a \
            "${state_dir}/checkpoint/results/" \
            "${HOME}/.marqed/results/${workflow_id}/"
        echo "   ✅ Results restored"
    fi
    
    # Restore task file
    if [[ -f "${state_dir}/checkpoint/tasks.json" ]]; then
        mkdir -p "${HOME}/.claude/tasks"
        cp "${state_dir}/checkpoint/tasks.json" \
           "${HOME}/.claude/tasks/${workflow_id}.json"
        echo "   ✅ Tasks restored"
    fi
    
    # Restore logs
    if [[ -d "${state_dir}/checkpoint/logs" ]]; then
        mkdir -p "${HOME}/.marqed/logs/${workflow_id}"
        rsync -a \
            "${state_dir}/checkpoint/logs/" \
            "${HOME}/.marqed/logs/${workflow_id}/"
        echo "   ✅ Logs restored"
    fi
    
    echo ""
    echo "✅ Checkpoint restored successfully"
    
    return 0
}

#######################################
# Clear checkpoint
#######################################
clear_checkpoint() {
    local workflow_id="$1"
    local state_dir="${HOME}/.marqed/state/${workflow_id}"
    
    if [[ -d "${state_dir}/checkpoint" ]]; then
        rm -rf "${state_dir}/checkpoint"
        rm -f "${state_dir}/last_completed_phase.txt"
        rm -f "${state_dir}/last_iteration.txt"
        echo "🗑️  Checkpoint cleared"
    fi
}

#######################################
# Diagnose workflow failure
#######################################
diagnose_failure() {
    local exit_code="$1"
    local log_file="$2"
    local workflow_type="$3"
    
    echo ""
    echo "❌ Workflow failed with exit code: ${exit_code}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [[ ! -f "${log_file}" ]]; then
        echo "⚠️  Log file not found: ${log_file}"
        echo "Cannot provide detailed diagnostics without log file."
        return 1
    fi
    
    # Check for rate limiting
    if grep -qi "rate limit\|too many requests\|429" "${log_file}"; then
        echo "🚫 RATE LIMIT DETECTED"
        echo ""
        echo "Cause: Too many API requests to Claude"
        echo ""
        echo "Solutions:"
        echo "  1. Wait 60 seconds and retry with --resume flag"
        echo "  2. Reduce --max-iter if running too many iterations"
        echo "  3. Use --parallel with lower number"
        echo ""
        echo "Command to resume:"
        echo "  $(basename "$0") --resume"
        echo ""
        return 1
    fi
    
    # Check for timeout
    if grep -qi "timeout\|timed out" "${log_file}"; then
        echo "⏱️  TIMEOUT DETECTED"
        echo ""
        echo "Cause: Operation took longer than expected"
        echo ""
        echo "Solutions:"
        echo "  1. Check network connection"
        echo "  2. Increase timeout with --timeout flag (if available)"
        echo "  3. Use --resume to continue from last checkpoint"
        echo "  4. Check if Claude is stuck (review last lines of log)"
        echo ""
        return 1
    fi
    
    # Check for missing tools
    if grep -q "command not found\|not found" "${log_file}"; then
        local missing_tool=$(grep "not found" "${log_file}" | head -1 | awk '{print $1}')
        echo "🔧 MISSING TOOL: ${missing_tool}"
        echo ""
        echo "Cause: Required tool not installed"
        echo ""
        echo "Solution:"
        
        case "${missing_tool}" in
            pylint|flake8|bandit|radon)
                echo "  pip install --break-system-packages ${missing_tool}"
                ;;
            dotnet)
                echo "  Install .NET SDK from https://dotnet.microsoft.com/"
                ;;
            jq)
                echo "  # Ubuntu/Debian:"
                echo "  sudo apt-get install jq"
                echo ""
                echo "  # macOS:"
                echo "  brew install jq"
                ;;
            python3)
                echo "  # Ubuntu/Debian:"
                echo "  sudo apt-get install python3"
                echo ""
                echo "  # macOS:"
                echo "  brew install python3"
                ;;
            rsync)
                echo "  # Ubuntu/Debian:"
                echo "  sudo apt-get install rsync"
                echo ""
                echo "  # macOS (usually pre-installed)"
                ;;
            *)
                echo "  Install ${missing_tool} using your package manager"
                echo "  Or check documentation for ${workflow_type} workflow"
                ;;
        esac
        echo ""
        return 1
    fi
    
    # Check for validation failures
    if grep -q "Validation failed\|validation error" "${log_file}"; then
        echo "✅ VALIDATION FAILURE"
        echo ""
        echo "Cause: Phase validation did not pass"
        echo ""
        echo "This usually means:"
        echo "  - Expected files were not created"
        echo "  - Tests did not pass"
        echo "  - Quality checks failed"
        echo ""
        echo "Solutions:"
        echo "  1. Check validation criteria in PRD.md"
        echo "  2. Review last Claude Code session output"
        echo "  3. May need manual intervention to fix issues"
        echo "  4. Use --resume after fixing issues"
        echo ""
        
        # Show last validation error
        echo "Last validation error:"
        grep -A 5 "Validation failed" "${log_file}" | tail -6
        echo ""
        return 1
    fi
    
    # Check for disk space
    if grep -qi "no space left\|disk full" "${log_file}"; then
        echo "💾 DISK SPACE ISSUE"
        echo ""
        echo "Cause: Insufficient disk space"
        echo ""
        echo "Solutions:"
        echo "  1. Free up disk space"
        echo "  2. Check current usage: df -h"
        echo "  3. Clean old results: rm -rf ~/.marqed/results/old-*"
        echo "  4. Clean checkpoints: rm -rf ~/.marqed/state/*/checkpoint"
        echo "  5. Clean logs: find ~/.marqed/logs -mtime +30 -delete"
        echo ""
        
        # Show current disk usage
        echo "Current disk usage:"
        df -h ~ | tail -1
        echo ""
        return 1
    fi
    
    # Check for permission errors
    if grep -qi "permission denied\|access denied" "${log_file}"; then
        echo "🔐 PERMISSION ERROR"
        echo ""
        echo "Cause: Insufficient permissions"
        echo ""
        echo "Solutions:"
        echo "  1. Check file/directory permissions"
        echo "  2. Ensure you own the directories"
        echo "  3. Check: ls -la ~/.marqed"
        echo ""
        return 1
    fi
    
    # Check for Claude API errors
    if grep -qi "api error\|authentication failed\|invalid api key" "${log_file}"; then
        echo "🔑 API AUTHENTICATION ERROR"
        echo ""
        echo "Cause: Claude API authentication issue"
        echo ""
        echo "Solutions:"
        echo "  1. Verify Claude API key is set"
        echo "  2. Check: claude-code --version"
        echo "  3. Re-authenticate if needed"
        echo ""
        return 1
    fi
    
    # Generic failure - show context
    echo "❓ GENERIC FAILURE"
    echo ""
    echo "Exit code: ${exit_code}"
    echo "Workflow: ${workflow_type}"
    echo ""
    echo "Last 30 lines of log:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -30 "${log_file}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Full log: ${log_file}"
    echo ""
    echo "For support, provide:"
    echo "  1. Workflow type: ${workflow_type}"
    echo "  2. Exit code: ${exit_code}"
    echo "  3. Last 50 lines: tail -50 ${log_file}"
    echo "  4. Task status: cat ~/.claude/tasks/${CLAUDE_CODE_TASK_LIST_ID}.json"
    echo ""
    
    return 1
}

# Export all functions
export -f check_tasks_complete
export -f get_next_task
export -f get_current_phase_number
export -f update_prd_phase_status
export -f sync_tasks_to_prd
export -f spawn_parallel_sessions
export -f save_checkpoint
export -f load_checkpoint
export -f clear_checkpoint
export -f diagnose_failure
#!/bin/bash
# spawn-parallel-sessions.sh - Spawn multiple parallel Claude Code sessions
# Part of MarQed.ai AI-driven development workflow

set -e

#######################################
# Display usage information
#######################################
usage() {
    cat << EOF
Usage: $(basename "$0") TASK_ID CONTEXT_DIR PROMPT_FILE NUM_SESSIONS MAX_ITERATIONS

Spawn multiple parallel Claude Code sessions for concurrent task execution

ARGUMENTS:
    TASK_ID          Task list ID (shared across all sessions)
    CONTEXT_DIR      Context directory for code
    PROMPT_FILE      Prompt file for Claude Code
    NUM_SESSIONS     Number of parallel sessions to spawn
    MAX_ITERATIONS   Maximum iterations per session

EXAMPLES:
    # Spawn 3 parallel sessions
    $(basename "$0") CHANGE-2026-01-23-001 ./src prompt.md 3 30

    # Spawn 5 parallel sessions for large project
    $(basename "$0") CHANGE-2026-01-23-001 ./src prompt.md 5 50

BEHAVIOR:
    - All sessions share the same task list (TASK_ID)
    - Each session picks available parallelizable tasks
    - Coordination happens through task status updates
    - Sessions exit when no more tasks available
    - Parent waits for all sessions to complete

SESSION MANAGEMENT:
    - Each session logs to a separate file
    - Session IDs: A, B, C, D, E, ...
    - Logs: ~/.marqed/logs/${TASK_ID}/session-[A-Z].log
    - PIDs tracked for monitoring

TASK COORDINATION:
    - Sessions check for available tasks
    - Prefer tasks marked "parallelizable: true"
    - Avoid tasks already "in_progress" by other sessions
    - Update status to "in_progress" when starting
    - Update to "completed" when done

For more information: https://github.com/marqed-ai/workflows
EOF
}

#######################################
# Run a single Claude Code session
# Arguments:
#   $1 - Session ID (A, B, C, ...)
#   $2 - Task ID
#   $3 - Context directory
#   $4 - Prompt file
#   $5 - Max iterations
#######################################
run_session() {
    local session_id="$1"
    local task_id="$2"
    local context_dir="$3"
    local prompt_file="$4"
    local max_iterations="$5"
    
    local log_dir="${HOME}/.marqed/logs/${task_id}"
    mkdir -p "${log_dir}"
    
    local log_file="${log_dir}/session-${session_id}.log"
    local task_file="${HOME}/.claude/tasks/${task_id}.json"
    
    echo "🚀 Session ${session_id} starting (PID: $$)" | tee "${log_file}"
    echo "   Log: ${log_file}" | tee -a "${log_file}"
    echo "" | tee -a "${log_file}"
    
    # Export task list ID
    export CLAUDE_CODE_TASK_LIST_ID="${task_id}"
    
    local iteration=1
    
    while [[ ${iteration} -le ${max_iterations} ]]; do
        echo "[Session ${session_id}] Iteration ${iteration}/${max_iterations}" | tee -a "${log_file}"
        
        # Check for available parallelizable tasks
        local available_task=$(jq -r '
            .tasks[] |
            select(.status == "pending") |
            select(.parallelizable == true) |
            select(
                .dependencies as $deps |
                all(
                    $deps[];
                    . as $dep |
                    any(.tasks[]; .id == $dep and .status == "completed")
                )
            ) |
            .id
        ' "${task_file}" | head -1)
        
        if [[ -z "${available_task}" ]]; then
            # Try non-parallelizable tasks if no parallel tasks available
            available_task=$(jq -r '
                .tasks[] |
                select(.status == "pending") |
                select(
                    .dependencies as $deps |
                    all(
                        $deps[];
                        . as $dep |
                        any(.tasks[]; .id == $dep and .status == "completed")
                    )
                ) |
                .id
            ' "${task_file}" | head -1)
        fi
        
        if [[ -z "${available_task}" ]]; then
            # Check if all tasks are complete
            local pending=$(jq '[.tasks[] | select(.status == "pending")] | length' "${task_file}")
            local in_progress=$(jq '[.tasks[] | select(.status == "in_progress")] | length' "${task_file}")
            
            if [[ ${pending} -eq 0 ]] && [[ ${in_progress} -eq 0 ]]; then
                echo "[Session ${session_id}] ✅ All tasks completed" | tee -a "${log_file}"
                break
            fi
            
            echo "[Session ${session_id}] ⏳ No available tasks, waiting..." | tee -a "${log_file}"
            sleep 10
            continue
        fi
        
        local task_title=$(jq -r ".tasks[] | select(.id == \"${available_task}\") | .title" "${task_file}")
        echo "[Session ${session_id}] 📌 Picked task: ${task_title}" | tee -a "${log_file}"
        
        # Mark task as in progress (with session ID in notes)
        jq "(.tasks[] | select(.id == \"${available_task}\")) |= 
            (.status = \"in_progress\" | 
             .notes = \"Session ${session_id} - Started: $(date +'%Y-%m-%d %H:%M:%S')\")" \
            "${task_file}" > "${task_file}.tmp"
        mv "${task_file}.tmp" "${task_file}"
        
        # Load prompt
        local prompt=$(cat "${prompt_file}")
        
        # Add session-specific context
        prompt="${prompt}

## Session Context

**Session ID**: ${session_id}
**Current Task**: ${available_task}
**Coordination**: Multiple sessions may be running in parallel. Check task status before starting work.

Focus on your assigned task: ${task_title}
"
        
        # Run Claude Code
        echo "[Session ${session_id}] 🤖 Running Claude Code..." | tee -a "${log_file}"
        
        if claude-code \
            --task-list "${task_id}" \
            --context "${context_dir}" \
            --prompt "${prompt}" \
            2>&1 | tee -a "${log_file}"; then
            
            echo "[Session ${session_id}] ✅ Task completed successfully" | tee -a "${log_file}"
            
            # Mark task as completed
            jq "(.tasks[] | select(.id == \"${available_task}\")) |= 
                (.status = \"completed\" | 
                 .completedAt = \"$(date -Iseconds)\" |
                 .notes = \"Session ${session_id} - Completed: $(date +'%Y-%m-%d %H:%M:%S')\")" \
                "${task_file}" > "${task_file}.tmp"
            mv "${task_file}.tmp" "${task_file}"
        else
            echo "[Session ${session_id}] ⚠️  Task execution failed" | tee -a "${log_file}"
            
            # Mark task as blocked
            jq "(.tasks[] | select(.id == \"${available_task}\")) |= 
                (.status = \"blocked\" | 
                 .notes = \"Session ${session_id} - Failed: $(date +'%Y-%m-%d %H:%M:%S')\")" \
                "${task_file}" > "${task_file}.tmp"
            mv "${task_file}.tmp" "${task_file}"
        fi
        
        echo "" | tee -a "${log_file}"
        ((iteration++))
        
        # Brief pause between tasks
        sleep 3
    done
    
    echo "[Session ${session_id}] 🏁 Session complete after ${iteration} iterations" | tee -a "${log_file}"
}

#######################################
# Monitor all sessions
#######################################
monitor_sessions() {
    local task_id="$1"
    local num_sessions="$2"
    local pids=("${@:3}")
    
    echo ""
    echo "👀 Monitoring ${num_sessions} parallel sessions..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Display session info
    local session_labels=({A..Z})
    for i in $(seq 0 $((num_sessions - 1))); do
        echo "Session ${session_labels[$i]}: PID ${pids[$i]}"
    done
    echo ""
    
    # Wait for all sessions with periodic status updates
    local completed=0
    while [[ ${completed} -lt ${num_sessions} ]]; do
        sleep 5
        
        completed=0
        for pid in "${pids[@]}"; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                ((completed++))
            fi
        done
        
        echo "Progress: ${completed}/${num_sessions} sessions completed"
        
        # Display task progress
        local task_file="${HOME}/.claude/tasks/${task_id}.json"
        if [[ -f "${task_file}" ]]; then
            local total=$(jq '.tasks | length' "${task_file}")
            local done=$(jq '[.tasks[] | select(.status == "completed")] | length' "${task_file}")
            local in_prog=$(jq '[.tasks[] | select(.status == "in_progress")] | length' "${task_file}")
            
            echo "Tasks: ${done}/${total} completed, ${in_prog} in progress"
        fi
        echo ""
    done
    
    echo "✅ All sessions completed!"
}

#######################################
# Main entry point
#######################################
main() {
    # Check arguments
    if [[ $# -lt 5 ]]; then
        usage
        exit 1
    fi
    
    local task_id="$1"
    local context_dir="$2"
    local prompt_file="$3"
    local num_sessions="$4"
    local max_iterations="$5"
    
    # Validate arguments
    if [[ ! -d "${context_dir}" ]]; then
        echo "❌ Error: Context directory not found: ${context_dir}" >&2
        exit 1
    fi
    
    if [[ ! -f "${prompt_file}" ]]; then
        echo "❌ Error: Prompt file not found: ${prompt_file}" >&2
        exit 1
    fi
    
    if [[ ${num_sessions} -lt 1 ]] || [[ ${num_sessions} -gt 10 ]]; then
        echo "❌ Error: Number of sessions must be between 1 and 10" >&2
        exit 1
    fi
    
    local task_file="${HOME}/.claude/tasks/${task_id}.json"
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        exit 1
    fi
    
    # Display startup info
    echo "🚀 Spawning ${num_sessions} Parallel Claude Code Sessions"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Task ID: ${task_id}"
    echo "Context: ${context_dir}"
    echo "Prompt: ${prompt_file}"
    echo "Sessions: ${num_sessions}"
    echo "Max Iterations: ${max_iterations}"
    echo ""
    
    # Session labels
    local session_labels=({A..Z})
    local pids=()
    
    # Spawn sessions
    for i in $(seq 0 $((num_sessions - 1))); do
        local session_id="${session_labels[$i]}"
        
        echo "Spawning Session ${session_id}..."
        
        run_session "${session_id}" "${task_id}" "${context_dir}" "${prompt_file}" "${max_iterations}" &
        pids+=($!)
        
        # Small delay between spawns to avoid race conditions
        sleep 1
    done
    
    # Monitor sessions
    monitor_sessions "${task_id}" "${num_sessions}" "${pids[@]}"
    
    # Wait for all sessions to complete
    for pid in "${pids[@]}"; do
        wait "${pid}" || true
    done
    
    echo ""
    echo "🎉 All parallel sessions completed successfully!"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
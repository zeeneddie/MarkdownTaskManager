#!/bin/bash
# monitor-tasks.sh - Real-time task progress monitoring for MarQed.ai
# Part of MarQed.ai AI-driven development workflow

set -e

#######################################
# Display usage information
#######################################
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] TASK_ID

Monitor Claude Code task progress in real-time

ARGUMENTS:
    TASK_ID              Task list ID to monitor

OPTIONS:
    -i, --interval N     Update interval in seconds (default: 2)
    -f, --format FORMAT  Output format: table|json|simple (default: table)
    -h, --help           Show this help message

EXAMPLES:
    # Basic monitoring
    $(basename "$0") BUG-2026-01-23-001

    # Faster updates
    $(basename "$0") --interval 1 BUG-2026-01-23-001

    # JSON output
    $(basename "$0") --format json CHANGE-2026-01-23-001

    # Use with watch
    watch -n 2 '$(basename "$0") --format simple BUG-2026-01-23-001'

OUTPUT:
    - Real-time task status updates
    - Progress percentage
    - Visual progress bar
    - Time estimates
    - Blocker alerts

For more information: https://github.com/marqed-ai/workflows
EOF
}

#######################################
# Display tasks in table format
#######################################
display_table_format() {
    local task_file="$1"
    
    clear
    
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║             MarQed.ai Task Monitor - $(date +'%Y-%m-%d %H:%M:%S')                    ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Summary statistics
    local total=$(jq '.tasks | length' "${task_file}")
    local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "${task_file}")
    local in_progress=$(jq '[.tasks[] | select(.status == "in_progress")] | length' "${task_file}")
    local pending=$(jq '[.tasks[] | select(.status == "pending")] | length' "${task_file}")
    local blocked=$(jq '[.tasks[] | select(.status == "blocked")] | length' "${task_file}")
    
    echo "📊 Summary:"
    echo "   Total: ${total} | ✅ Completed: ${completed} | 🔄 In Progress: ${in_progress}"
    echo "   ⏳ Pending: ${pending} | ⛔ Blocked: ${blocked}"
    echo ""
    
    # Progress bar
    local progress=$((completed * 100 / total))
    local bar_length=50
    local filled=$((progress * bar_length / 100))
    local empty=$((bar_length - filled))
    
    printf "Progress: ["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%\n" "${progress}"
    echo ""
    
    # Task list
    echo "┌────┬────────────────────────────────────────────┬────────────┬──────────────┐"
    echo "│ #  │ Task                                       │ Status     │ Time         │"
    echo "├────┼────────────────────────────────────────────┼────────────┼──────────────┤"
    
    local counter=1
    jq -r '.tasks[] | "\(.id)|\(.title)|\(.status)|\(.estimatedTime)"' "${task_file}" | while IFS='|' read -r id title status time; do
        # Truncate title if too long
        if [[ ${#title} -gt 40 ]]; then
            title="${title:0:37}..."
        fi
        
        # Format status with emoji
        case "${status}" in
            completed)
                status_display="✅ Complete"
                ;;
            in_progress)
                status_display="🔄 Progress"
                ;;
            pending)
                status_display="⏳ Pending "
                ;;
            blocked)
                status_display="⛔ Blocked "
                ;;
            *)
                status_display="❓ Unknown "
                ;;
        esac
        
        printf "│ %-2d │ %-42s │ %-10s │ %-12s │\n" "${counter}" "${title}" "${status_display}" "${time}"
        
        ((counter++))
    done
    
    echo "└────┴────────────────────────────────────────────┴────────────┴──────────────┘"
    echo ""
    
    # Blockers alert
    if [[ ${blocked} -gt 0 ]]; then
        echo "⚠️  BLOCKERS DETECTED:"
        jq -r '.tasks[] | select(.status == "blocked") | "   - \(.title): \(.notes // "No reason specified")"' "${task_file}"
        echo ""
    fi
    
    # Current task
    local current_task=$(jq -r '.tasks[] | select(.status == "in_progress") | .title' "${task_file}" | head -1)
    if [[ -n "${current_task}" ]]; then
        echo "🎯 Current Task: ${current_task}"
        echo ""
    fi
    
    # Time estimate
    local remaining_time=$(jq -r '[.tasks[] | select(.status != "completed") | .estimatedTime | gsub("[^0-9.]"; "") | tonumber] | add' "${task_file}")
    if [[ "${remaining_time}" != "null" ]] && [[ -n "${remaining_time}" ]]; then
        echo "⏱️  Estimated Remaining: ~${remaining_time} hours"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit"
}

#######################################
# Display tasks in JSON format
#######################################
display_json_format() {
    local task_file="$1"
    
    jq '{
        timestamp: now | strftime("%Y-%m-%d %H:%M:%S"),
        summary: {
            total: (.tasks | length),
            completed: ([.tasks[] | select(.status == "completed")] | length),
            in_progress: ([.tasks[] | select(.status == "in_progress")] | length),
            pending: ([.tasks[] | select(.status == "pending")] | length),
            blocked: ([.tasks[] | select(.status == "blocked")] | length),
            progress_percent: (([.tasks[] | select(.status == "completed")] | length) * 100 / (.tasks | length))
        },
        tasks: .tasks
    }' "${task_file}"
}

#######################################
# Display tasks in simple format
#######################################
display_simple_format() {
    local task_file="$1"
    
    local total=$(jq '.tasks | length' "${task_file}")
    local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "${task_file}")
    local progress=$((completed * 100 / total))
    
    echo "Progress: ${completed}/${total} (${progress}%)"
    echo ""
    
    jq -r '.tasks[] | "[\(.status | ascii_upcase)] \(.title)"' "${task_file}"
}

#######################################
# Main monitoring loop
#######################################
monitor_tasks() {
    local task_id="$1"
    local interval="$2"
    local format="$3"
    
    local task_file="${HOME}/.claude/tasks/${task_id}.json"
    
    # Check if task file exists
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not found: ${task_file}" >&2
        echo "" >&2
        echo "Available task files:" >&2
        ls -1 "${HOME}/.claude/tasks/" 2>/dev/null | grep "\.json$" || echo "  (none)" >&2
        exit 1
    fi
    
    # For JSON format, just output once
    if [[ "${format}" == "json" ]]; then
        display_json_format "${task_file}"
        exit 0
    fi
    
    # For table and simple formats, monitor continuously
    while true; do
        if [[ "${format}" == "table" ]]; then
            display_table_format "${task_file}"
        elif [[ "${format}" == "simple" ]]; then
            display_simple_format "${task_file}"
        fi
        
        # Check if all tasks are complete
        local pending=$(jq '[.tasks[] | select(.status != "completed")] | length' "${task_file}")
        if [[ ${pending} -eq 0 ]]; then
            echo ""
            echo "🎉 All tasks completed!"
            exit 0
        fi
        
        sleep "${interval}"
    done
}

#######################################
# Main entry point
#######################################
main() {
    local task_id=""
    local interval=2
    local format="table"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interval)
                interval="$2"
                shift 2
                ;;
            -f|--format)
                format="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                echo "❌ Error: Unknown option: $1" >&2
                usage
                exit 1
                ;;
            *)
                task_id="$1"
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "${task_id}" ]]; then
        echo "❌ Error: Task ID is required" >&2
        usage
        exit 1
    fi
    
    # Validate format
    if [[ ! "${format}" =~ ^(table|json|simple)$ ]]; then
        echo "❌ Error: Invalid format: ${format}" >&2
        echo "Valid formats: table, json, simple" >&2
        exit 1
    fi
    
    # Start monitoring
    monitor_tasks "${task_id}" "${interval}" "${format}"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
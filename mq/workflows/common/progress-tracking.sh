#!/bin/bash
# Progress tracking and visualization

#######################################
# Log progress to CSV
#######################################
log_progress() {
    local workflow_id="$1"
    local task_file="$2"
    local progress_file="${HOME}/.marqed/logs/${workflow_id}/progress.csv"
    
    # Create header if file doesn't exist
    if [[ ! -f "${progress_file}" ]]; then
        echo "timestamp,completed,in_progress,pending,blocked,total" > "${progress_file}"
    fi
    
    # Extract counts
    local completed=$(jq '[.tasks[] | select(.status=="completed")] | length' "${task_file}")
    local in_progress=$(jq '[.tasks[] | select(.status=="in_progress")] | length' "${task_file}")
    local pending=$(jq '[.tasks[] | select(.status=="pending")] | length' "${task_file}")
    local blocked=$(jq '[.tasks[] | select(.status=="blocked")] | length' "${task_file}")
    local total=$(jq '.tasks | length' "${task_file}")
    
    # Append to CSV
    echo "$(date -Iseconds),${completed},${in_progress},${pending},${blocked},${total}" >> "${progress_file}"
}

#######################################
# Generate progress chart (ASCII)
#######################################
generate_progress_chart() {
    local workflow_id="$1"
    local progress_file="${HOME}/.marqed/logs/${workflow_id}/progress.csv"
    
    if [[ ! -f "${progress_file}" ]]; then
        echo "No progress data available"
        return 1
    fi
    
    echo "📊 Progress Over Time"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Read CSV and create ASCII chart
    local max_val=$(tail -n +2 "${progress_file}" | cut -d, -f2 | sort -rn | head -1)
    local chart_width=50
    
    tail -n +2 "${progress_file}" | while IFS=, read ts completed in_prog pending blocked total; do
        local timestamp=$(date -d "${ts}" +"%H:%M" 2>/dev/null || echo "${ts:11:5}")
        local bar_length=$((completed * chart_width / total))
        local bar=$(printf '%*s' "${bar_length}" | tr ' ' '█')
        local pct=$((completed * 100 / total))
        
        printf "%s │%s %3d%% (%d/%d)\n" "${timestamp}" "${bar}" "${pct}" "${completed}" "${total}"
    done
    
    echo ""
}

#######################################
# Show detailed progress breakdown
#######################################
show_progress_breakdown() {
    local workflow_id="$1"
    local task_file="$2"
    
    echo "📋 Progress Breakdown"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # By phase
    echo "By Phase:"
    jq -r '.tasks | group_by(.phase) | .[] | 
        "\(.  | first | .phase // "N/A"): \(map(select(.status=="completed")) | length)/\(length) completed"' \
        "${task_file}" | column -t -s:
    
    echo ""
    
    # By status
    echo "By Status:"
    jq -r '.tasks | group_by(.status) | .[] | 
        "\(. | first | .status): \(length) tasks"' \
        "${task_file}" | column -t -s:
    
    echo ""
    
    # Time tracking
    local start_time=$(jq -r '.created' "${task_file}")
    local elapsed=$(( $(date +%s) - $(date -d "${start_time}" +%s 2>/dev/null || echo $(date +%s)) ))
    local hours=$((elapsed / 3600))
    local mins=$(( (elapsed % 3600) / 60 ))
    
    echo "Time Elapsed: ${hours}h ${mins}m"
    
    # Estimated time remaining
    local completed=$(jq '[.tasks[] | select(.status=="completed")] | length' "${task_file}")
    local total=$(jq '.tasks | length' "${task_file}")
    local remaining=$((total - completed))
    
    if [[ ${completed} -gt 0 ]]; then
        local avg_time_per_task=$((elapsed / completed))
        local est_remaining=$((remaining * avg_time_per_task))
        local est_hours=$((est_remaining / 3600))
        local est_mins=$(( (est_remaining % 3600) / 60 ))
        
        echo "Estimated Remaining: ${est_hours}h ${est_mins}m"
    fi
    
    echo ""
}

export -f log_progress
export -f generate_progress_chart
export -f show_progress_breakdown
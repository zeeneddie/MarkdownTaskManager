#!/bin/bash
# prd-to-tasks.sh - Convert PRD.md to Claude Code Tasks JSON
# Part of MarQed.ai AI-driven development workflow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat << EOF
Usage: $0 <prd_file> [output_file]

Convert PRD.md with task metadata to Claude Code tasks JSON format.

ARGUMENTS:
    prd_file        Path to PRD.md file with task metadata
    output_file     Optional output path (default: ~/.claude/tasks/TASK_ID.json)

EXAMPLES:
    # Convert bug PRD to tasks
    $0 bug-BUG-042/PRD.md

    # Convert to specific output file
    $0 bug-BUG-042/PRD.md /tmp/bug-042-tasks.json

PRD FORMAT REQUIREMENTS:
    Each phase must have:
    - **Task ID**: \`task-X\`
    - **Dependencies**: \`[task-Y, task-Z]\` or \`[]\`
    - **Can Parallelize**: Yes/No
    - **Estimated Time**: X hours

OUTPUT FORMAT:
    Claude Code tasks JSON in ~/.claude/tasks/
EOF
}

if [ "$#" -lt 1 ]; then
    usage
    exit 1
fi

PRD_FILE="$1"
OUTPUT_FILE="$2"

if [ ! -f "$PRD_FILE" ]; then
    echo "Error: PRD file not found: $PRD_FILE"
    exit 1
fi

# Extract task list ID from PRD
extract_task_id() {
    local prd="$1"
    
    # Try to extract from PRD header (Bug ID: BUG-XXX, Change ID: CHANGE-XXX, Migration ID: MIG-XXX)
    local task_id=$(grep -E "^# (Bug|Change|Migration) ID: " "$prd" | head -1 | sed -E 's/.*: \[?([A-Z]+-[0-9]+)\]?.*/\1/')
    
    if [ -z "$task_id" ]; then
        # Fallback: try Claude Code Task Configuration section
        task_id=$(grep -A 1 "Task List ID" "$prd" | grep -oE '[A-Z]+-[0-9]+' | head -1)
    fi
    
    if [ -z "$task_id" ]; then
        echo "ERROR: Could not extract task ID from PRD"
        echo "PRD must contain one of:"
        echo "  # Bug ID: [BUG-XXX]"
        echo "  # Change ID: [CHANGE-XXX]"
        echo "  # Migration ID: [MIG-XXX]"
        echo "  OR"
        echo "  **Task List ID**: \`XXX-YYY\`"
        exit 1
    fi
    
    echo "$task_id"
}

# Parse a single phase/feature from PRD
parse_phase() {
    local phase_text="$1"
    local phase_number="$2"
    
    # Extract task metadata
    local task_id=$(echo "$phase_text" | grep -oP '(?<=\*\*Task ID\*\*: `)[^`]+' || echo "task-${phase_number}")
    local title=$(echo "$phase_text" | grep -E "^###" | head -1 | sed 's/^### //' | sed 's/\[.*\] //')
    local dependencies=$(echo "$phase_text" | grep -oP '(?<=\*\*Dependencies\*\*: `\[)[^\]]*' || echo "")
    local can_parallel=$(echo "$phase_text" | grep -oP '(?<=\*\*Can Parallelize\*\*: )[^\n]*' || echo "No")
    local estimated_time=$(echo "$phase_text" | grep -oP '(?<=\*\*Estimated Time\*\*: )[^\n]*' || echo "Unknown")
    local priority=$(echo "$phase_text" | grep -oP '(?<=\*\*Priority\*\*: )[^\n]*' || echo "MEDIUM")
    
    # Extract description (first paragraph after Description: or first paragraph in section)
    local description=$(echo "$phase_text" | sed -n '/\*\*Description\*\*/,/\*\*Tasks\*\*/p' | grep -v "^\*\*" | grep -v "^$" | head -3 | tr '\n' ' ')
    
    if [ -z "$description" ]; then
        description=$(echo "$phase_text" | grep -A 3 "^###" | tail -2 | tr '\n' ' ')
    fi
    
    # Determine status (check if "Passes: true" or "passes: true")
    local status="pending"
    if echo "$phase_text" | grep -qi "passes.*true"; then
        status="completed"
    elif echo "$phase_text" | grep -qi "passes.*false"; then
        status="pending"
    fi
    
    # Convert dependencies string to JSON array
    local deps_json="[]"
    if [ -n "$dependencies" ]; then
        deps_json=$(echo "$dependencies" | sed 's/task-/"/g' | sed 's/, /", "task-/g' | sed 's/^/["task-/' | sed 's/$/"]/')
    fi
    
    # Convert can_parallel to boolean
    local parallel_json="false"
    if echo "$can_parallel" | grep -qi "yes"; then
        parallel_json="true"
    fi
    
    # Generate JSON for this task
    cat << JSON
    {
      "id": "$task_id",
      "title": "$title",
      "description": "$description",
      "status": "$status",
      "priority": "$priority",
      "dependencies": $deps_json,
      "can_parallelize": $parallel_json,
      "estimated_time": "$estimated_time",
      "metadata": {
        "phase_number": $phase_number,
        "source_prd": "$(basename "$PRD_FILE")"
      }
    }
JSON
}

# Main conversion logic
convert_prd_to_tasks() {
    local prd="$1"
    local output="$2"
    
    echo "Converting PRD to Claude Code tasks..." >&2
    echo "  Input: $prd" >&2
    
    # Extract task list ID
    local task_id=$(extract_task_id "$prd")
    echo "  Task List ID: $task_id" >&2
    
    # Set default output if not provided
    if [ -z "$output" ]; then
        mkdir -p ~/.claude/tasks
        output=~/.claude/tasks/${task_id}.json
    fi
    
    echo "  Output: $output" >&2
    
    # Extract all phases (sections starting with ###)
    local phases=$(awk '
        /^### / { 
            if (phase != "") print phase;
            phase = $0 "\n";
            next;
        }
        {
            if (phase != "") phase = phase $0 "\n";
        }
        END {
            if (phase != "") print phase;
        }
    ' "$prd")
    
    # Count phases
    local phase_count=$(echo "$phases" | grep -c "^###" || echo "0")
    
    if [ "$phase_count" -eq 0 ]; then
        echo "ERROR: No phases found in PRD (no ### headers)" >&2
        exit 1
    fi
    
    echo "  Found $phase_count phases" >&2
    
    # Generate tasks JSON
    echo "{" > "$output"
    echo "  \"task_list_id\": \"$task_id\"," >> "$output"
    echo "  \"created_at\": \"$(date -Iseconds)\"," >> "$output"
    echo "  \"source_prd\": \"$prd\"," >> "$output"
    echo "  \"total_phases\": $phase_count," >> "$output"
    echo "  \"tasks\": [" >> "$output"
    
    # Parse each phase
    local phase_num=1
    local first=true
    
    while IFS= read -r phase; do
        if [ -z "$phase" ]; then
            continue
        fi
        
        if [ "$first" = false ]; then
            echo "," >> "$output"
        fi
        first=false
        
        parse_phase "$phase" "$phase_num" >> "$output"
        
        phase_num=$((phase_num + 1))
    done <<< "$phases"
    
    echo "" >> "$output"
    echo "  ]" >> "$output"
    echo "}" >> "$output"
    
    # Validate JSON
    if command -v jq &> /dev/null; then
        if jq empty "$output" 2>/dev/null; then
            echo "✅ Valid JSON generated" >&2
        else
            echo "❌ ERROR: Invalid JSON generated" >&2
            cat "$output" >&2
            exit 1
        fi
    fi
    
    echo "✅ Tasks file created: $output" >&2
    echo "✅ Task count: $(jq '.tasks | length' "$output" 2>/dev/null || echo "unknown")" >&2
    
    # Display task summary
    if command -v jq &> /dev/null; then
        echo "" >&2
        echo "Task Summary:" >&2
        jq -r '.tasks[] | "  - \(.id): \(.title) [\(.status)]"' "$output" >&2
    fi
    
    echo "$output"
}

# Execute conversion
OUTPUT_PATH=$(convert_prd_to_tasks "$PRD_FILE" "$OUTPUT_FILE")

# Return output path for scripting
echo "$OUTPUT_PATH"

exit 0

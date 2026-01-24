#!/bin/bash
# initialize-tasks.sh - Initialize Claude Code Tasks from PRD
# Part of MarQed.ai AI-driven development workflow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat << EOF
Usage: $0 <task_id> <prd_file>

Initialize Claude Code task list from PRD.md

ARGUMENTS:
    task_id         Task list identifier (e.g., BUG-042, CHANGE-123, MIG-001)
    prd_file        Path to PRD.md file with task metadata

EXAMPLES:
    # Initialize bug fix tasks
    $0 BUG-042 bug-BUG-042/PRD.md

    # Initialize change request tasks
    $0 CHANGE-123 change-CHANGE-123/PRD.md

WHAT IT DOES:
    1. Validates PRD format
    2. Converts PRD to Claude Code tasks JSON
    3. Sets CLAUDE_CODE_TASK_LIST_ID environment variable
    4. Creates tasks directory if needed
    5. Validates generated tasks file

ENVIRONMENT:
    After running, sets:
    export CLAUDE_CODE_TASK_LIST_ID="<task_id>"
EOF
}

if [ "$#" -ne 2 ]; then
    usage
    exit 1
fi

TASK_ID="$1"
PRD_FILE="$2"

echo "=== Initializing Claude Code Tasks ==="
echo "Task ID: $TASK_ID"
echo "PRD: $PRD_FILE"
echo ""

# Validate inputs
if [ ! -f "$PRD_FILE" ]; then
    echo "❌ Error: PRD file not found: $PRD_FILE"
    exit 1
fi

if ! echo "$TASK_ID" | grep -qE '^[A-Z]+-[0-9]+$'; then
    echo "⚠️  Warning: Task ID format unusual (expected: XXX-NNN)"
    echo "   Got: $TASK_ID"
fi

# Check if PRD has required task metadata
echo "Validating PRD format..."

has_task_ids=$(grep -c "Task ID" "$PRD_FILE" || echo "0")
has_dependencies=$(grep -c "Dependencies" "$PRD_FILE" || echo "0")

if [ "$has_task_ids" -eq 0 ]; then
    echo "❌ Error: PRD missing task metadata"
    echo ""
    echo "PRD must have task metadata in each phase:"
    echo "  **Task ID**: \`task-X\`"
    echo "  **Dependencies**: \`[task-Y]\`"
    echo "  **Can Parallelize**: Yes/No"
    echo "  **Estimated Time**: X hours"
    echo ""
    echo "Run this to upgrade your PRD:"
    echo "  # (Instructions to upgrade template)"
    exit 1
fi

echo "✅ PRD format valid ($has_task_ids phases found)"

# Create tasks directory
mkdir -p ~/.claude/tasks

# Convert PRD to tasks JSON
echo ""
echo "Converting PRD to Claude Code tasks..."

TASKS_FILE=$(bash "$SCRIPT_DIR/prd-to-tasks.sh" "$PRD_FILE")

if [ ! -f "$TASKS_FILE" ]; then
    echo "❌ Error: Task file not created"
    exit 1
fi

# Validate tasks file
if command -v jq &> /dev/null; then
    TASK_COUNT=$(jq '.tasks | length' "$TASKS_FILE")
    echo "✅ Created $TASK_COUNT tasks"
    
    # Check for dependency issues
    echo ""
    echo "Checking task dependencies..."
    
    ALL_TASK_IDS=$(jq -r '.tasks[].id' "$TASKS_FILE")
    HAS_ISSUES=false
    
    while IFS= read -r task_id; do
        DEPS=$(jq -r ".tasks[] | select(.id == \"$task_id\") | .dependencies[]?" "$TASKS_FILE")
        
        while IFS= read -r dep; do
            if [ -n "$dep" ] && ! echo "$ALL_TASK_IDS" | grep -q "^${dep}$"; then
                echo "⚠️  Warning: Task $task_id depends on non-existent task: $dep"
                HAS_ISSUES=true
            fi
        done <<< "$DEPS"
    done <<< "$ALL_TASK_IDS"
    
    if [ "$HAS_ISSUES" = false ]; then
        echo "✅ All dependencies valid"
    fi
else
    echo "⚠️  jq not installed, skipping validation"
fi

# Set environment variable
export CLAUDE_CODE_TASK_LIST_ID="$TASK_ID"

echo ""
echo "=== Initialization Complete ==="
echo ""
echo "Task file: $TASKS_FILE"
echo "Task List ID: $TASK_ID"
echo ""
echo "To use in current shell, run:"
echo "  export CLAUDE_CODE_TASK_LIST_ID=\"$TASK_ID\""
echo ""
echo "To start Claude Code with these tasks:"
echo "  CLAUDE_CODE_TASK_LIST_ID=\"$TASK_ID\" claude-code"
echo ""
echo "To monitor task progress:"
echo "  watch -n 5 'cat $TASKS_FILE | jq \".tasks[] | {id, title, status}\"'"
echo ""

exit 0

#!/bin/bash
# Direct test of Felix LLM integration

echo "🧪 Testing Felix LLM Integration - Direct Test"
echo "=============================================="
echo ""

# Test payload
cat <<'EOF' | npx ts-node execute-felix-task-generation.ts
{
  "command": "generate-epics",
  "specification": {
    "id": "test-spec-001",
    "project_id": "test-project-001",
    "content_json": {
      "title": "Simple Task Manager",
      "architecture": {
        "style": "monolithic",
        "layers": ["api", "service", "data"]
      },
      "components": [
        {"name": "Task API", "type": "backend"},
        {"name": "Task Service", "type": "backend"},
        {"name": "Database", "type": "data"}
      ],
      "technical_requirements": [
        "RESTful API",
        "PostgreSQL database",
        "Python FastAPI"
      ]
    },
    "content_markdown": "# Simple Task Manager\n\nA basic task management system."
  },
  "projectId": "test-project-001",
  "options": {
    "max_epics": 3
  }
}
EOF

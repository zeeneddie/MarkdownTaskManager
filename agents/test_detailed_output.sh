#!/bin/bash
# Detailed output test to examine quality of AI-generated content

echo "🔍 Detailed LLM Generation Quality Test"
echo "========================================"
echo ""

cat <<'EOF' | npx ts-node execute-felix-task-generation.ts | jq '.'
{
  "command": "generate-epics",
  "specification": {
    "id": "quality-test",
    "project_id": "quality-test-project",
    "content_json": {
      "title": "Real-time Collaboration Platform",
      "architecture": {
        "style": "microservices",
        "layers": ["api-gateway", "event-bus", "services", "websocket", "cache", "data"]
      },
      "components": [
        {"name": "API Gateway", "type": "backend"},
        {"name": "WebSocket Server", "type": "realtime"},
        {"name": "User Service", "type": "backend"},
        {"name": "Document Service", "type": "backend"},
        {"name": "Collaboration Service", "type": "backend"},
        {"name": "Event Bus (Kafka)", "type": "messaging"},
        {"name": "Redis Cache", "type": "cache"},
        {"name": "PostgreSQL", "type": "database"},
        {"name": "React + TypeScript", "type": "frontend"}
      ],
      "technical_requirements": [
        "Real-time collaborative editing",
        "Operational transformation for conflict resolution",
        "WebSocket connections with fallback to long-polling",
        "Event-driven architecture with Kafka",
        "Redis for session management and caching",
        "PostgreSQL for persistent storage",
        "JWT authentication",
        "Role-based access control (RBAC)",
        "Horizontal scaling support",
        "99.9% uptime SLA"
      ]
    }
  },
  "projectId": "quality-test-project",
  "options": {"max_epics": 3}
}
EOF

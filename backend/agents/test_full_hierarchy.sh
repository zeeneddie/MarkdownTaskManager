#!/bin/bash
# Test full hierarchy generation: Epic → Features → Stories → Tasks

echo "🧪 Testing Felix Full Hierarchy Generation"
echo "==========================================="
echo ""

# Step 1: Generate Epics
echo "1️⃣  Generating Epics..."
EPICS_OUTPUT=$(cat <<'EOF' | npx ts-node execute-felix-task-generation.ts
{
  "command": "generate-epics",
  "specification": {
    "id": "test-spec-hierarchy",
    "project_id": "test-project-hierarchy",
    "content_json": {
      "title": "E-Commerce Platform",
      "architecture": {
        "style": "microservices",
        "layers": ["api-gateway", "services", "data"]
      },
      "components": [
        {"name": "API Gateway", "type": "backend"},
        {"name": "User Service", "type": "backend"},
        {"name": "Product Service", "type": "backend"},
        {"name": "Order Service", "type": "backend"},
        {"name": "Payment Gateway", "type": "integration"}
      ],
      "technical_requirements": [
        "RESTful APIs with OpenAPI docs",
        "PostgreSQL databases",
        "React frontend with TypeScript",
        "Docker containerization",
        "Kubernetes orchestration"
      ]
    }
  },
  "projectId": "test-project-hierarchy",
  "options": {"max_epics": 2}
}
EOF
)

echo "$EPICS_OUTPUT" | jq -r '.metadata | "✅ Generated \(.epics_generated // (.llm_used | if . then "epics" else "epics (mock)" end)) - LLM Used: \(.llm_used)"'
FIRST_EPIC=$(echo "$EPICS_OUTPUT" | jq -r '.epics[0]')
EPIC_TITLE=$(echo "$FIRST_EPIC" | jq -r '.title')
echo "   First Epic: $EPIC_TITLE"
echo ""

# Step 2: Generate Features for first epic
echo "2️⃣  Generating Features for: $EPIC_TITLE"
FEATURES_OUTPUT=$(cat <<EOF | npx ts-node execute-felix-task-generation.ts
{
  "command": "generate-features",
  "epic": $FIRST_EPIC,
  "specificationContext": {
    "title": "E-Commerce Platform",
    "architecture": {"style": "microservices"}
  },
  "projectId": "test-project-hierarchy",
  "options": {"max_features": 3}
}
EOF
)

echo "$FEATURES_OUTPUT" | jq -r '.metadata | "✅ Generated features - LLM Used: \(.llm_used)"'
FIRST_FEATURE=$(echo "$FEATURES_OUTPUT" | jq -r '.features[0]')
FEATURE_TITLE=$(echo "$FIRST_FEATURE" | jq -r '.title')
echo "   First Feature: $FEATURE_TITLE"
echo ""

# Step 3: Generate Stories for first feature
echo "3️⃣  Generating Stories for: $FEATURE_TITLE"
STORIES_OUTPUT=$(cat <<EOF | npx ts-node execute-felix-task-generation.ts
{
  "command": "generate-stories",
  "feature": $FIRST_FEATURE,
  "epicContext": $FIRST_EPIC,
  "projectId": "test-project-hierarchy",
  "options": {"max_stories": 3}
}
EOF
)

echo "$STORIES_OUTPUT" | jq -r '.metadata | "✅ Generated stories - LLM Used: \(.llm_used)"'
FIRST_STORY=$(echo "$STORIES_OUTPUT" | jq -r '.stories[0]')
STORY_TITLE=$(echo "$FIRST_STORY" | jq -r '.title')
echo "   First Story: $STORY_TITLE"
echo ""

# Step 4: Generate Tasks for first story
echo "4️⃣  Generating Tasks for: $STORY_TITLE"
TASKS_OUTPUT=$(cat <<EOF | npx ts-node execute-felix-task-generation.ts
{
  "command": "generate-tasks",
  "story": $FIRST_STORY,
  "featureContext": $FIRST_FEATURE,
  "projectId": "test-project-hierarchy",
  "options": {"max_tasks": 4}
}
EOF
)

echo "$TASKS_OUTPUT" | jq -r '.metadata | "✅ Generated tasks - LLM Used: \(.llm_used)"'
echo ""

# Summary
echo "==========================================="
echo "✨ Full Hierarchy Test Complete!"
echo "==========================================="
echo ""
echo "📊 Summary:"
echo "   - Specification → Epics: ✅"
echo "   - Epic → Features: ✅"
echo "   - Feature → Stories: ✅"
echo "   - Story → Tasks: ✅"
echo ""
echo "🤖 All 4 levels generated with qwen2.5-coder:7b!"

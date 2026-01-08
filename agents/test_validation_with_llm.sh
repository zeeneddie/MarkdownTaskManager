#!/bin/bash
# Test validation integrated with real LLM generation

echo "🔍 Testing Validation with Real LLM Generation"
echo "=============================================="
echo ""

echo "Generating features with real AI and automatic validation..."
echo ""

cat <<'EOF' | npx ts-node execute-felix-task-generation.ts | jq '{
  features: .features | length,
  validation: .validation,
  sample_feature: .features[0].title
}'
{
  "command": "generate-features",
  "epic": {
    "id": "epic-validation-test",
    "title": "Real-time Collaboration Platform",
    "description": "Build a comprehensive real-time collaboration platform with WebSocket support",
    "business_value": "Enable teams to work together in real-time",
    "estimated_story_points": 50,
    "estimated_weeks": 4,
    "priority": "critical"
  },
  "specificationContext": {
    "title": "Real-time Collaboration Platform",
    "architecture": {
      "style": "microservices",
      "layers": ["api", "websocket", "services", "data"]
    }
  },
  "projectId": "test-project",
  "options": {"max_features": 5}
}
EOF

echo ""
echo "✅ Features generated with automatic validation!"
echo ""
echo "Validation checks performed:"
echo "  - Required field validation"
echo "  - Story point ranges (5-21, Fibonacci)"
echo "  - Timeline reasonableness (2-8 days)"
echo "  - Priority validation"
echo "  - Technical approach completeness"
echo "  - Dependency cycle detection"

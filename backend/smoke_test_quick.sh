#!/bin/bash
# Quick smoke test

echo "🧪 Running Quick Smoke Tests..."
echo ""

# Test 1: Work Types
echo "Test 1: Work Types (expecting 9)"
curl -s http://localhost:8000/api/workflows/work-types | jq 'length'

# Test 2: Agents
echo "Test 2: Agents (expecting 10)"
curl -s http://localhost:8000/api/workflows/agents | jq 'length'

# Test 3: NEW_FEATURE workflow
echo "Test 3: NEW_FEATURE Workflow"
curl -s -X POST http://localhost:8000/api/workflows/analyze \
  -H "Content-Type: application/json" \
  -d '{"description": "Add OAuth2 authentication"}' | jq '{work_type, agent_count: (.agents_executed | length), execution_time: .total_execution_time}'

# Test 4: BUG workflow
echo "Test 4: BUG Workflow"
curl -s -X POST http://localhost:8000/api/workflows/analyze \
  -H "Content-Type: application/json" \
  -d '{"description": "Fix session timeout bug"}' | jq '{work_type, agent_count: (.agents_executed | length), execution_time: .total_execution_time}'

echo ""
echo "✅ Smoke tests complete!"

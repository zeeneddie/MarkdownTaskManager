"""
E2E Tests Package

End-to-end tests for MarQed AI Agent Platform workflows.

Test Categories:
- TC101-103: Week 69 Project Workflows (HCI-CRS demo)
- TC104-106: Reference data, review flow, negative cases

Run with:
    pytest tests/e2e/ -v -m e2e

Requirements:
- Backend server running on localhost:8000
- Database migrated (alembic upgrade head)
- Ollama service running
- HCI-CRS project at /opt/projecten/hci-crs/src
"""

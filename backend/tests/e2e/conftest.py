"""
E2E Test Configuration

Fixtures and configuration for end-to-end tests.
"""

import pytest
import os

# E2E test marker
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test (requires running server)"
    )


# Skip E2E tests if server not running
@pytest.fixture(scope="session", autouse=True)
def check_server_running():
    """Check if backend server is running before E2E tests"""
    import httpx

    try:
        response = httpx.get("http://localhost:8000/api/health", timeout=5.0)
        if response.status_code != 200:
            pytest.skip("Backend server not healthy")
    except httpx.ConnectError:
        pytest.skip("Backend server not running on localhost:8000")


# Common test data
@pytest.fixture
def hci_crs_path():
    """Path to HCI-CRS demo project"""
    path = "/opt/projecten/hci-crs/src"
    if not os.path.exists(path):
        pytest.skip(f"HCI-CRS project not found at {path}")
    return path


@pytest.fixture
def base_url():
    """Base URL for API calls"""
    return os.environ.get("E2E_BASE_URL", "http://localhost:8000")

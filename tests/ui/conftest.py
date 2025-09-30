import pytest
import requests
import time
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
    }

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }

@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the server is running before UI tests start."""
    base_url = "http://localhost:8000"
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code in [200, 404]:  # 404 is fine, server is responding
                print(f"Server is responding at {base_url}")
                return
        except requests.exceptions.RequestException:
            if attempt < max_attempts - 1:
                time.sleep(1)
            else:
                pytest.fail(f"Server at {base_url} is not responding after {max_attempts} attempts")

@pytest.fixture
def base_url():
    """Base URL for the application."""
    return "http://localhost:8000"

@pytest.fixture(autouse=True)
async def setup_teardown():
    # Setup code here (if needed)
    yield
    # Teardown code here (if needed)
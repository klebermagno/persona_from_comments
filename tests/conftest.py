import os
import pytest

def pytest_configure(config):
    """Configure pytest - runs before tests start."""
    os.environ['TESTING'] = 'true'

def pytest_unconfigure(config):
    """Cleanup after all tests are done."""
    os.environ['TESTING'] = 'false'

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup per-test environment variables."""
    yield  # No need to set/unset TESTING here as it's handled at pytest level

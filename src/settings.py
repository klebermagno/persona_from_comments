import os
from dotenv import load_dotenv

# Check if we're in test mode
IN_TEST_MODE = os.getenv('TESTING', 'false').lower() == 'true'

# Load environment variables from .env file if not in test mode
if not IN_TEST_MODE:
    load_dotenv()

# Default values for testing
TEST_API_KEY = 'test_api_key'
TEST_YOUTUBE_KEY = 'test_youtube_key'
TEST_NAMSOR_KEY = 'test_namsor_key'

# Settings with test mode support
OPENAI_API_KEY = TEST_API_KEY if IN_TEST_MODE else os.getenv("OPENAI_API_KEY")
YOUTUBE_DEVELOPER_KEY = TEST_YOUTUBE_KEY if IN_TEST_MODE else os.getenv("YOUTUBE_DEVELOPER_KEY")
NAMSOR_KEY = TEST_NAMSOR_KEY if IN_TEST_MODE else os.getenv("NAMSOR_KEY")

# Only validate in non-test mode
if not IN_TEST_MODE:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. Please create a .env file with your API key."
        )

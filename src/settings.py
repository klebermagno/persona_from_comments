import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. Please create a .env file with your API key."
    )

YOUTUBE_DEVELOPER_KEY = os.getenv("YOUTUBE_DEVELOPER_KEY")
NAMSOR_KEY = os.getenv("NAMSOR_KEY")

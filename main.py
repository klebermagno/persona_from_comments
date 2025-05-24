import sys
import logging

from gathering import Gathering
from mining import Mining
from llm_analysis import LLMAnalysis
from generating import (
    Generating,
)  # Added import for consistency, though not used in original main

# Configure logging - This will configure the root logger.
# If other modules (like app.py) also configure it, the first one wins,
# or if they configure specific loggers, those will be additive.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),  # Log pipeline specific messages to a file
        logging.StreamHandler(sys.stdout),  # And also print to console
    ],
)
logger = logging.getLogger(__name__)


def main(video_id):
    logger.info(f"Starting full pipeline for video_id: {video_id}")

    logger.info("Starting Gathering phase...")
    gathering = Gathering()
    gathering.execute(video_id)
    logger.info("Finished Gathering phase.")

    logger.info("Starting Mining phase...")
    mining = Mining()
    mining.execute(video_id)
    logger.info("Finished Mining phase.")

    logger.info("Starting Content Analysis phase (sentiments, genders, keywords)...")
    content_analyzer = LLMAnalysis()
    content_analyzer.execute(video_id)
    logger.info("Finished Content Analysis phase.")

    # Assuming LLMAnalysis is a separate step, not explicitly mentioned to add here
    # but was part of the original app.py flow (PersonaGenerator._ensure_video_analyzed)
    # For this refactoring, only adding Generating as per implication.

    logger.info("Starting Generating phase (persona report)...")
    generating = Generating()
    generating.execute(video_id)
    logger.info("Finished Generating phase.")

    logger.info(f"Full pipeline finished for video_id: {video_id}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_id_arg = str(sys.argv[1])
        logger.info(
            f"Running pipeline for video_id from command line argument: {video_id_arg}"
        )
        main(video_id_arg)
    else:
        logger.error("No video_id provided as command line argument.")
        print("Usage: python main.py <video_id>")

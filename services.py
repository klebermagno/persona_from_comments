import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from db_manager import DBManager
from llm_analysis import LLMAnalysis
from main import main  # Assuming main function is for processing video if not exists

logger = logging.getLogger(__name__)


@dataclass
class PersonaData:
    """Data class to hold persona information"""

    title: str
    name: str
    gender: str
    issues: List[str]
    wishes: List[str]
    pains: List[str]
    expressions: List[str]
    status: str


class PersonaGenerator:
    """Class to handle persona generation logic"""

    def __init__(self):
        self.db = DBManager()

    def _ensure_video_analyzed(self, video_id: str) -> Optional[Dict[str, List[str]]]:
        """Ensure video has LLM analysis, create if missing"""
        try:
            # self.db.connect() # REMOVED
            analysis = self.db.get_analysis(video_id)

            if not analysis:
                logger.info(
                    f"No existing analysis found for video {video_id}, creating new analysis"
                )
                llm = LLMAnalysis()
                analysis = llm.execute(video_id)
                if not analysis:
                    logger.warning(f"Failed to create analysis for video {video_id}")

            # self.db.close() # REMOVED
            return analysis
        except Exception as e:
            logger.error(
                f"Error in _ensure_video_analyzed for video {video_id}: {str(e)}"
            )
            # self.db.close() # REMOVED
            # It's often better to re-raise or handle more gracefully than just returning None
            # For now, matching existing behavior of potentially returning None if llm.execute fails
            return None  # Or re-raise depending on desired error handling

    def _format_gender(self, gender_code: str) -> str:
        """Convert gender code to display format"""
        return "Female" if gender_code == "F" else "Male"

    def generate_persona(self, video_id: str) -> PersonaData:
        """Generate a persona for a video"""
        if not video_id:
            logger.warning("No video ID provided")
            return PersonaData(
                title="No Video Selected",
                name="",
                gender="",
                issues=[],
                wishes=[],
                pains=[],
                expressions=[],
                status="Please enter a video ID",
            )

        try:
            logger.info(f"Generating persona for video {video_id}")
            # self.db.connect() # REMOVED

            # Process video if not in database
            if not self.db.video_exists(video_id):
                logger.info(f"Video {video_id} not found in database, processing...")
                try:
                    main(video_id)
                except ValueError as ve:
                    # Handle specific error for invalid/inaccessible videos
                    logger.error(f"Invalid video ID {video_id}: {str(ve)}")
                    return PersonaData(
                        title="Error",
                        name="",
                        gender="",
                        issues=[],
                        wishes=[],
                        pains=[],
                        expressions=[],
                        status=f"Invalid video ID: {str(ve)}",
                    )
                except Exception as e:
                    # Handle other errors in processing
                    logger.error(f"Error processing video {video_id}: {str(e)}")
                    return PersonaData(
                        title="Error",
                        name="",
                        gender="",
                        issues=[],
                        wishes=[],
                        pains=[],
                        expressions=[],
                        status=f"Error processing video: {str(e)}",
                    )

            # Get video information
            title = self.db.get_video_title(video_id)
            name, gender = self.db.get_user_demographics(video_id)

            # Get or create analysis
            analysis = self._ensure_video_analyzed(
                video_id
            )  # This now correctly uses the refactored DBManager
            if not analysis:
                logger.warning(
                    f"No analysis available for video {video_id}, using empty data."
                )
                analysis = {"issues": [], "wishes": [], "pains": [], "expressions": []}

            # self.db.close() # REMOVED

            return PersonaData(
                title=f"Generated Persona for Video: {title}",
                name=name,
                gender=self._format_gender(gender),
                issues=analysis.get("issues", []),  # Use .get for safety
                wishes=analysis.get("wishes", []),  # Use .get for safety
                pains=analysis.get("pains", []),  # Use .get for safety
                expressions=analysis.get("expressions", []),  # Use .get for safety
                status=f"Persona generated for video: {video_id}",
            )

        except Exception as e:
            error_msg = f"Error processing video {video_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # self.db.close() # REMOVED
            return PersonaData(
                title="Error",
                name="",
                gender="",
                issues=[],
                wishes=[],
                pains=[],
                expressions=[],
                status=error_msg,
            )

import os
import googleapiclient.discovery
import googleapiclient.errors
import logging

from .settings import YOUTUBE_DEVELOPER_KEY as DEVELOPER_KEY
from .db_manager import DBManager
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class Gathering:
    def __init__(self) -> None:
        api_service_name = "youtube"
        api_version = "v3"
        
        # Disable OAuthlib's HTTPS verification for local development
        # This is required by the YouTube API client. Do not enable in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY
        )
        self.db = DBManager()

    def execute(self, video_id):
        """Execute the gathering process for the given video ID.
        
        Args:
            video_id (str): The YouTube video ID to gather comments from.
            
        Raises:
            ValueError: If video_id is empty or invalid
            Exception: For other API or processing errors
        """
        if not video_id:
            error_msg = "Video ID cannot be empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            extractor = MetadataExtractor()

            # Get video details
            request_video_details = self.youtube.videos().list(part="snippet", id=video_id)
            response_video_details = request_video_details.execute()
            
            # Check if video exists
            if not response_video_details.get("items"):
                error_msg = f"Video {video_id} not found or not accessible. Please check if the video ID is correct and the video is publicly available."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            video_title = response_video_details["items"][0]["snippet"]["title"]
            logger.info(f"Found video: {video_title} ({video_id})")
            self.db.save_video_title(video_id, video_title)

            # Get comments
            request = self.youtube.commentThreads().list(
                part="snippet", maxResults=3000, videoId=video_id
            )
            response = request.execute()

            # Check if video has comments
            if not response.get("items"):
                warning_msg = f"No comments found for video {video_id}"
                logger.warning(warning_msg)
                return

            # Process all comment pages
            while response:
                for item in response["items"]:
                    comment = extractor.extract(item)
                    comment.video_id = video_id
                    if len(comment.text) > 20:
                        self.db.save_comment(comment)

                # Get the next page of comments if available
                if "nextPageToken" not in response:
                    break
                    
                request = self.youtube.commentThreads().list(
                    part="snippet",
                    maxResults=3000,
                    videoId=video_id,
                    pageToken=response["nextPageToken"],
                )
                response = request.execute()

        except googleapiclient.errors.HttpError as e:
            error_msg = f"YouTube API error occurred: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(error_msg)
            raise

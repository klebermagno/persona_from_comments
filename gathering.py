import os
import googleapiclient.discovery
from datetime import datetime
from db_manager import DBManager
from comment import Comment
import settings


class MetadataExtractor:

    def extract(self, item):
        comment = Comment()  # Changed from Comment(None)
        # comment.video_id = '' # Not needed, default is ''
        comment.published = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
        comment.author_display_name = item["snippet"]["topLevelComment"]["snippet"][
            "authorDisplayName"
        ]
        comment.likes = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
        comment.text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]

        return comment


class Gathering:
    def __init__(self) -> None:
        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = settings.YOUTUBE_DEVELOPER_KEY
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = (
            "1"  # Keep this for YouTube API client
        )
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY
        )
        self.db = DBManager()  # Initialize DBManager instance

    def execute(self, video_id):
        extractor = MetadataExtractor()
        # db = DBManager() # DBManager is now an instance variable self.db
        # db.connect() # REMOVED

        request_video_details = self.youtube.videos().list(part="snippet", id=video_id)
        response_video_details = request_video_details.execute()
        video_title = response_video_details["items"][0]["snippet"]["title"]

        self.db.save_video_title(video_id, video_title)  # Use new DBManager method
        # db.con.commit() # REMOVED

        request = self.youtube.commentThreads().list(
            part="snippet", maxResults=3000, videoId=video_id
        )

        response = request.execute()

        while "nextPageToken" in response:
            for item in response["items"]:
                comment = extractor.extract(item)
                comment.video_id = video_id
                if len(comment.text) > 20:
                    self.db.save_comment(comment)  # Use self.db

            # Get the next page of comments
            # and update the request with the new page token
            request = self.youtube.commentThreads().list(
                part="snippet",
                maxResults=3000,
                videoId=video_id,
                pageToken=response["nextPageToken"],
            )

            response = request.execute()

        # db.con.commit() # REMOVED - save_comment and save_video_title handle their own commits
        # db.close() # REMOVED - DBManager connections are managed by context managers

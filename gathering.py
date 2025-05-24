import os
import googleapiclient.discovery
from datetime import datetime
from db_manager import DBManager
from comment import Comment
import settings
    
class MetadataExtractor:
    
    def extract(self, item):  
        comment = Comment(None) 
        comment.video_id = '' 
        comment.published = item['snippet']['topLevelComment']['snippet']['publishedAt']
        comment.author_display_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
        comment.likes = item['snippet']['topLevelComment']['snippet']['likeCount']
        comment.text = item['snippet']['topLevelComment']['snippet']['textOriginal']
    
        return comment

class Gathering:
    def __init__(self) -> None:
        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = settings.YOUTUBE_DEVELOPER_KEY
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY)

    def execute(self, video_id):
        extractor = MetadataExtractor()
        db = DBManager()
        db.connect()
        
        request_video_details = self.youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response_video_details = request_video_details.execute()
        video_title = response_video_details["items"][0]["snippet"]["title"]
        
        db.cur.execute('INSERT INTO video (video_id, title) VALUES (?,?)', (video_id, video_title))
        db.con.commit()
        
        request = self.youtube.commentThreads().list(
                part="snippet",
                maxResults=3000,
                videoId=video_id
            )

        response = request.execute()      
        
        while 'nextPageToken' in response: 
            for item in response['items']:
                comment = extractor.extract(item)
                comment.video_id = video_id
                if len(comment.text) > 20:
                    db.save_comment(comment)
            
            # Get the next page of comments
            # and update the request with the new page token
            request = self.youtube.commentThreads().list(
                part="snippet",
                maxResults=3000,
                videoId=video_id,
                pageToken=response['nextPageToken']
            )

            response = request.execute()
       
        
        db.con.commit()
        db.close()

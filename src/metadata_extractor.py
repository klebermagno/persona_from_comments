from datetime import datetime
from .comment import Comment
from .text_cleaner import TextCleaner # Added as per subtask description

class MetadataExtractor:
    def extract(self, item) -> Comment:
        """Extract metadata from a YouTube comment item.
        
        Args:
            item: A comment item from the YouTube API response.
            
        Returns:
            Comment: A Comment object containing the extracted metadata.
        """
        comment = Comment(None)  # Initialize with None since we're not reading from DB
        
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        
        comment.video_id = ""  # This will be set by the caller
        comment.published = datetime.strptime(snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        comment.author_display_name = snippet["authorDisplayName"]
        comment.author_clean_name = ""  # This will be cleaned by the mining process
        comment.author_gender = ""  # This will be set by the analysis process
        comment.likes = snippet.get("likeCount", 0)
        comment.text = snippet["textOriginal"]
        comment.clean_text = ""  # This will be cleaned by the mining process
        comment.sentiment = 0  # This will be set by the analysis process
        comment.created = datetime.now()
        comment.updated = None
        
        return comment

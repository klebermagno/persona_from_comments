from dataclasses import dataclass
from datetime import datetime

@dataclass
class Comment:
    id: int = 0
    video_id: str = ''
    published: datetime = None
    author_display_name: str = ''
    author_clean_name: str = ''
    author_gender: str = ''
    likes: int = -1
    text: str = ''
    clean_text: str = ''
    sentiment: float = 0
    created: datetime = None
    updated: datetime = None
    
    def __init__(self, db_row):
        if db_row:
            self.id = db_row[0]
            self.video_id = db_row[1]
            self.published = db_row[2]
            self.author_display_name = db_row[3]
            self.author_clean_name = db_row[4]
            self.author_gender = db_row[5]
            self.likes = db_row[6]
            self.text = db_row[7]
            self.clean_text = db_row[8]
            self.sentiment = db_row[9]
            self.created = db_row[10]
            self.updated = db_row[11]
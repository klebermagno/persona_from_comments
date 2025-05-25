from dataclasses import dataclass
from datetime import datetime


@dataclass
class Comment:
    id: int = 0
    video_id: str = ""
    published: datetime = None
    author_display_name: str = ""
    author_clean_name: str = ""
    author_gender: str = ""
    likes: int = -1
    text: str = ""
    clean_text: str = ""
    sentiment: float = 0.0  # Ensured default for float
    created: datetime = None
    updated: datetime = None

    # Removed custom __init__(self, db_row)

    @classmethod
    def from_db_row(cls, db_row: tuple):
        if db_row:
            return cls(
                id=db_row[0],
                video_id=db_row[1],
                published=db_row[2],
                author_display_name=db_row[3],
                author_clean_name=db_row[4],
                author_gender=db_row[5],
                likes=db_row[6],
                text=db_row[7],
                clean_text=db_row[8],
                sentiment=db_row[9],
                created=db_row[10],
                updated=db_row[11],
            )
        return cls()  # Return an empty Comment object with default values

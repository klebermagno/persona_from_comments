import sqlite3
from datetime import datetime
import json
from typing import List, Tuple, Dict, Optional

    
class DBManager:
    def connect(self):
        self.con = sqlite3.connect("youtube.db")
        self.cur = self.con.cursor()
        
    def close(self):
        self.con.close()

    def _row_to_dict(self, row):
        """Convert a database row to a dictionary"""
        return {
            "id": row[0],
            "video_id": row[1],
            "published": row[2],
            "author_display_name": row[3],
            "author_clean_name": row[4],
            "author_gender": row[5],
            "likes": row[6],
            "text": row[7],
            "clean_text": row[8],
            "sentiment": row[9],
            "created": row[10],
            "updated": row[11]
        }

    def create_db(self):
        create_table_comment = """
        CREATE TABLE if not exists comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            published DATATIME NOT NULL,
            author_display_name CHAR(100) NOT NULL,
            author_clean_name CHAR(100),
            author_gender CHAR(1),
            likes INTEGER NOT NULL,
            text TEXT NOT NULL,
            clean_text TEXT,
            sentiment REAL,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME
        );
        """
        self.cur.execute(create_table_comment)
        
        create_comment_keywords = """
        CREATE TABLE if not exists comment_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            text TEXT NOT NULL,
            score REAL,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cur.execute(create_comment_keywords)
        
        create_video = """
        CREATE TABLE if not exists video (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            title TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cur.execute(create_video)

        create_analysis = """
        CREATE TABLE if not exists analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            issues TEXT,
            wishes TEXT,
            pains TEXT,
            expressions TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME,
            UNIQUE(video_id)
        );
        """
        self.cur.execute(create_analysis)

    def save_comment(self, comment):
        sql = "INSERT INTO comment(created, published, video_id, author_display_name, likes, text) VALUES (?,?,?,?,?,?)"
        
        
        self.cur.execute(sql, (datetime.now(), comment.published, comment.video_id,
                               comment.author_display_name, comment.likes, comment.text))
        
    def get_comments(self, video_id, no_sentiment=False, no_gender=False):
        if no_sentiment:
            res = self.cur.execute("SELECT * FROM comment WHERE video_id = '{}' AND sentiment IS NULL".format(video_id))
        elif no_gender:
            res = self.cur.execute("SELECT * FROM comment WHERE video_id = '{}' AND author_gender IS NULL".format(video_id))
        else:
            res = self.cur.execute("SELECT * FROM comment WHERE video_id = '{}'".format(video_id))
        
        rows = res.fetchall()
        return [self._row_to_dict(row) for row in rows]
        
    def save_analysis(self, video_id: str, analysis_data: dict) -> None:
        """Save analysis results to the database."""
        # Convert lists to JSON strings for storage
        analysis_json = {
            key: json.dumps(value, ensure_ascii=False) 
            for key, value in analysis_data.items()
        }
        
        sql = """
        INSERT INTO analysis (video_id, issues, wishes, pains, expressions, created, updated)
        VALUES (:video_id, :issues, :wishes, :pains, :expressions, :created, :updated)
        ON CONFLICT(video_id) DO UPDATE SET
            issues = :issues,
            wishes = :wishes,
            pains = :pains,
            expressions = :expressions,
            updated = :updated
        """
        
        params = {
            "video_id": video_id,
            "issues": analysis_json.get("issues"),
            "wishes": analysis_json.get("wishes"),
            "pains": analysis_json.get("pains"),
            "expressions": analysis_json.get("expressions"),
            "created": datetime.now(),
            "updated": datetime.now()
        }
        
        self.cur.execute(sql, params)
        
    def get_user_demographics(self, video_id: str) -> Tuple[str, str]:
        """Get the most common gender and name from comments for a video."""
        genders_count = {'M': 0, 'F': 0}
        names = {'F': {}, 'M': {}}
        
        self.cur.execute(
            "SELECT author_clean_name, author_gender FROM comment WHERE video_id = ? AND author_gender IS NOT NULL",
            (video_id,)
        )
        results = self.cur.fetchall()
        
        for name, gender in results:
            if gender in genders_count:
                genders_count[gender] += 1
                
            if name and gender in names:
                firstname = name.split()[0] if name and ' ' in name else name
                if firstname:
                    names[gender][firstname] = names[gender].get(firstname, 0) + 1
        
        dominant_gender = 'M' if genders_count.get('M', 0) > genders_count.get('F', 0) else 'F'
        
        most_common_name = ""
        highest_count = 0
        for name, count in names.get(dominant_gender, {}).items():
            if count > highest_count:
                most_common_name = name
                highest_count = count
                
        return most_common_name, dominant_gender

    def get_analysis(self, video_id: str) -> Optional[Dict[str, List[str]]]:
        """Get LLM analysis results for a video."""
        self.cur.execute(
            "SELECT issues, wishes, pains, expressions FROM analysis WHERE video_id = ?",
            (video_id,)
        )
        row = self.cur.fetchone()
        
        if not row:
            return None
            
        return {
            'issues': json.loads(row[0]) if row[0] else [],
            'wishes': json.loads(row[1]) if row[1] else [],
            'pains': json.loads(row[2]) if row[2] else [],
            'expressions': json.loads(row[3]) if row[3] else []
        }

    def get_video_title(self, video_id: str) -> str:
        """Get the title of a video."""
        self.cur.execute("SELECT title FROM video WHERE video_id = ?", (video_id,))
        row = self.cur.fetchone()
        return row[0] if row else "Unknown Title"

    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in the database."""
        self.cur.execute("SELECT 1 FROM video WHERE video_id = ?", (video_id,))
        return bool(self.cur.fetchone())

    def get_all_videos(self) -> List[Tuple[str, str]]:
        """Get all videos with their titles."""
        self.cur.execute("SELECT video_id, title FROM video ORDER BY created DESC")
        return self.cur.fetchall()

    def get_keywords(self, video_id: str) -> List[str]:
        """Get keywords for a video."""
        self.cur.execute(
            "SELECT text FROM comment_keywords WHERE video_id = ? ORDER BY score ASC LIMIT 20",
            (video_id,)
        )
        return [row[0] for row in self.cur.fetchall()]
import sqlite3
from datetime import datetime
import json
from typing import List, Tuple, Dict, Optional, Union
from contextlib import contextmanager


class DBManager:
    def __init__(self, db_name="youtube.db"):
        self.db_name = db_name
        self.conn = None
        if self.db_name == ":memory:":
            self.conn = sqlite3.connect(self.db_name)
            cur = self.conn.cursor()
            self._ensure_tables_exist(cur) # Ensure tables are created for in-memory DB

    @contextmanager
    def _managed_cursor(self, commit_on_exit=False):
        """Context manager for database cursor with automatic connection management."""
        if self.conn:  # If there's a persistent connection (for :memory:)
            con = self.conn
        else:
            con = sqlite3.connect(self.db_name)
        
        cur = con.cursor()
        
        if not self.conn: # Only call _ensure_tables_exist if it's not a persistent conn
                          # (assuming it was called for persistent conn in __init__)
            self._ensure_tables_exist(cur) # This ensures tables for file DBs on each new temp connection
        
        try:
            yield cur
            if commit_on_exit:
                con.commit()
        finally:
            if not self.conn: # Only close if it's not the persistent connection
                con.close()
            
    def _ensure_tables_exist(self, cursor):
        """Ensure all required tables exist."""
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            published DATETIME NOT NULL,
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
        
        CREATE TABLE IF NOT EXISTS comment_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            text TEXT NOT NULL,
            score REAL,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS video (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL UNIQUE,
            title TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            video_id CHAR(150) NOT NULL,
            name TEXT,
            gender TEXT,
            age TEXT,
            language TEXT,
            issues TEXT,
            wishes TEXT,
            pains TEXT,
            expressions TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME,
            UNIQUE(video_id)
        );
        """)

    def _execute_query(
        self,
        sql: str,
        params: tuple = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        commit: bool = False,
    ):
        with self._managed_cursor(commit_on_exit=commit) as cur:
            cur.execute(sql, params or ())
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            return None  # Or cur.rowcount, depending on desired return for non-select queries

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
            "updated": row[11],
        }

    def create_db(self):
        """Create all required database tables if they don't exist."""
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            
            # Create comment table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS comment (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                video_id CHAR(150) NOT NULL,
                published DATETIME NOT NULL,
                author_display_name CHAR(100) NOT NULL,
                author_clean_name CHAR(100),
                author_gender CHAR(1),
                likes INTEGER NOT NULL,
                text TEXT NOT NULL,
                clean_text TEXT,
                sentiment REAL,
                created DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated DATETIME
            )
            """)
            
            # Create comment_keywords table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                video_id CHAR(150) NOT NULL,
                text TEXT NOT NULL,
                score REAL,
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create video table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS video (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                video_id CHAR(150) NOT NULL UNIQUE,
                title TEXT,
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create analysis table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                video_id CHAR(150) NOT NULL,
                name TEXT,
                gender TEXT,
                age TEXT,
                language TEXT,
                issues TEXT,
                wishes TEXT,
                pains TEXT,
                expressions TEXT,
                created DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated DATETIME,
                UNIQUE(video_id)
            )
            """)
            
            conn.commit()

    def save_comment(self, comment):
        sql = "INSERT INTO comment(created, published, video_id, author_display_name, likes, text) VALUES (?,?,?,?,?,?)"
        params = (
            datetime.now(),
            comment.published,
            comment.video_id,
            comment.author_display_name,
            comment.likes,
            comment.text,
        )
        self._execute_query(sql, params, commit=True)

    def save_video_title(self, video_id: str, title: str):
        """Saves a new video with its ID and title."""
        sql = "INSERT INTO video (video_id, title) VALUES (?, ?)"
        params = (video_id, title)
        self._execute_query(sql, params, commit=True)

    def get_comments(self, video_id, no_sentiment=False, no_gender=False):
        sql_base = "SELECT * FROM comment WHERE video_id = ?"
        params = (video_id,)

        if no_sentiment:
            sql = f"{sql_base} AND sentiment IS NULL"
        elif no_gender:
            sql = f"{sql_base} AND author_gender IS NULL"
        else:
            sql = sql_base  # No change needed for params

        rows = self._execute_query(sql, params, fetch_all=True)
        return [self._row_to_dict(row) for row in rows] if rows else []

    def save_analysis(self, video_id: str, analysis_data: dict) -> None:
        """Save analysis results to the database."""
        # Convert lists to JSON strings for storage, but keep scalar values as is
        analysis_json = {}
        for key, value in analysis_data.items():
            if isinstance(value, (list, dict)):
                analysis_json[key] = json.dumps(value, ensure_ascii=False)
            else:
                analysis_json[key] = value

        sql = """
        INSERT INTO analysis (
            video_id, name, gender, age, language,
            issues, wishes, pains, expressions, 
            created, updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(video_id) DO UPDATE SET
            name = excluded.name,
            gender = excluded.gender,
            age = excluded.age,
            language = excluded.language,
            issues = excluded.issues,
            wishes = excluded.wishes,
            pains = excluded.pains,
            expressions = excluded.expressions,
            updated = excluded.updated
        """

        now = datetime.now()
        params = (
            video_id,
            analysis_json.get("name"),
            analysis_json.get("gender"),
            analysis_json.get("age"),
            analysis_json.get("language"),
            analysis_json.get("issues"),
            analysis_json.get("wishes"),
            analysis_json.get("pains"),
            analysis_json.get("expressions"),
            now,
            now,
        )
        self._execute_query(sql, params, commit=True)

    def get_user_demographics(self, video_id: str) -> Tuple[str, str]:
        """Get the most common gender and name from comments for a video."""
        genders_count = {"M": 0, "F": 0}
        names = {"F": {}, "M": {}}

        sql = "SELECT author_clean_name, author_gender FROM comment WHERE video_id = ? AND author_gender IS NOT NULL"
        params = (video_id,)

        results = self._execute_query(sql, params, fetch_all=True)

        if results:
            for name, gender in results:
                if gender in genders_count:  # Corrected indentation
                    genders_count[gender] += 1

                if name and gender in names:  # Corrected indentation
                    firstname = name.split()[0] if name and " " in name else name
                    if firstname:  # Corrected indentation
                        names[gender][firstname] = names[gender].get(firstname, 0) + 1

        dominant_gender = (
            "M" if genders_count.get("M", 0) > genders_count.get("F", 0) else "F"
        )

        most_common_name = ""
        highest_count = 0
        for name, count in names.get(dominant_gender, {}).items():
            if count > highest_count:
                most_common_name = name
                highest_count = count

        return most_common_name, dominant_gender

    def get_analysis(self, video_id: str) -> Optional[Dict[str, Union[List[str], str]]]:
        """Get LLM analysis results for a video."""
        sql = (
            "SELECT name, gender, age, language, issues, wishes, pains, expressions FROM analysis WHERE video_id = ?"
        )
        params = (video_id,)
        row = self._execute_query(sql, params, fetch_one=True)

        if not row:
            return None

        return {
            "name": row[0] or "",
            "gender": row[1] or "",
            "age": row[2] or "",
            "language": row[3] or "",
            "issues": json.loads(row[4]) if row[4] else [],
            "wishes": json.loads(row[5]) if row[5] else [],
            "pains": json.loads(row[6]) if row[6] else [],
            "expressions": json.loads(row[7]) if row[7] else [],
        }

    def get_video_title(self, video_id: str) -> str:
        """Get the title of a video."""
        sql = "SELECT title FROM video WHERE video_id = ?"
        params = (video_id,)
        row = self._execute_query(sql, params, fetch_one=True)
        return row[0] if row else "Unknown Title"

    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in the database."""
        sql = "SELECT 1 FROM video WHERE video_id = ?"
        params = (video_id,)
        return bool(self._execute_query(sql, params, fetch_one=True))

    def get_all_videos(self) -> List[Tuple[str, str]]:
        """Get all videos with their titles."""
        sql = "SELECT video_id, title FROM video ORDER BY created DESC"
        return self._execute_query(sql, fetch_all=True) or []

    def get_keywords(self, video_id: str) -> List[str]:
        """Get keywords for a video."""
        sql = "SELECT text FROM comment_keywords WHERE video_id = ? ORDER BY score ASC LIMIT 20"
        params = (video_id,)
        results = self._execute_query(sql, params, fetch_all=True)
        return [row[0] for row in results] if results else []

    def update_comment_processed_text(
        self,
        comment_id: int,
        clean_text: str,
        author_clean_name: str,
        updated_time: datetime,
    ):
        """Updates the clean_text and author_clean_name of a comment."""
        sql = (
            "UPDATE comment SET clean_text=?, author_clean_name=?, updated=? WHERE id=?"
        )
        params = (clean_text, author_clean_name, updated_time, comment_id)
        self._execute_query(sql, params, commit=True)

    def update_comment_sentiment(
        self, comment_id: int, sentiment_score: float, updated_time: datetime
    ):
        """Updates the sentiment score of a comment."""
        sql = "UPDATE comment SET sentiment=?, updated=? WHERE id=?"
        params = (sentiment_score, updated_time, comment_id)
        self._execute_query(sql, params, commit=True)

    def update_comment_gender(
        self, comment_id: int, gender: str, updated_time: datetime
    ):
        """Updates the author_gender of a comment."""
        sql = "UPDATE comment SET author_gender=?, updated=? WHERE id=?"
        params = (gender, updated_time, comment_id)
        self._execute_query(sql, params, commit=True)

    def save_comment_keyword(self, video_id: str, text: str, score: float):
        """Saves a new comment keyword."""
        sql = "INSERT INTO comment_keywords (video_id, text, score) VALUES (?,?,?)"
        params = (video_id, text, score)
        self._execute_query(sql, params, commit=True)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

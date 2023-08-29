import sqlite3
from datetime import datetime

    
class DBManager:
    def connect(self):
        self.con = sqlite3.connect("youtube.db")
        self.cur = self.con.cursor()
        
    def close(self):
        self.con.close()

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
        
        return res.fetchall()
        
    
if __name__ == '__main__':
    db = DBManager()
    db.connect()
    db.create_db()
    db.close()
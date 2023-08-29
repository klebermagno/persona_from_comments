
from datetime import datetime
from comment import Comment
from db_manager import DBManager
from text_cleaner import TextCleaner


class Mining:
    
    def __init__(self) -> None:
        self.cleaner = TextCleaner()
        self.db = DBManager()
    
    def clear_name(self, name):
        clean_name = self.cleaner.clean_entities_symbols(name)
        return clean_name
    
    def execute(self, video_id):       
        self.db.connect()
        for row in self.db.get_comments(video_id):
            comment = Comment(row)
            clean_text = self.cleaner.strip_entities_links(comment.text).replace('..', '.')
            clean_text = clean_text.replace('kk', '')
            clean_text = clean_text.replace('rs', '')
            author_clean_name = self.clear_name(comment.author_display_name)
            self.db.cur.execute('UPDATE comment SET clean_text=?, author_clean_name=?, updated=? WHERE id=?',
                                (''.join(clean_text), author_clean_name, datetime.now(), row[0]))
        self.db.con.commit()
        self.db.close()

from db_manager import DBManager
from gender_analyzer import GenderAnalyzer
from sentiment_analyzer import SentimentAnalyser
from comment import Comment
from datetime import datetime
from keyword_extractor import KeywordExtractor


class Analysis:
    
    def __init__(self) -> None:
        self.db = DBManager()
        self.db.connect()
         
    def _set_sentiments(self, video_id) -> None:
        sentiment_analyzer = SentimentAnalyser()        
        
        for row in self.db.get_comments(video_id, no_sentiment=False):
            comment = Comment(row)
            polarity = sentiment_analyzer.sentiment(comment.clean_text)
            self.db.cur.execute('UPDATE comment SET sentiment=?, updated=? WHERE id=?',
                            (polarity, datetime.now(), comment.id))
        self.db.con.commit()   
    
    def _set_genders(self, video_id) -> dict:
        gender_analyzer = GenderAnalyzer()
        authors_names = []
        
        for row in self.db.get_comments(video_id, no_gender=True):
            comment = Comment(row)
            authors_names.append({'id' : comment.id, 'name' : comment.author_clean_name})    
        
        gender_list = gender_analyzer.get_names_genders(authors_names)
        for key in gender_list:    
            self.db.cur.execute('UPDATE comment SET author_gender=?, updated=? WHERE id=?',
                                ( ('M' if gender_list[key] == 'male' else 'F'), datetime.now(), int(key)))
        self.db.con.commit()
        
    def _set_comment_keywords(self, video_id) -> None:
        # building corpus        
        corpus = []
        for row in self.db.get_comments(video_id):
            corpus.append(Comment(row).clean_text)

        keyword_extractor = KeywordExtractor()
        keywords = keyword_extractor.get_yake_keywords('\n'.join(corpus))
        for keyword in keywords:
            self.db.cur.execute("INSERT INTO comment_keywords (video_id, text, score) VALUES (?,?,?)",
                            (video_id, keyword[0], keyword[1]))
        self.db.con.commit()
        
    def execute(self, video_id) -> None:
        self._set_sentiments(video_id)
        self._set_genders(video_id)
        self._set_comment_keywords(video_id)    
        self.db.close()
        
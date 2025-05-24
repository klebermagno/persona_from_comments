import logging
from db_manager import DBManager
from gender_analyzer import GenderAnalyzer
from sentiment_analyzer import SentimentAnalyser

# Comment class might not be directly needed here if we use dicts from db_manager
from datetime import datetime
from keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)


class Analysis:

    def __init__(self) -> None:
        self.db = DBManager()
        # self.db.connect() # REMOVED

    def _set_sentiments(self, video_id) -> None:
        logger.info(f"Starting sentiment analysis for video {video_id}")
        sentiment_analyzer = SentimentAnalyser()

        comments_data = self.db.get_comments(
            video_id, no_sentiment=False
        )  # get_comments returns list of dicts
        for comment_dict in comments_data:
            comment_id = comment_dict["id"]
            clean_text = comment_dict["clean_text"]
            if clean_text:  # Ensure text is not empty for sentiment analysis
                polarity = sentiment_analyzer.sentiment(clean_text)
                self.db.update_comment_sentiment(comment_id, polarity, datetime.now())
            else:
                logger.debug(
                    f"Skipping sentiment analysis for comment_id {comment_id} due to empty clean_text."
                )

        # self.db.con.commit() # REMOVED - Handled by DBManager method
        logger.info(f"Finished sentiment analysis for video {video_id}")

    def _set_genders(self, video_id) -> None:
        logger.info(f"Starting gender analysis for video {video_id}")
        gender_analyzer = GenderAnalyzer()
        authors_names = (
            []
        )  # This list will contain dicts like {'id': comment_id, 'name': author_name}

        comments_data = self.db.get_comments(
            video_id, no_gender=True
        )  # get_comments returns list of dicts
        for comment_dict in comments_data:
            comment_id = comment_dict["id"]
            author_clean_name = comment_dict["author_clean_name"]
            if author_clean_name:  # Ensure name is not empty for gender analysis
                authors_names.append(
                    {"id": str(comment_id), "name": author_clean_name}
                )  # GenderAnalyzer expects id as string
            else:
                logger.debug(
                    f"Skipping gender analysis for comment_id {comment_id} due to empty author_clean_name."
                )

        if not authors_names:
            logger.info(f"No names found for gender analysis for video {video_id}")
            return

        gender_list = gender_analyzer.get_names_genders(authors_names)
        for item in gender_list:  # GenderAnalyzer returns a list of dicts
            comment_id_str = item["id"]
            gender_code = "M" if item["gender"] == "male" else "F"
            self.db.update_comment_gender(
                int(comment_id_str), gender_code, datetime.now()
            )

        # self.db.con.commit() # REMOVED - Handled by DBManager method
        logger.info(f"Finished gender analysis for video {video_id}")

    def _set_comment_keywords(self, video_id) -> None:
        logger.info(f"Starting keyword extraction for video {video_id}")
        corpus = []
        comments_data = self.db.get_comments(
            video_id
        )  # get_comments returns list of dicts
        for comment_dict in comments_data:
            clean_text = comment_dict["clean_text"]
            if clean_text:  # Ensure text is not empty
                corpus.append(clean_text)

        if not corpus:
            logger.info(f"No text found for keyword extraction for video {video_id}")
            return

        keyword_extractor = KeywordExtractor()
        keywords = keyword_extractor.get_yake_keywords("\n".join(corpus))
        for (
            keyword_text,
            keyword_score,
        ) in keywords:  # Adjusted to expect tuple from get_yake_keywords
            self.db.save_comment_keyword(video_id, keyword_text, keyword_score)

        # self.db.con.commit() # REMOVED - Handled by DBManager method
        logger.info(f"Finished keyword extraction for video {video_id}")

    def execute(self, video_id) -> None:
        logger.info(f"Starting full analysis phase for video {video_id}")
        self._set_sentiments(video_id)
        self._set_genders(video_id)
        self._set_comment_keywords(video_id)
        # self.db.close() # REMOVED - Handled by DBManager context manager
        logger.info(f"Finished full analysis phase for video {video_id}")

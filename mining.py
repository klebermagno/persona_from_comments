import logging
from datetime import datetime
from comment import Comment
from db_manager import DBManager
from text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class Mining:

    def __init__(self) -> None:
        self.cleaner = TextCleaner()
        self.db = DBManager()  # Ensure DBManager is initialized

    def clear_name(self, name):
        clean_name = self.cleaner.clean_entities_symbols(name)
        return clean_name

    def execute(self, video_id):
        logger.info(f"Starting mining for video {video_id}")
        # self.db.connect() # REMOVED

        # Assuming get_comments returns list of dictionaries now, as per DBManager refactoring
        comments_data = self.db.get_comments(video_id)

        for comment_dict in comments_data:
            # Create Comment object from dictionary
            # This assumes Comment class can be initialized from a dict or has a method for it
            # Based on previous refactoring, Comment.from_db_row expects a tuple.
            # However, db_manager._row_to_dict is used in get_comments.
            # Let's adjust to construct Comment object field by field from dict for clarity
            # Or better, ensure Comment has a from_dict method or adapt from_db_row if possible.
            # For now, let's assume get_comments returns dicts and we'll manually construct or adapt.
            # If Comment.from_db_row is strictly for tuples, we might need to fetch raw rows,
            # or adapt Comment.from_db_row to handle dicts, or add from_dict.
            # Given current Comment.from_db_row expects a tuple (db_row[0], etc.),
            # and db_manager.get_comments returns list of dicts, this is a mismatch.
            # For this step, I will assume get_comments can return raw tuples or adapt.
            # Re-checking db_manager.py: get_comments returns list of dicts via _row_to_dict.
            # So, Comment.from_db_row(row) is incorrect if row is a dict.
            # We'll need to access dict keys.

            comment_id = comment_dict["id"]
            original_text = comment_dict["text"]
            author_display_name = comment_dict["author_display_name"]

            clean_text = self.cleaner.strip_entities_links(original_text).replace(
                "..", "."
            )
            clean_text = clean_text.replace("kk", "")
            clean_text = clean_text.replace("rs", "")
            author_clean_name = self.clear_name(author_display_name)

            self.db.update_comment_processed_text(
                comment_id, "".join(clean_text), author_clean_name, datetime.now()
            )

        # self.db.con.commit() # REMOVED - Handled by DBManager methods
        # self.db.close() # REMOVED - Handled by DBManager context manager
        logger.info(f"Finished mining for video {video_id}")

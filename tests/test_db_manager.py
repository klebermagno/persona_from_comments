import unittest
import sqlite3
from src.db_manager import DBManager
from datetime import datetime, timezone  # Use timezone-aware datetimes for consistency
import json
import time # Ensure time is imported


# Using a simple mock object for comment data to avoid direct dependency on Comment class structure in tests
class MockComment:
    def __init__(
        self,
        video_id,
        published,
        author_display_name,
        likes,
        text,
        id=None,
        clean_text=None,
        author_clean_name=None,
        author_gender=None,
        sentiment=None,
    ):
        self.id = id
        self.video_id = video_id
        self.published = published
        self.author_display_name = author_display_name
        self.author_clean_name = author_clean_name
        self.author_gender = author_gender
        self.likes = likes
        self.text = text
        self.clean_text = clean_text
        self.sentiment = sentiment
        # created and updated are usually handled by DB or DBManager


class TestDBManager(unittest.TestCase):

    def setUp(self):
        """Set up a new in-memory database for each test."""
        self.db = DBManager(db_name=":memory:")
        # self.db.create_db() # create_db might be redundant now, tables are ensured in __init__ for :memory:

    def tearDown(self):
        if self.db:
            self.db.close() # Ensure the in-memory connection is closed after tests

    def test_save_and_get_video_title(self):
        self.db.save_video_title("video1", "Test Video Title 1")
        title = self.db.get_video_title("video1")
        self.assertEqual(title, "Test Video Title 1")

        unknown_title = self.db.get_video_title("nonexistent_video")
        self.assertEqual(unknown_title, "Unknown Title")

    def test_video_exists(self):
        self.db.save_video_title("video2", "Test Video Title 2")
        self.assertTrue(self.db.video_exists("video2"))
        self.assertFalse(self.db.video_exists("nonexistent_video2"))

    def test_save_and_get_comments(self):
        now = datetime.now(timezone.utc)
        mock_comment = MockComment(
            video_id="vid_comment_test",
            published=now,
            author_display_name="CommentAuthor",
            likes=15,
            text="This is a test comment for save_and_get.",
        )
        self.db.save_comment(mock_comment)

        comments = self.db.get_comments("vid_comment_test")
        self.assertEqual(len(comments), 1)
        self.assertEqual(
            comments[0]["text"], "This is a test comment for save_and_get."
        )
        self.assertEqual(comments[0]["author_display_name"], "CommentAuthor")
        self.assertEqual(comments[0]["likes"], 15)
        # Timestamps might be tricky to compare exactly if not controlled,
        # but we can check if they are datetime objects.
        self.assertIsInstance(
            datetime.fromisoformat(comments[0]["published"].replace("Z", "+00:00")),
            datetime,
        )  # published is from mock
        self.assertIsInstance(
            datetime.fromisoformat(comments[0]["created"].replace("Z", "+00:00")),
            datetime,
        )  # created is by DBManager

    def test_save_and_get_analysis(self):
        analysis_data = {
            "name": "John",
            "gender": "M",
            "age": "25-34",
            "language": "English",
            "issues": ["issue_test1"],
            "wishes": ["wish_test1"],
            "pains": ["pain_test1"],
            "expressions": ["expr_test1"],
        }
        self.db.save_analysis("vid_analysis_test", analysis_data)

        retrieved_analysis = self.db.get_analysis("vid_analysis_test")
        self.assertEqual(retrieved_analysis, analysis_data)

        # Test that scalar values are handled correctly
        self.assertEqual(retrieved_analysis["name"], "John")
        self.assertEqual(retrieved_analysis["gender"], "M")
        self.assertEqual(retrieved_analysis["age"], "25-34")
        self.assertEqual(retrieved_analysis["language"], "English")

        # Test that list values are still handled correctly
        self.assertEqual(retrieved_analysis["issues"], ["issue_test1"])
        self.assertEqual(retrieved_analysis["wishes"], ["wish_test1"])
        self.assertEqual(retrieved_analysis["pains"], ["pain_test1"])
        self.assertEqual(retrieved_analysis["expressions"], ["expr_test1"])

        non_existent_analysis = self.db.get_analysis("nonexistent_analysis_vid")
        self.assertIsNone(
            non_existent_analysis
        )  # As per current DBManager.get_analysis behavior

    def test_get_all_videos(self):
        # First video saved
        self.db.save_video_title("vid_all1", "Title B")
        time.sleep(0.2)  # Small delay between saves
        # Second video saved later, should appear first due to ORDER BY created DESC
        self.db.save_video_title("vid_all2", "Title A")

        videos = self.db.get_all_videos()
        self.assertEqual(len(videos), 2)

    def _add_base_comment_for_updates(
        self, video_id="vid_update", comment_text="Initial comment text"
    ):
        now = datetime.now(timezone.utc)
        mock_comment = MockComment(
            video_id=video_id,
            published=now,
            author_display_name="UpdateAuthor",
            likes=5,
            text=comment_text,
        )
        self.db.save_comment(mock_comment)
        # Get the ID of the saved comment (assuming get_comments returns it)
        comments = self.db.get_comments(video_id)
        self.assertTrue(
            len(comments) > 0, "Failed to save base comment for update tests"
        )
        return comments[0]["id"]

    def test_update_comment_processed_text(self):
        comment_id = self._add_base_comment_for_updates()
        updated_time = datetime.now(timezone.utc)

        self.db.update_comment_processed_text(
            comment_id, "Processed text", "CleanAuthorName", updated_time
        )

        comments = self.db.get_comments("vid_update")
        updated_comment = next((c for c in comments if c["id"] == comment_id), None)

        self.assertIsNotNone(updated_comment)
        self.assertEqual(updated_comment["clean_text"], "Processed text")
        self.assertEqual(updated_comment["author_clean_name"], "CleanAuthorName")
        # Comparing datetime strings after formatting to ISO, as DB might store differently
        self.assertEqual(
            datetime.fromisoformat(
                updated_comment["updated"].replace("Z", "+00:00")
            ).replace(microsecond=0),
            updated_time.replace(microsecond=0),
        )

    def test_update_comment_sentiment(self):
        comment_id = self._add_base_comment_for_updates()
        updated_time = datetime.now(timezone.utc)
        sentiment_score = 0.95

        self.db.update_comment_sentiment(comment_id, sentiment_score, updated_time)

        comments = self.db.get_comments("vid_update")
        updated_comment = next((c for c in comments if c["id"] == comment_id), None)

        self.assertIsNotNone(updated_comment)
        self.assertEqual(updated_comment["sentiment"], sentiment_score)
        self.assertEqual(
            datetime.fromisoformat(
                updated_comment["updated"].replace("Z", "+00:00")
            ).replace(microsecond=0),
            updated_time.replace(microsecond=0),
        )

    def test_update_comment_gender(self):
        comment_id = self._add_base_comment_for_updates()
        updated_time = datetime.now(timezone.utc)
        gender = "F"

        self.db.update_comment_gender(comment_id, gender, updated_time)

        comments = self.db.get_comments("vid_update")
        updated_comment = next((c for c in comments if c["id"] == comment_id), None)

        self.assertIsNotNone(updated_comment)
        self.assertEqual(updated_comment["author_gender"], gender)
        self.assertEqual(
            datetime.fromisoformat(
                updated_comment["updated"].replace("Z", "+00:00")
            ).replace(microsecond=0),
            updated_time.replace(microsecond=0),
        )

    def test_save_and_get_keywords(self):
        video_id_keywords = "vid_keywords_test"
        self.db.save_comment_keyword(video_id_keywords, "keyword1", 0.8)
        self.db.save_comment_keyword(video_id_keywords, "keyword2", 0.9)  # Higher score
        self.db.save_comment_keyword(video_id_keywords, "keyword3", 0.7)

        keywords = self.db.get_keywords(
            video_id_keywords
        )  # Returns list of strings (text)
        self.assertEqual(len(keywords), 3)
        # get_keywords sorts by score ASC
        self.assertIn("keyword1", keywords)
        self.assertIn("keyword2", keywords)
        self.assertIn("keyword3", keywords)

        # To check order by score ASC:
        # If get_keywords returned tuples (text, score), we could check order directly.
        # For now, just checking presence as per current get_keywords implementation.
        # If specific order testing is needed, get_keywords would need to return scores too.
        # Current get_keywords: "SELECT text FROM comment_keywords WHERE video_id = ? ORDER BY score ASC LIMIT 20"
        # So, "keyword3" (0.7) should be first, "keyword1" (0.8) second, "keyword2" (0.9) third.
        self.assertEqual(keywords, ["keyword3", "keyword1", "keyword2"])


if __name__ == "__main__":
    unittest.main()

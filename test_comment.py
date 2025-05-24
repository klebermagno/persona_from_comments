import unittest
from comment import Comment
from datetime import datetime, timezone


class TestComment(unittest.TestCase):

    def test_creation_with_defaults(self):
        comment = Comment()
        self.assertEqual(comment.id, 0)
        self.assertEqual(comment.video_id, "")
        self.assertIsNone(comment.published)  # Default for datetime is None
        self.assertEqual(comment.author_display_name, "")
        self.assertEqual(comment.author_clean_name, "")
        self.assertEqual(comment.author_gender, "")
        self.assertEqual(comment.likes, -1)
        self.assertEqual(comment.text, "")
        self.assertEqual(comment.clean_text, "")
        self.assertEqual(comment.sentiment, 0.0)
        self.assertIsNone(comment.created)  # Default for datetime is None
        self.assertIsNone(comment.updated)  # Default for datetime is None

    def test_from_db_row_valid(self):
        # Create a sample valid database row tuple (12 fields)
        now = datetime.now(timezone.utc)
        sample_row = (
            1,
            "video123",
            now,
            "Test Author",
            "TestAuthorClean",
            "M",
            100,
            "This is a test comment.",
            "This is a test comment.",
            0.75,
            now,
            now,
        )
        comment = Comment.from_db_row(sample_row)

        self.assertEqual(comment.id, sample_row[0])
        self.assertEqual(comment.video_id, sample_row[1])
        self.assertEqual(comment.published, sample_row[2])
        self.assertEqual(comment.author_display_name, sample_row[3])
        self.assertEqual(comment.author_clean_name, sample_row[4])
        self.assertEqual(comment.author_gender, sample_row[5])
        self.assertEqual(comment.likes, sample_row[6])
        self.assertEqual(comment.text, sample_row[7])
        self.assertEqual(comment.clean_text, sample_row[8])
        self.assertEqual(comment.sentiment, sample_row[9])
        self.assertEqual(comment.created, sample_row[10])
        self.assertEqual(comment.updated, sample_row[11])

    def test_from_db_row_none(self):
        comment = Comment.from_db_row(None)
        # Assert that this returns a Comment object with default values
        self.assertIsInstance(comment, Comment)
        self.assertEqual(comment.id, 0)
        self.assertEqual(comment.video_id, "")
        self.assertIsNone(comment.published)
        self.assertEqual(comment.sentiment, 0.0)

    def test_from_db_row_incomplete(self):
        incomplete_row = (1, "video123")  # Only 2 fields
        # This should raise an IndexError because the from_db_row method directly accesses indices
        with self.assertRaises(IndexError):
            Comment.from_db_row(incomplete_row)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import json
from src.llm_analysis import LLMAnalysis
from src.db_manager import DBManager  # For mocking spec
from openai import OpenAI  # For mocking spec

# For controlling token counting in tests
MOCK_BASE_PROMPT_TEXT = """
            Analyze the following YouTube comments. Extract and summarize:
            - Common issues
            - Common wishes
            - Common pains
            - Common expressions or catchphrases
            - Name (Summarize all names into one)
            - Gender (Summarize all genders into one, based on the average comments it should be male or female)
            - Age (Summarize all ages into one, based on the content of the comments text which is related to age)
            - Language (Summarize all languages into one, based on the content of the comments which is related to language)

            Return your response as a single JSON object with four keys: "issues", "wishes", "pains", and "expressions". Each key should correspond to a list of strings (the extracted items).

            Comments:
        """


class TestLLMAnalysis(unittest.TestCase):

    def setUp(self):
        self.mock_db_manager = MagicMock(spec=DBManager)
        self.mock_openai_client = MagicMock(spec=OpenAI)
        # Mock the specific method chain used in LLMAnalysis
        self.mock_openai_client.chat.completions.create = MagicMock()

        self.patcher_db = patch(
            "src.llm_analysis.DBManager", return_value=self.mock_db_manager
        )
        # Patch the OpenAI class where it's instantiated in LLMAnalysis
        self.patcher_openai = patch(
            "src.llm_analysis.OpenAI", return_value=self.mock_openai_client
        )

        # Mock for tiktoken
        self.mock_encoding = MagicMock()
        self.patcher_tiktoken = patch(
            "src.llm_analysis.tiktoken.encoding_for_model", return_value=self.mock_encoding
        )

        self.MockDBManager = self.patcher_db.start()
        self.MockOpenAI = self.patcher_openai.start()
        self.MockTiktoken = self.patcher_tiktoken.start()

        # Configure the mock_encoding's encode method
        # Default behavior: returns a list with length equal to text length (1 token per char)
        self.mock_encoding.encode.side_effect = lambda text: list(range(len(text)))

        self.analyzer = LLMAnalysis()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_openai.stop()
        self.patcher_tiktoken.stop()

    def test_execute_no_comments(self):
        self.mock_db_manager.get_comments.return_value = []
        result = self.analyzer.execute("vid_no_comments")
        self.assertIsNone(result)
        self.mock_db_manager.save_analysis.assert_not_called()

    def test_execute_successful_analysis(self):
        comments_data = [
            {"id": 1, "text": "Comment 1", "clean_text": "Comment 1", "author_clean_name": "TestAuthor1"},
            {"id": 2, "text": "Comment 2", "clean_text": "Comment 2", "author_clean_name": "TestAuthor2"},
        ]
        self.mock_db_manager.get_comments.return_value = comments_data

        mock_llm_response_content_dict = {
            "issues": ["i1"], "wishes": ["w1"], "pains": ["p1"], "expressions": ["e1"],
            "name": "John Doe", "gender": "Male", "age": "25-34", "language": "English"
        }
        mock_llm_response_content_json = json.dumps(mock_llm_response_content_dict)

        mock_choice = MagicMock()
        mock_choice.message.content = mock_llm_response_content_json
        self.mock_openai_client.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        result = self.analyzer.execute("vid_success")

        self.assertEqual(result, mock_llm_response_content_dict)
        self.mock_db_manager.save_analysis.assert_called_once_with(
            "vid_success", result
        )
        self.mock_openai_client.chat.completions.create.assert_called_once()

    def test_execute_openai_api_error(self):
        self.mock_db_manager.get_comments.return_value = [
            {"id": 1, "text": "Comment 1", "clean_text": "Comment 1"}
        ]
        self.mock_openai_client.chat.completions.create.side_effect = Exception(
            "OpenAI API Error"
        )

        result = self.analyzer.execute("vid_api_error")
        self.assertIsNone(result) # Expect None as execute returns None if no results
        self.mock_db_manager.save_analysis.assert_not_called()

    def test_batch_comments_logic(self):
        # Set specific token counts for this test via the mock_encoding
        # Each character will count as 1 token due to side_effect lambda text: [1]*len(text) in setUp

        # Use the actual prompt from LLMAnalysis for accurate base token count
        base_prompt_tokens = len(
            MOCK_BASE_PROMPT_TEXT
        )  # As per current mock: 1 token per char

        # Configure analyzer's limits for this test
        self.analyzer.max_tokens_per_request = 1000
        self.analyzer.max_tokens_response = 100  # Reduced for easier testing

        # This is the max tokens available for the comments text itself in a batch
        max_batch_tokens_for_text = (
            self.analyzer.max_tokens_per_request
            - base_prompt_tokens
            - self.analyzer.max_tokens_response
        )

        # Ensure max_batch_tokens_for_text is positive, otherwise the test setup is wrong
        self.assertGreater(
            max_batch_tokens_for_text,
            0,
            "Max batch tokens for text is not positive, check prompt/limits",
        )

        comments = [
            {
                "id": 1,
                "text": "a" * (max_batch_tokens_for_text - 10),
            },  # Fits in one batch
            {
                "id": 2,
                "text": "b" * (max_batch_tokens_for_text - 5),
            },  # Fits in another batch
            {"id": 3, "text": "c" * 20},  # Fits with comment 2 or in a new batch
        ]

        # Re-calculate token counts based on actual text using the mock
        comment1_tokens = len(comments[0]["text"])
        comment2_tokens = len(comments[1]["text"])
        comment3_tokens = len(comments[2]["text"])

        batches = self.analyzer.batch_comments(comments)

        # Expected:
        # Batch 1: comment1 (fits)
        # Batch 2: comment2 (fits because comment1 + comment2 > max_batch_tokens_for_text)
        # Batch 3: comment3 (fits because comment2 + comment3 > max_batch_tokens_for_text, assuming comment3 itself isn't too large)
        # This depends on the exact addition logic.
        # If current_tokens + comment_tokens > max_batch_tokens:
        # Batch 1: comment1
        # current_tokens = comment1_tokens.
        # For comment2: comment1_tokens + comment2_tokens > max_batch_tokens_for_text. So new batch.
        # Batch 2: comment2
        # current_tokens = comment2_tokens
        # For comment3: comment2_tokens + comment3_tokens <= max_batch_tokens_for_text. So comment3 adds to Batch 2.

        if comment1_tokens + comment2_tokens > max_batch_tokens_for_text:
            if comment2_tokens + comment3_tokens > max_batch_tokens_for_text:
                self.assertEqual(
                    len(batches), 3, "Should be 3 batches if c3 makes a new batch"
                )
                self.assertEqual(len(batches[0]), 1)
                self.assertEqual(len(batches[1]), 1)
                self.assertEqual(len(batches[2]), 1)
            else:  # c3 fits with c2
                self.assertEqual(
                    len(batches), 2, "Should be 2 batches if c3 fits with c2"
                )
                self.assertEqual(len(batches[0]), 1)
                self.assertEqual(len(batches[1]), 2)
        else:  # c1 and c2 fit together
            self.assertEqual(
                len(batches), 1, "Should be 1 batch if c1+c2 fit, and c3 fits too"
            )
            self.assertEqual(len(batches[0]), 3)

    def test_parse_response_valid_json(self):
        json_string = '{"issues": ["issue1"], "wishes": ["wish1"], "pains": [], "expressions": ["expr1"], "name": "Test Name", "gender": "Female", "age": "30-40", "language": "Spanish"}'
        parsed = self.analyzer._parse_response(json_string)
        self.assertEqual(parsed["issues"], ["issue1"])
        self.assertEqual(parsed["wishes"], ["wish1"])
        self.assertEqual(parsed["pains"], [])
        self.assertEqual(parsed["expressions"], ["expr1"])
        self.assertEqual(parsed["name"], "Test Name")
        self.assertEqual(parsed["gender"], "Female")
        self.assertEqual(parsed["age"], "30-40")
        self.assertEqual(parsed["language"], "Spanish")

    def test_parse_response_invalid_json(self):
        invalid_json_string = '{"issues": ["issue1"], "wishes": incomplete_json'
        parsed = self.analyzer._parse_response(invalid_json_string)
        # Expect default structure due to JSONDecodeError
        expected_on_invalid_json = {"issues": [], "wishes": [], "pains": [], "expressions": [], "name": "", "gender": "", "age": "", "language": ""}
        self.assertEqual(parsed, expected_on_invalid_json)

    def test_parse_response_partial_keys(self):
        json_string = '{"issues": ["issue1"], "name": "Only Name", "extras": ["unexpected"]}'  # Missing other main keys
        parsed = self.analyzer._parse_response(json_string)
        self.assertEqual(parsed["issues"], ["issue1"])
        self.assertEqual(parsed["name"], "Only Name")
        self.assertEqual(parsed["wishes"], [])  # default
        self.assertEqual(parsed["pains"], []) # default
        self.assertEqual(parsed["expressions"], []) # default
        self.assertEqual(parsed["gender"], "") # default
        self.assertEqual(parsed["age"], "") # default
        self.assertEqual(parsed["language"], "") # default

    def test_merge_results(self):
        results_list = [
            {
                "issues": ["i1"], "wishes": ["w1"], "pains": ["p1"], "expressions": ["e1"],
                "name": "John", "gender": "Male", "age": "20-30", "language": "English"
            },
            {
                "issues": ["i2", "i1"], "wishes": ["w2"], "pains": [], "expressions": ["e2"],
                "name": "John", "gender": "Male", "age": "25-35", "language": "English"
            },
            {
                "issues": ["i3"], "wishes": ["w3"], "pains": ["p3"], "expressions": ["e3"],
                "name": "Jane", "gender": "Female", "age": "20-30", "language": "Spanish"
            }
        ]
        merged = self.analyzer.merge_results(results_list)

        # dict.fromkeys preserves order from Python 3.7+ for list fields
        self.assertEqual(merged["issues"], ["i1", "i2", "i3"])
        self.assertEqual(merged["wishes"], ["w1", "w2", "w3"])
        self.assertEqual(merged["pains"], ["p1", "p3"])
        self.assertEqual(merged["expressions"], ["e1", "e2", "e3"])
        # For scalar fields, the most common non-empty value is taken
        self.assertEqual(merged["name"], "John")
        self.assertEqual(merged["gender"], "Male")
        self.assertEqual(merged["age"], "20-30") # John (20-30), John (25-35), Jane (20-30) -> "20-30" is most common
        self.assertEqual(merged["language"], "English")


if __name__ == "__main__":
    unittest.main()

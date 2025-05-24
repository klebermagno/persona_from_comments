import unittest
from unittest.mock import (
    patch,
    MagicMock,
    call,
)  # Import call for checking ordered calls
from main import main  # Import the main function to be tested


class TestMainPipeline(unittest.TestCase):

    @patch("main.Generating")
    @patch("main.Analysis")
    @patch("main.Mining")
    @patch("main.Gathering")
    def test_pipeline_calls_execute_on_all_components(
        self, MockGathering, MockMining, MockAnalysis, MockGenerating
    ):
        # Create mock instances for each class
        mock_gathering_instance = MockGathering.return_value
        mock_mining_instance = MockMining.return_value
        mock_analysis_instance = MockAnalysis.return_value
        mock_generating_instance = MockGenerating.return_value

        # Call the main function with a test video ID
        main("test_video_id")

        # Assert that the execute method was called once on each mock instance with "test_video_id"
        mock_gathering_instance.execute.assert_called_once_with("test_video_id")
        mock_mining_instance.execute.assert_called_once_with("test_video_id")
        mock_analysis_instance.execute.assert_called_once_with("test_video_id")
        mock_generating_instance.execute.assert_called_once_with("test_video_id")

    @patch("main.Generating")
    @patch("main.Analysis")
    @patch("main.Mining")
    @patch("main.Gathering")
    def test_pipeline_order_of_execution(
        self, MockGathering, MockMining, MockAnalysis, MockGenerating
    ):
        # Use a manager mock to track call order
        manager = MagicMock()

        # Assign the manager's methods to the execute methods of the mocked instances
        MockGathering.return_value.execute = manager.gathering_execute
        MockMining.return_value.execute = manager.mining_execute
        MockAnalysis.return_value.execute = manager.analysis_execute
        MockGenerating.return_value.execute = manager.generating_execute

        # Call the main function
        main("test_video_id_order")

        # Create a list of expected calls in order
        expected_calls = [
            call.gathering_execute("test_video_id_order"),
            call.mining_execute("test_video_id_order"),
            call.analysis_execute("test_video_id_order"),
            call.generating_execute("test_video_id_order"),
        ]

        # Assert that the calls were made in the expected order
        self.assertEqual(manager.mock_calls, expected_calls)

    @patch("main.Generating")  # Patch in reverse order of decorator application
    @patch("main.Analysis")
    @patch("main.Mining")
    @patch("main.Gathering")
    @patch("main.logging.getLogger")  # Patch the logger
    def test_pipeline_logging(
        self, mock_get_logger, MockGathering, MockMining, MockAnalysis, MockGenerating
    ):
        # mock_get_logger is the mock for logging.getLogger itself
        # We need to mock the logger instance that getLogger returns
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Call the main function
        main("test_video_id_logging")

        # Assert that specific log messages were made
        # Using any_call because the exact call list might include other logs from within components if not mocked out
        mock_logger_instance.info.assert_any_call(
            "Starting full pipeline for video_id: test_video_id_logging"
        )
        mock_logger_instance.info.assert_any_call("Starting Gathering phase...")
        mock_logger_instance.info.assert_any_call("Finished Gathering phase.")
        mock_logger_instance.info.assert_any_call("Starting Mining phase...")
        mock_logger_instance.info.assert_any_call("Finished Mining phase.")
        mock_logger_instance.info.assert_any_call(
            "Starting Content Analysis phase (sentiments, genders, keywords)..."
        )
        mock_logger_instance.info.assert_any_call("Finished Content Analysis phase.")
        mock_logger_instance.info.assert_any_call(
            "Starting Generating phase (persona report)..."
        )
        mock_logger_instance.info.assert_any_call("Finished Generating phase.")
        mock_logger_instance.info.assert_any_call(
            "Full pipeline finished for video_id: test_video_id_logging"
        )

        # Verify that the mocked components' execute methods were still called
        MockGathering.return_value.execute.assert_called_once_with(
            "test_video_id_logging"
        )
        MockMining.return_value.execute.assert_called_once_with("test_video_id_logging")
        MockAnalysis.return_value.execute.assert_called_once_with(
            "test_video_id_logging"
        )
        MockGenerating.return_value.execute.assert_called_once_with(
            "test_video_id_logging"
        )


if __name__ == "__main__":
    unittest.main()

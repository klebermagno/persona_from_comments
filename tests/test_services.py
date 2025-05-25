import unittest
from unittest.mock import patch, MagicMock
from src.services import PersonaGenerator, PersonaData
from src.db_manager import DBManager  # For type hinting and spec for MagicMock
from src.llm_analysis import LLMAnalysis  # For spec for MagicMock


class TestPersonaGenerator(unittest.TestCase):

    def setUp(self):
        # Create mocks for DBManager and LLMAnalysis
        self.mock_db_manager = MagicMock(spec=DBManager)
        self.mock_llm_analysis = MagicMock(spec=LLMAnalysis)

        # Patch DBManager and LLMAnalysis at the 'services' module level
        self.patcher_db = patch("src.services.DBManager", return_value=self.mock_db_manager)
        self.patcher_llm = patch(
            "src.services.LLMAnalysis", return_value=self.mock_llm_analysis
        )

        self.MockDBManager = self.patcher_db.start()
        self.MockLLMAnalysis = self.patcher_llm.start()

        # Create an instance of PersonaGenerator
        self.generator = PersonaGenerator()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_llm.stop()

    def test_generate_persona_no_video_id(self):
        persona = self.generator.generate_persona("")
        self.assertEqual(persona.title, "No Video Selected")
        self.assertEqual(persona.name, "")
        self.assertEqual(persona.gender, "")
        self.assertEqual(persona.wishes, [])
        self.assertEqual(persona.pains, [])
        self.assertEqual(persona.expressions, [])
        self.assertEqual(persona.status, "Please enter a video ID")

    def test_generate_persona_video_exists_analysis_exists(self):
        self.mock_db_manager.video_exists.return_value = True
        self.mock_db_manager.get_video_title.return_value = "Existing Video"
        self.mock_db_manager.get_user_demographics.return_value = ("TestName", "M")
        mock_analysis_data = {
            "wishes": ["wish1"],
            "pains": ["pain1"],
            "expressions": ["expr1"],
            "issues": ["issue1"],
        }
        self.mock_db_manager.get_analysis.return_value = mock_analysis_data

        persona = self.generator.generate_persona("vid123")

        self.assertEqual(persona.title, "Generated Persona for Video: Existing Video")
        self.assertEqual(persona.name, "TestName")
        self.assertEqual(persona.gender, "Male")  # After _format_gender
        self.assertEqual(persona.wishes, ["wish1"])
        self.assertEqual(persona.pains, ["pain1"])
        self.assertEqual(persona.expressions, ["expr1"])
        self.assertEqual(persona.status, "Persona generated for video: vid123")

        self.mock_llm_analysis.execute.assert_not_called()
        self.MockDBManager.assert_called_once()  # Check DBManager was instantiated
        # Check that get_analysis was called inside _ensure_video_analyzed
        self.mock_db_manager.get_analysis.assert_called_once_with("vid123")

    def test_generate_persona_video_exists_needs_analysis(self):
        self.mock_db_manager.video_exists.return_value = True
        self.mock_db_manager.get_video_title.return_value = "Needs Analysis Video"
        self.mock_db_manager.get_user_demographics.return_value = ("TestName", "F")

        # First call to get_analysis (in _ensure_video_analyzed) returns None
        self.mock_db_manager.get_analysis.return_value = None

        # LLMAnalysis().execute will be called and should return new analysis
        llm_generated_analysis = {
            "wishes": ["new_wish"],
            "pains": ["new_pain"],
            "expressions": ["new_expr"],
            "issues": ["new_issue"],
        }
        self.mock_llm_analysis.execute.return_value = llm_generated_analysis

        persona = self.generator.generate_persona("vid456")

        self.assertEqual(
            persona.title, "Generated Persona for Video: Needs Analysis Video"
        )
        self.assertEqual(persona.name, "TestName")
        self.assertEqual(persona.gender, "Female")  # After _format_gender
        self.assertEqual(persona.wishes, ["new_wish"])
        self.assertEqual(persona.pains, ["new_pain"])
        self.assertEqual(persona.expressions, ["new_expr"])

        self.mock_llm_analysis.execute.assert_called_once_with("vid456", "English")
        # get_analysis is called once in _ensure_video_analyzed
        self.mock_db_manager.get_analysis.assert_called_once_with("vid456")

    @patch("src.services.run_full_pipeline")  # Patch main within services module
    def test_generate_persona_video_does_not_exist(self, mock_run_full_pipeline_function):
        self.mock_db_manager.video_exists.return_value = (
            False  # Video does not exist initially
        )

        # Mock methods that are called after 'main' processing
        self.mock_db_manager.get_video_title.return_value = "New Video Processed"
        self.mock_db_manager.get_user_demographics.return_value = ("NewName", "M")
        # Assume analysis is available after main, or LLM is called if not (tested separately)
        # For this test, let's assume _ensure_video_analyzed finds or creates analysis after main
        self.mock_db_manager.get_analysis.return_value = {
            "wishes": ["main_wish"],
            "pains": ["main_pain"],
            "expressions": ["main_expr"],
            "issues": ["main_issue"],
        }

        persona = self.generator.generate_persona("vid789")

        mock_run_full_pipeline_function.assert_called_once_with("vid789")
        self.assertEqual(
            persona.title, "Generated Persona for Video: New Video Processed"
        )
        self.assertEqual(persona.name, "NewName")
        self.assertEqual(persona.gender, "Male")
        self.assertEqual(persona.wishes, ["main_wish"])

        # Ensure video_exists was checked
        self.mock_db_manager.video_exists.assert_called_once_with("vid789")
        # Ensure get_analysis was called (by _ensure_video_analyzed)
        self.mock_db_manager.get_analysis.assert_called_with("vid789")

    def test_generate_persona_error_handling(self):
        self.mock_db_manager.video_exists.side_effect = Exception("Database error")

        persona = self.generator.generate_persona("vid_error")

        self.assertEqual(persona.title, "Error")
        self.assertIn("Database error", persona.status)
        self.assertEqual(persona.name, "")
        self.assertEqual(persona.gender, "")
        self.assertEqual(persona.wishes, [])

    def test_format_gender(self):
        self.assertEqual(self.generator._format_gender("F"), "Female")
        self.assertEqual(self.generator._format_gender("M"), "Male")
        self.assertEqual(
            self.generator._format_gender(""), "Male"
        )  # Default case if gender code is empty or unexpected
        self.assertEqual(
            self.generator._format_gender("X"), "Male"
        )  # Default case for unexpected


if __name__ == "__main__":
    unittest.main()

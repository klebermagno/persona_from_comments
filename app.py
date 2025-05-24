import os
import gradio as gr
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from main import main
from db_manager import DBManager
from llm_analysis import LLMAnalysis

@dataclass
class PersonaData:
    """Data class to hold persona information"""
    title: str
    name: str
    gender: str
    wishes: List[str]
    pains: List[str]
    expressions: List[str]
    status: str

class PersonaGenerator:
    """Class to handle persona generation logic"""
    def __init__(self):
        self.db = DBManager()

    def _ensure_video_analyzed(self, video_id: str) -> Optional[Dict[str, List[str]]]:
        """Ensure video has LLM analysis, create if missing"""
        try:
            self.db.connect()
            analysis = self.db.get_analysis(video_id)
            
            if not analysis:
                logger.info(f"No existing analysis found for video {video_id}, creating new analysis")
                llm = LLMAnalysis()
                analysis = llm.execute(video_id)
                if not analysis:
                    logger.warning(f"Failed to create analysis for video {video_id}")
            
            self.db.close()
            return analysis
        except Exception as e:
            logger.error(f"Error in _ensure_video_analyzed: {str(e)}")
            self.db.close()
            raise

    def _format_gender(self, gender_code: str) -> str:
        """Convert gender code to display format"""
        return "Female" if gender_code == "F" else "Male"

    def generate_persona(self, video_id: str) -> PersonaData:
        """Generate a persona for a video"""
        if not video_id:
            logger.warning("No video ID provided")
            return PersonaData(
                title="No Video Selected",
                name="",
                gender="",
                wishes=[],
                pains=[],
                expressions=[],
                status="Please enter a video ID"
            )

        try:
            logger.info(f"Generating persona for video {video_id}")
            self.db.connect()
            
            # Process video if not in database
            if not self.db.video_exists(video_id):
                logger.info(f"Video {video_id} not found in database, processing...")
                main(video_id)
                self.db.close()
                self.db.connect()
            
            # Get video information
            title = self.db.get_video_title(video_id)
            name, gender = self.db.get_user_demographics(video_id)
            
            # Get or create analysis
            analysis = self._ensure_video_analyzed(video_id)
            if not analysis:
                logger.warning(f"No analysis available for video {video_id}")
                analysis = {'issues': [], 'wishes': [], 'pains': [], 'expressions': []}
            
            self.db.close()
            
            return PersonaData(
                title=f"Generated Persona for Video: {title}",
                name=name,
                gender=self._format_gender(gender),
                wishes=analysis['wishes'],
                pains=analysis['pains'],
                expressions=analysis['expressions'],
                status=f"Persona generated for video: {video_id}"
            )
            
        except Exception as e:
            error_msg = f"Error processing video {video_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)  # This will log the full stack trace
            self.db.close()
            return PersonaData(
                title="Error",
                name="",
                gender="",
                wishes=[],
                pains=[],
                expressions=[],
                status=error_msg
            )

class PersonaUI:
    """Class to handle UI components and interactions"""
    def __init__(self):
        self.generator = PersonaGenerator()
        self.db = DBManager()

    def _format_for_display(self, persona: PersonaData) -> Tuple:
        """Format persona data for Gradio display"""
        wishes_data = [[w] for w in persona.wishes]
        pains_data = [[p] for p in persona.pains]
        vocab_data = [[v] for v in persona.expressions]
        
        return (
            persona.title,
            persona.name,
            persona.gender,
            wishes_data,
            pains_data,
            vocab_data,
            persona.status
        )

    def process_video(self, video_id: str) -> Tuple:
        """Process video and format for display"""
        persona = self.generator.generate_persona(video_id)
        return self._format_for_display(persona)

    def get_video_list(self) -> List[Tuple[str, str]]:
        """Get list of available videos"""
        self.db.connect()
        videos = self.db.get_all_videos()
        self.db.close()
        return [(f"{title} ({video_id})", video_id) for video_id, title in videos]

    def _update_video_list(self):
        """Update the video list dropdown"""
        choices = self.get_video_list()
        return gr.Dropdown(choices=choices if choices else [("No videos found", "")])

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        with gr.Blocks(theme=gr.themes.Base()) as app:
            gr.Markdown("# YouTube Comment Persona Generator")
            gr.Markdown("Enter a YouTube video ID to generate a persona based on the comments.")
            
            with gr.Row():
                with gr.Column(scale=1):
                    video_id_input = gr.Textbox(
                        label="YouTube Video ID",
                        placeholder="Enter YouTube Video ID",
                        info="Example: dQw4w9WgXcQ"
                    )
                    
                    with gr.Row():
                        submit_btn = gr.Button("Generate Persona", variant="primary", interactive=True)
                        list_btn = gr.Button("List Previous Personas")
                    
                    with gr.Accordion("Previously Generated Personas", open=False) as acc:
                        video_list = gr.Dropdown(
                            label="Select a Video",
                            choices=[],
                            interactive=True,
                            allow_custom_value=False
                        )
                        load_btn = gr.Button("Load Selected Persona")
                    
                    status_output = gr.Textbox(label="Status", interactive=False)
                
                with gr.Column(scale=2):
                    persona_title = gr.Markdown("## Persona Details")
                    
                    with gr.Group() as persona_details:
                        with gr.Row():
                            with gr.Column(min_width=150):
                                gr.Markdown("**Name:**")
                            with gr.Column():
                                persona_name = gr.Textbox(interactive=False, show_label=False)
                        
                        with gr.Row():
                            with gr.Column(min_width=150):
                                gr.Markdown("**Gender:**")
                            with gr.Column():
                                persona_gender = gr.Textbox(interactive=False, show_label=False)
                        
                        # Display sections
                        with gr.Group(visible=True):
                            gr.Markdown("### Wishes")
                            wishes_list = gr.Dataframe(
                                headers=["Wishes"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=200,
                                col_count=(1, "fixed")
                            )
                            
                            gr.Markdown("### Pains")
                            pains_list = gr.Dataframe(
                                headers=["Pains"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=200,
                                col_count=(1, "fixed")
                            )
                            
                            gr.Markdown("### Common Expressions")
                            vocab_list = gr.Dataframe(
                                headers=["Expressions"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=200,
                                col_count=(1, "fixed")
                            )

            # Event handlers with loading states
            submit_btn.click(
                fn=lambda: (gr.Button(interactive=False), "Generating persona..."),
                inputs=None,
                outputs=[submit_btn, status_output],
                queue=False
            ).then(
                fn=self.process_video,
                inputs=video_id_input,
                outputs=[persona_title, persona_name, persona_gender, 
                        wishes_list, pains_list, vocab_list, status_output]
            ).then(
                fn=lambda: gr.Button(interactive=True),
                inputs=None,
                outputs=submit_btn,
                queue=False
            )

            # Loading state for Load Selected Persona button
            load_btn.click(
                fn=lambda: (gr.Button(interactive=False), "Loading selected persona..."),
                inputs=None,
                outputs=[load_btn, status_output],
                queue=False
            ).then(
                fn=self.process_video,
                inputs=video_list,
                outputs=[persona_title, persona_name, persona_gender,
                        wishes_list, pains_list, vocab_list, status_output]
            ).then(
                fn=lambda: gr.Button(interactive=True),
                inputs=None,
                outputs=load_btn,
                queue=False
            )

            # List Previous Personas button handling
            list_btn.click(
                self._update_video_list,
                inputs=None,
                outputs=video_list
            ).then(
                lambda: (gr.Accordion(open=True), "Video list updated"),
                inputs=None,
                outputs=[acc, status_output]
            )

            # Load video list on page load
            app.load(
                self._update_video_list,
                inputs=None,
                outputs=video_list
            )

        return app

def initialize_environment():
    """Initialize the application environment"""
    Path("output").mkdir(exist_ok=True)
    
    if not os.path.exists("youtube.db"):
        db = DBManager()
        db.connect()
        db.create_db()
        db.close()
    
    missing_vars = []
    required_vars = ["YOUTUBE_DEVELOPER_KEY", "NAMSOR_KEY", "OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Warning: The following environment variables are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        print("Please set these variables for full functionality.")

if __name__ == "__main__":
    initialize_environment()
    ui = PersonaUI()
    ui.create_interface().launch(share=False)
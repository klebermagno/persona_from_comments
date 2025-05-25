import os
import gradio as gr
from pathlib import Path
from typing import (
    Tuple,
    List,
)  # dataclass removed from here, Optional, Dict, Any removed
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

from .db_manager import DBManager  # Moved up
from .services import PersonaGenerator, PersonaData  # Moved up

# from main import main # main is used in services.py, not directly here anymore
# from llm_analysis import LLMAnalysis # LLMAnalysis is used in services.py


class PersonaUI:
    """Class to handle UI components and interactions"""

    def __init__(self):
        self.generator = PersonaGenerator()
        self.db = (
            DBManager()
        )  # DBManager instance for PersonaUI specific tasks like get_video_list

    def _format_for_display(self, persona: PersonaData) -> Tuple:
        """Format persona data for Gradio display"""
        issues_data = [[i] for i in persona.issues]
        wishes_data = [[w] for w in persona.wishes]
        pains_data = [[p] for p in persona.pains]
        vocab_data = [[v] for v in persona.expressions]

        return (
            persona.title,
            persona.name,
            persona.gender,
            persona.age,
            persona.language,
            issues_data,
            wishes_data,
            pains_data,
            vocab_data,
            persona.status,
        )

    def process_video(self, video_id: str) -> Tuple:
        """Process video and format for display"""
        persona = self.generator.generate_persona(video_id)
        return self._format_for_display(persona)

    def get_video_list(self) -> List[Tuple[str, str]]:
        """Get list of available videos"""
        # self.db.connect() # REMOVED
        videos = (
            self.db.get_all_videos()
        )  # DBManager methods handle their own connections
        # self.db.close() # REMOVED
        return (
            [(f"{title} ({video_id})", video_id) for video_id, title in videos]
            if videos
            else []
        )

    def _update_video_list(self):
        """Update the video list dropdown"""
        choices = self.get_video_list()
        return gr.Dropdown(choices=choices if choices else [("No videos found", "")])

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        with gr.Blocks(theme=gr.themes.Base()) as app:
            gr.Markdown("# YouTube Comment Persona Generator")
            gr.Markdown(
                "Enter a YouTube video ID to generate a persona based on the comments."
            )

            with gr.Row():
                with gr.Column(scale=1):
                    video_id_input = gr.Textbox(
                        label="YouTube Video ID",
                        placeholder="Enter YouTube Video ID",
                        info="Example: dQw4w9WgXcQ",
                    )

                    with gr.Row():
                        submit_btn = gr.Button(
                            "Generate Persona", variant="primary", interactive=True
                        )
                        list_btn = gr.Button("List Previous Personas")

                    with gr.Accordion(
                        "Previously Generated Personas", open=False
                    ) as acc:
                        video_list = gr.Dropdown(
                            label="Select a Video",
                            choices=[],
                            interactive=True,
                            allow_custom_value=False,
                        )
                        load_btn = gr.Button("Load Selected Persona")

                    status_output = gr.Textbox(label="Status", interactive=False)

                with gr.Column(scale=2):
                    persona_title = gr.Markdown("## Persona Details")

                    # Basic Information Grid using flexible layout
                    with gr.Group():
                        gr.Markdown("### Basic Information")
                        with gr.Row():
                            # Left column for labels
                            with gr.Column(min_width=80, scale=1):
                                gr.Markdown("**Name:**")
                                gr.Markdown("**Gender:**")
                                gr.Markdown("**Age:**")
                                gr.Markdown("**Language:**")
                            # Right column for values with consistent width
                            with gr.Column(min_width=200, scale=1):
                                persona_name = gr.Textbox(
                                    interactive=False, 
                                    show_label=False,
                                    lines=1
                                )
                                persona_gender = gr.Textbox(
                                    interactive=False, 
                                    show_label=False,
                                    lines=1
                                )
                                persona_age = gr.Textbox(
                                    interactive=False, 
                                    show_label=False,
                                    lines=1
                                )
                                persona_language = gr.Textbox(
                                    interactive=False, 
                                    show_label=False,
                                    lines=1
                                )
                        gr.Markdown("---")

                        # Display sections
                        with gr.Group(visible=True):
                            gr.Markdown("### Issues")
                            issues_list = gr.Dataframe(
                                headers=["Issues"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=150,
                                col_count=(1, "fixed"),
                            )

                            gr.Markdown("### Wishes")
                            wishes_list = gr.Dataframe(
                                headers=["Wishes"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=150,
                                col_count=(1, "fixed"),
                            )

                            gr.Markdown("### Pains")
                            pains_list = gr.Dataframe(
                                headers=["Pains"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=150,
                                col_count=(1, "fixed"),
                            )

                            gr.Markdown("---")  # Horizontal divider
                            gr.Markdown("### Common Expressions")
                            vocab_list = gr.Dataframe(
                                headers=["Expressions"],
                                datatype=["str"],
                                interactive=False,
                                type="array",
                                wrap=True,
                                height=150,
                                col_count=(1, "fixed"),
                            )

            # Event handlers with loading states
            submit_btn.click(
                fn=lambda: (gr.Button(interactive=False), "Generating persona..."),
                inputs=None,
                outputs=[submit_btn, status_output],
                queue=False,
            ).then(
                fn=self.process_video,
                inputs=video_id_input,
                outputs=[
                    persona_title,
                    persona_name,
                    persona_gender,
                    persona_age,
                    persona_language,
                    issues_list,
                    wishes_list,
                    pains_list,
                    vocab_list,
                    status_output,
                ],
            ).then(
                fn=lambda: gr.Button(interactive=True),
                inputs=None,
                outputs=submit_btn,
                queue=False,
            )

            # Loading state for Load Selected Persona button
            load_btn.click(
                fn=lambda: (
                    gr.Button(interactive=False),
                    "Loading selected persona...",
                ),
                inputs=None,
                outputs=[load_btn, status_output],
                queue=False,
            ).then(
                fn=self.process_video,
                inputs=video_list,
                outputs=[
                    persona_title,
                    persona_name,
                    persona_gender,
                    persona_age,
                    persona_language,
                    issues_list,
                    wishes_list,
                    pains_list,
                    vocab_list,
                    status_output,
                ],
            ).then(
                fn=lambda: gr.Button(interactive=True),
                inputs=None,
                outputs=load_btn,
                queue=False,
            )

            # List Previous Personas button handling
            list_btn.click(
                self._update_video_list, inputs=None, outputs=video_list
            ).then(
                lambda: (gr.Accordion(open=True), "Video list updated"),
                inputs=None,
                outputs=[acc, status_output],
            )

            # Load video list on page load
            app.load(self._update_video_list, inputs=None, outputs=video_list)

        return app


def initialize_environment():
    """Initialize the application environment"""
    Path("output").mkdir(exist_ok=True)

    if not os.path.exists("youtube.db"):
        db = DBManager()
        # db.connect() # REMOVED
        db.create_db()  # DBManager methods handle their own connections
        # db.close() # REMOVED

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

import os
import gradio as gr
from pathlib import Path

from main import main
from generating import PersonaBuilder
from db_manager import DBManager
from sentiment_analyzer import SentimentAnalyser
from keyword_extractor import KeywordExtractor

def get_most_common_gender_and_name(db, video_id):
    """Get the most common gender and name from comments"""
    genders_count = {'M': 0, 'F': 0}
    names = {'F': {}, 'M': {}}
    
    db.cur.execute("SELECT author_clean_name, author_gender FROM comment WHERE video_id = ? AND author_gender IS NOT NULL", (video_id,))
    results = db.cur.fetchall()
    
    for name, gender in results:
        if gender in genders_count:
            genders_count[gender] += 1
            
        if name and gender in names:
            firstname = name.split()[0] if name and ' ' in name else name
            if firstname:
                if firstname in names[gender]:
                    names[gender][firstname] += 1
                else:
                    names[gender][firstname] = 1
    
    # Determine dominant gender
    dominant_gender = 'M' if genders_count.get('M', 0) > genders_count.get('F', 0) else 'F'
    
    # Find most common name for dominant gender
    most_common_name = ""
    highest_count = 0
    for name, count in names.get(dominant_gender, {}).items():
        if count > highest_count:
            most_common_name = name
            highest_count = count
            
    return most_common_name, dominant_gender

def get_pains_and_wishes(db, video_id):
    """Get the pains and wishes from comments"""
    sentiment_analyzer = SentimentAnalyser()
    possible_pains = []
    possible_wishes = []
    
    # Get pains (most negative comments)
    db.cur.execute("SELECT clean_text FROM comment WHERE video_id = ? AND sentiment IS NOT NULL ORDER BY sentiment ASC LIMIT 10", (video_id,))
    for row in db.cur.fetchall():
        if row[0]:
            sentimental_sentence = sentiment_analyzer.get_most_sentimental_sentence(row[0], True)
            if sentimental_sentence:
                possible_pains.append(sentimental_sentence)
    
    # Get wishes (most positive comments)
    db.cur.execute("SELECT clean_text FROM comment WHERE video_id = ? AND sentiment IS NOT NULL ORDER BY sentiment DESC LIMIT 10", (video_id,))
    for row in db.cur.fetchall():
        if row[0]:
            sentimental_sentence = sentiment_analyzer.get_most_sentimental_sentence(row[0], False)
            if sentimental_sentence:
                possible_wishes.append(sentimental_sentence)
                
    return possible_wishes, possible_pains

def get_vocabulary(db, video_id):
    """Get the most common keywords"""
    vocabulary = []
    db.cur.execute("SELECT text FROM comment_keywords WHERE video_id = ? ORDER BY score ASC LIMIT 20", (video_id,))
    for row in db.cur.fetchall():
        vocabulary.append(row[0])
    return vocabulary

def get_video_title(db, video_id):
    """Get the video title"""
    db.cur.execute("SELECT title FROM video WHERE video_id = ?", (video_id,))
    row = db.cur.fetchone()
    return row[0] if row else "Unknown Title"

def process_video(video_id):
    """Process a YouTube video and generate a persona"""
    if not video_id:
        return "No Video Selected", "", "", [], [], [], "Please enter a video ID"
        
    try:
        # Check if we already have this video in the database
        db = DBManager()
        db.connect()
        db.cur.execute("SELECT video_id FROM video WHERE video_id = ?", (video_id,))
        result = db.cur.fetchone()
        
        # If not already processed, run the main processing pipeline
        if not result:
            main(video_id)
            # Reconnect to get fresh data
            db.close()
            db.connect()
        
        # Get data directly from database
        video_title = get_video_title(db, video_id)
        name, gender = get_most_common_gender_and_name(db, video_id)
        wishes, pains = get_pains_and_wishes(db, video_id)
        vocabulary = get_vocabulary(db, video_id)
        
        db.close()
        
        # Format the data for display
        gender_display = "Female" if gender == "F" else "Male"
        
        # Return the structured data
        return (
            f"Generated Persona for Video: {video_title}",  # Title
            name,                                           # Name
            gender_display,                                 # Gender
            wishes,                                         # Wishes as list
            pains,                                          # Pains as list
            vocabulary,                                     # Vocabulary as list
            f"Persona generated for video: {video_id}"      # Status message
        )
    except Exception as e:
        # Return empty values and error message
        return (
            "Error",                           # Title
            "",                                # Name
            "",                                # Gender
            [],                                # Wishes
            [],                                # Pains
            [],                                # Vocabulary
            f"Error processing video {video_id}: {str(e)}"  # Status message
        )

def list_videos():
    """Get list of all videos in the database"""
    db = DBManager()
    db.connect()
    db.cur.execute("SELECT video_id, title FROM video ORDER BY created DESC")
    videos = db.cur.fetchall()
    db.close()
    return videos

# Add these function definitions before the "Create the Gradio interface" section

def format_data_for_display(title, name, gender, wishes, pains, vocabulary, status):
    # Convert lists to proper dataframe format (list of lists)
    wishes_data = [[w] for w in (wishes if isinstance(wishes, list) else [])]
    pains_data = [[p] for p in (pains if isinstance(pains, list) else [])]
    vocab_data = [[v] for v in (vocabulary if isinstance(vocabulary, list) else [])]
    
    return title, name, gender, wishes_data, pains_data, vocab_data, status

def process_and_format(video_id):
    title, name, gender, wishes, pains, vocabulary, status = process_video(video_id)
    return format_data_for_display(title, name, gender, wishes, pains, vocabulary, status)


# Function to update the dropdown with available videos
def update_video_list():
    videos = list_videos()
    choices = [(f"{title} ({video_id})", video_id) for video_id, title in videos]
    return gr.Dropdown(choices=choices if choices else [("No videos found", "")])

# Create output directory if it doesn't exist
Path("output").mkdir(exist_ok=True)

# Create the Gradio interface
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
                submit_btn = gr.Button("Generate Persona", variant="primary")
                list_btn = gr.Button("List Previous Personas")
            
            # List of previously generated personas
            with gr.Accordion("Previously Generated Personas", open=False) as acc:
                video_list = gr.Dropdown(
                    label="Select a Video",
                    choices=[],
                    interactive=True,
                    allow_custom_value=False
                )
                load_btn = gr.Button("Load Selected Persona")
            
            # Status output
            status_output = gr.Textbox(label="Status", interactive=False)
        
        with gr.Column(scale=2):
            # Persona display components using Gradio's native components
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
                
                # Wishes section
                gr.Markdown("### Wishes")
                wishes_list = gr.Dataframe(
                    headers=["Wishes"],
                    datatype=["str"],
                    interactive=False,
                    type="array"
                )
                
                # Pains section
                gr.Markdown("### Pains")
                pains_list = gr.Dataframe(
                    headers=["Pains"],
                    datatype=["str"],
                    interactive=False,
                    type="array"
                )
                
                # Vocabulary section
                gr.Markdown("### Common Expressions")
                vocab_list = gr.Dataframe(
                    headers=["Expressions"],
                    datatype=["str"],
                    interactive=False,
                    type="array"
                )

    # Move all event handlers inside the Blocks context
    submit_btn.click(
        fn=process_and_format,
        inputs=video_id_input,
        outputs=[persona_title, persona_name, persona_gender, wishes_list, pains_list, vocab_list, status_output]
    )

    # Refresh video list when clicking "List Previous Personas"
    list_btn.click(
        update_video_list,
        inputs=None,
        outputs=video_list
    ).then(
        lambda: (gr.Accordion(open=True), "Video list updated"),
        inputs=None,
        outputs=[acc, status_output]
    )

    # Load selected persona
    load_btn.click(
        fn=process_and_format,
        inputs=video_list,
        outputs=[persona_title, persona_name, persona_gender, wishes_list, pains_list, vocab_list, status_output]
    )

    # Update video list on page load
    app.load(
        update_video_list,
        inputs=None,
        outputs=video_list
    )



# Launch the app
if __name__ == "__main__":
    # Check if database exists, if not create it
    if not os.path.exists("youtube.db"):
        db = DBManager()
        db.connect()
        db.create_db()
        db.close()
        
    # Check for required environment variables
    missing_vars = []
    if not os.getenv("YOUTUBE_DEVELOPER_KEY"):
        missing_vars.append("YOUTUBE_DEVELOPER_KEY")
    if not os.getenv("NAMSOR_KEY"):
        missing_vars.append("NAMSOR_KEY")
    
    if missing_vars:
        print("Warning: The following environment variables are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        print("Please set these variables for full functionality.")
    
    app.launch(share=False)
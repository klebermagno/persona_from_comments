# YouTube Comment Persona Generator

[![Python CI/CD](https://github.com/klebermagno/persona_from_comments/actions/workflows/python-ci.yml/badge.svg)](https://github.com/klebermagno/persona_from_comments/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/klebermagno/persona_from_comments/branch/main/graph/badge.svg)](https://codecov.io/gh/klebermagno/persona_from_comments)

This project uses two external services: YouTube API and Namsor API.
You need to set up the following environment variables:

* `YOUTUBE_DEVELOPER_KEY` - YouTube Data API v3 key
* `NAMSOR_KEY` - Namsor API key for gender analysis
* `OPENAI_API_KEY` - OpenAI API key for LLM analysis

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required libraries:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python db_manager.py
```

4. Download the NLTK corpora:
```bash
python -m textblob.download_corpora
```

## Usage

To generate a persona from YouTube comments, run the following command:
```bash
python main.py <VIDEO_ID>
```
This will create an HTML report at `output/Report-<VIDEO_ID>.html`.

## Web Interface

For easier access, a web interface is available:
```bash
python app.py
```
Open your browser and go to `http://127.0.0.1:7860/`. There, you can:

1. Enter the YouTube video ID
2. Click on "Generate Persona"
3. View the result and access the full report

You can also view all previously generated personas by clicking on "List Previous Personas".

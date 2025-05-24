# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run Commands
- Setup database: `python db_manager.py`
- Download NLTK corpora: `python -m textblob.download_corpora`
- Run application: `python main.py <VIDEO_ID>`

## Environment Variables
- YOUTUBE_DEVELOPER_KEY - Required for YouTube API
- NAMSOR_KEY - Required for gender analysis

## Code Style
- Indentation: 4 spaces
- Naming: snake_case for functions/variables, CamelCase for classes
- Imports: Standard library → Third-party → Project modules
- Type hints: Use when possible, especially for return types
- Error handling: Try to handle errors gracefully
- Documentation: Add docstrings to functions and classes

## Project Structure
- Main workflow: gathering → mining → analysis → generating
- Output: HTML reports in output/ directory

## Dependencies
- Managed via requirements.txt
- Run `pip install -r requirements.txt` to install
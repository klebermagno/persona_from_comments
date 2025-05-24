from db_manager import DBManager
from comment import Comment
from openai import OpenAI
import os
from typing import List, Dict, Optional
import json
from itertools import islice
import time
import tiktoken
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

class LLMAnalysis:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        self.db = DBManager()
        self.db.connect()
        self.model = "gpt-4"  # Using standard GPT-4 model
        self.max_tokens_per_request = 8000  # Conservative limit
        self.max_tokens_response = 2000  # Expected response size
        
        # Initialize OpenAI client without any additional parameters
        self.client = OpenAI()
        
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception as e:
            logger.error(f"Error initializing tiktoken: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self.encoding.encode(text))
        
    def batch_comments(self, comments: List[Dict]) -> List[List[Dict]]:
        """Split comments into batches based on token count."""
        current_batch = []
        current_tokens = 0
        batches = []
        
        base_prompt_tokens = self.count_tokens("""
            Here are YouTube comments about Google AI 2025
            Please extract and summarize:
            1. Common issues.
            2. Common wishes.
            3. Common pains.
            4. Common expressions or catchphrases.
            Provide each category as a bullet list.
            
            Comments:
        """)
        
        max_batch_tokens = self.max_tokens_per_request - base_prompt_tokens - self.max_tokens_response
        
        for comment in comments:
            comment_tokens = self.count_tokens(comment["text"])
            if current_tokens + comment_tokens > max_batch_tokens:
                if current_batch:  # Save current batch if it exists
                    batches.append(current_batch)
                current_batch = [comment]
                current_tokens = comment_tokens
            else:
                current_batch.append(comment)
                current_tokens += comment_tokens
        
        if current_batch:  # Add the last batch if it exists
            batches.append(current_batch)
            
        return batches

    def analyze_batch(self, comments_batch: List[Dict]) -> dict:
        """Analyze a batch of comments using OpenAI API."""
        try:
            comments_text = "\n".join([comment["text"] for comment in comments_batch])
            
            prompt = """
            Here are YouTube comments about Google AI 2025
            Please extract and summarize:
            1. Common issues.
            2. Common wishes.
            3. Common pains.
            4. Common expressions or catchphrases.
            Provide each category as a bullet list.
            
            Comments:
            {comments}
            """.format(comments=comments_text)

            max_retries = 3
            retry_delay = 20  # seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting batch analysis (attempt {attempt + 1}/{max_retries})")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that analyzes YouTube comments."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=self.max_tokens_response
                    )
                    return self._parse_response(response.choices[0].message.content)
                    
                except Exception as e:
                    logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    raise
                    
        except Exception as e:
            logger.error(f"Error in analyze_batch: {str(e)}")
            raise

    def _parse_response(self, response: str) -> dict:
        """Parse the response into structured categories."""
        categories = {
            "issues": [],
            "wishes": [],
            "pains": [],
            "expressions": []
        }
        
        current_category = None
        for line in response.split('\n'):
            line = line.strip()
            if "1. Common issues" in line:
                current_category = "issues"
            elif "2. Common wishes" in line:
                current_category = "wishes"
            elif "3. Common pains" in line:
                current_category = "pains"
            elif "4. Common expressions" in line:
                current_category = "expressions"
            elif line.startswith('- ') or line.startswith('• ') and current_category:
                categories[current_category].append(line[2:])
                
        return categories

    def merge_results(self, results: List[dict]) -> dict:
        """Merge multiple analysis results."""
        merged = {
            "issues": [],
            "wishes": [],
            "pains": [],
            "expressions": []
        }
        
        for result in results:
            for category in merged:
                merged[category].extend(result.get(category, []))
        
        # Remove duplicates while preserving order
        for category in merged:
            merged[category] = list(dict.fromkeys(merged[category]))
            
        return merged

    def execute(self, video_id) -> Optional[Dict[str, List[str]]]:
        '''Perform LLM analysis on comments for a given video ID.'''
        try:
            comments = self.db.get_comments(video_id)
            
            if not comments:
                logger.warning(f"No comments found for video {video_id}")
                return None
                
            # Limit to 400 comments, taking most recent ones
            if len(comments) > 400:
                logger.info(f"Limiting analysis to 400 comments out of {len(comments)} total comments")
                comments = comments[:400]
                
            # Split comments into batches based on token count
            batches = self.batch_comments(comments)
            logger.info(f"Processing {len(comments)} comments in {len(batches)} batches...")
            
            results = []
            for i, batch in enumerate(batches, 1):
                try:
                    logger.info(f"Processing batch {i}/{len(batches)} ({len(batch)} comments)...")
                    batch_result = self.analyze_batch(batch)
                    results.append(batch_result)
                    # Small delay between batches to avoid rate limits
                    if i < len(batches):
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Error analyzing batch {i}: {str(e)}")
                    continue
            
            if not results:
                logger.error(f"No successful analysis results for video {video_id}")
                return None
                
            final_analysis = self.merge_results(results)
            
            # Store the results in the database
            self.db.save_analysis(video_id, final_analysis)
            self.db.con.commit()
            
            self.db.close()
            return final_analysis
            
        except Exception as e:
            logger.error(f"Error in execute: {str(e)}")
            self.db.close()
            raise
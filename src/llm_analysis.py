from .db_manager import DBManager
from .comment import Comment
from openai import OpenAI
from .settings import OPENAI_API_KEY  # Import OPENAI_API_KEY
from typing import List, Dict, Optional
import json
from itertools import islice
import time
import tiktoken
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class LLMAnalysis:
    def __init__(self) -> None:
        # Removed os.getenv and related check for OPENAI_API_KEY

        self.db = DBManager()
        # Removed self.db.connect() as DBManager now uses context managers
        self.model = "gpt-4"  # Using standard GPT-4 model
        self.max_tokens_per_request = 6000  # Reduced to stay under context limit
        self.max_tokens_response = 1000  # Reduced response size

        # Initialize OpenAI client with the imported API key
        self.client = OpenAI(api_key=OPENAI_API_KEY)

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

        # Updated prompt for token counting
        new_prompt_text = """
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
        """  # Note: removed {comments} placeholder for base token count
        base_prompt_tokens = self.count_tokens(new_prompt_text)

        max_batch_tokens = (
            self.max_tokens_per_request - base_prompt_tokens - self.max_tokens_response
        )

        for comment in comments:
            # Calculate tokens for both text and author name
            comment_content = f"{comment['text']} {comment.get('author_clean_name', '')}"
            comment_tokens = self.count_tokens(comment_content)
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

    def analyze_batch(self, comments_batch: List[Dict], language: str = "English") -> dict:
        """Analyze a batch of comments using OpenAI API."""
        try:
            # Format comments with author names
            formatted_comments = [
                f"Author: {comment['author_clean_name']}\nComment: {comment['text']}\n"
                for comment in comments_batch
            ]
            comments_text = "\n".join(formatted_comments)

            # Updated prompt to request JSON
            prompt = """
            
            Analyze the following YouTube comments. Extract and summarize:
            - Common issues
            - Common wishes
            - Common pains
            - Common expressions or catchphrases
            - Name (Summarize all names into one real name. Averaged Real Name, UNknown aren't a real name. The gender need match with the name).
            - Gender (Summarize all genders into one, based on the average comments it should be male or female)
            - Age (Summarize all ages into one, based on the content of the comments text which is related to age, give a range like 18-25 or 30-40)
            - Language (Summarize all languages into one, based on the content of the comments which is related to language)


            Return your response as a single JSON object with these keys:
            - "issues": list of strings - common problems or concerns
            - "wishes": list of strings - desires and aspirations
            - "pains": list of strings - frustrations and difficulties
            - "expressions": list of strings - common phrases or sayings
            - "name": string - Summarize all names into one real name(Averaged Real Name, UNknown aren't a real name).
            - "gender": string - inferred gender ("Male", "Female"). The gender need match with the name
            - "age": string - Summarize all ages into one, based on the content of the comments text which is related to age, give a range like 18-25 or 30-40
            - "language": string - primary language used in the comments
            
            The values should be in the language specified: {language}.

            Analyze these comments and provide insights in JSON format:
            {comments}
            """.format(
                comments=comments_text,
                language=language
            )
            
            #print(f"Prompt for batch analysis:\n{prompt}\n")  # Debugging line

            max_retries = 3
            retry_delay = 20  # seconds

            last_exception = None
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"Attempting batch analysis (attempt {attempt + 1}/{max_retries})"
                    )
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that analyzes YouTube comments and returns JSON.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=self.max_tokens_response,
                    )
                    return self._parse_response(response.choices[0].message.content)

                except Exception as e:
                    last_exception = e
                    logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = retry_delay * (2**attempt)  # Exponential backoff
                        logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

            if last_exception:
                raise last_exception  # Re-raise the last exception if all retries failed
            
            raise Exception("All retry attempts failed without an exception")

        except Exception as e:
            logger.error(f"Error in analyze_batch: {str(e)}")
            raise

    def _parse_response(self, response: str) -> dict:
        """Parse the JSON response into structured categories."""
        categories = {
            "issues": [], 
            "wishes": [], 
            "pains": [], 
            "expressions": [],
            "name": "",
            "gender": "",
            "age": "",
            "language": ""
        }
        
        # First, try to find JSON within the response if it's not pure JSON
        try:
            # Look for JSON-like structure between curly braces
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
            else:
                json_str = response

            parsed_json = json.loads(json_str)
            
            # Handle list categories
            for category_key in ["issues", "wishes", "pains", "expressions"]:
                if category_key in parsed_json and isinstance(
                    parsed_json[category_key], list
                ):
                    categories[category_key] = [
                        str(item).strip() for item in parsed_json[category_key]
                        if str(item).strip()  # Filter out empty strings
                    ]
            
            # Handle scalar demographic fields
            for field in ["name", "gender", "age", "language"]:
                if field in parsed_json:
                    categories[field] = str(parsed_json[field]).strip()
            
            return categories
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM response as JSON: {e}")
            logger.error(
                f"LLM Response was: {response}"
            )  # Log the problematic response
            return categories  # Return default structure on JSON decode error
        except Exception as e:  # Catch other potential errors during parsing
            logger.error(f"Error parsing LLM response content: {e}")
            logger.error(f"LLM Response was: {response}")
            return categories  # Return default structure on other errors

    def merge_results(self, results: List[dict]) -> dict:
        """Merge multiple analysis results."""
        merged = {
            "issues": [], 
            "wishes": [], 
            "pains": [], 
            "expressions": [],
            "name": "",
            "gender": "",
            "age": "",
            "language": ""
        }

        # Merge list fields
        for category in ["issues", "wishes", "pains", "expressions"]:
            all_items = []
            for result in results:
                all_items.extend(result.get(category, []))
            # Remove duplicates while preserving order
            merged[category] = list(dict.fromkeys(all_items))
        
        # For demographic fields, take the most common non-empty value
        for field in ["name", "gender", "age", "language"]:
            field_values = {}
            for result in results:
                value = result.get(field, "").strip()
                if value:
                    field_values[value] = field_values.get(value, 0) + 1
            
            # Get the most common value, or empty string if no values
            if field_values:
                merged[field] = max(field_values.items(), key=lambda x: x[1])[0]

        return merged

    def execute(self, video_id, language= "English") -> Optional[Dict[str, List[str]]]:
        """Perform LLM analysis on comments for a given video ID."""
        try:
            comments = self.db.get_comments(video_id)

            if not comments:
                logger.warning(f"No comments found for video {video_id}")
                return None

            # Limit to 400 comments, taking most recent ones
            if len(comments) > 400:
                logger.info(
                    f"Limiting analysis to 400 comments out of {len(comments)} total comments"
                )
                comments = comments[:400]

            # Split comments into batches based on token count
            batches = self.batch_comments(comments)
            logger.info(
                f"Processing {len(comments)} comments in {len(batches)} batches..."
            )

            results = []
            for i, batch in enumerate(batches, 1):
                try:
                    logger.info(
                        f"Processing batch {i}/{len(batches)} ({len(batch)} comments) in {language}..."
                    )
                    batch_result = self.analyze_batch(batch, language)
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
            # Removed self.db.con.commit() as it's handled by DBManager's context manager

            # Removed self.db.close() as it's handled by DBManager's context manager
            return final_analysis

        except Exception as e:
            logger.error(f"Error in execute: {str(e)}")
            # Removed self.db.close() as it's handled by DBManager's context manager
            raise

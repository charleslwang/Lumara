# utils.py

import os
import re
import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, RetryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_absolute_path(file_path: str) -> Path:
    """
    Convert relative paths to absolute paths.
    For prompt files, looks in the parent directory's prompts folder.
    """
    if os.path.isabs(file_path):
        return Path(file_path)
        
    # For prompt files, look in the parent directory's prompts folder
    if file_path.startswith('prompts/'):
        return Path(__file__).parent.parent / file_path
        
    return Path(__file__).parent / file_path

def load_prompt(file_path: str) -> str:
    """
    Reads and returns the content of a text file.
    
    Args:
        file_path: Path to the prompt file, can be relative or absolute
        
    Returns:
        str: The content of the file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        RuntimeError: If there's an error reading the file
    """
    try:
        abs_path = get_absolute_path(file_path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Prompt file is empty: {abs_path}")
            return content
    except FileNotFoundError as e:
        logger.error(f"Prompt file not found: {abs_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading prompt file {abs_path}: {str(e)}")
        raise RuntimeError(f"Failed to load prompt from {abs_path}") from e


def generate_session_id() -> str:
    """Generate a unique session identifier based on the current timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"recursive_session_{timestamp}"

def call_gemini_with_retry(
    model: genai.GenerativeModel,
    prompt: str,
    call_type: str = "generation",
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0
) -> str:
    """
    Robust wrapper for Gemini API calls with exponential backoff and retry logic.
    
    Args:
        model: Initialized Gemini model instance
        prompt: The prompt to send to the model
        call_type: Type of call for logging purposes (e.g., 'generation', 'critique')
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        str: The generated text response
        
    Raises:
        RuntimeError: If all retry attempts fail
        ValueError: If the response is invalid
    """
    delay = initial_delay
    last_exception = None
    
    logger.info(f"Initiating {call_type} API call with {max_retries} max retries")
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_retries} for {call_type}")
            
            # Generate content with the current version of the API
            response = model.generate_content(prompt)
            
            # Check if we got a valid response
            if not response or not hasattr(response, 'text'):
                raise ValueError("Invalid response format from API")
                
            response_text = response.text.strip()
            
            if not response_text:
                raise ValueError("Empty response from API")
                
            logger.info(f"Successfully completed {call_type} API call")
            logger.debug(f"Response (first 200 chars): {response_text[:200]}...")
            
            return response_text
            
        except (GoogleAPICallError, RetryError, Exception) as e:
            last_exception = e
            error_type = type(e).__name__
            
            if attempt == max_retries:
                logger.error(f"Final attempt ({attempt}/{max_retries}) failed for {call_type}: {str(e)}", 
                           exc_info=True)
                break
                
            logger.warning(
                f"Attempt {attempt}/{max_retries} for {call_type} failed with {error_type}: {str(e)}. "
                f"Retrying in {delay:.1f} seconds..."
            )
            
            # Exponential backoff with jitter
            time.sleep(delay + random.uniform(0, 0.1 * delay))
            delay = min(delay * 2, max_delay)
    
    # If we get here, all retries failed
    error_msg = f"Failed to complete {call_type} after {max_retries} attempts"
    logger.error(error_msg, exc_info=True)
    raise RuntimeError(f"{error_msg}: {str(last_exception)}")

def extract_improvements(critique_text: str) -> List[str]:
    """
    Parses a critique text to extract actionable improvement suggestions.
    It looks for 'TOP IMPROVEMENT PRIORITIES' and 'REFINED APPROACH SUGGESTION'.
    
    Args:
        critique_text: The text of the critique to parse
        
    Returns:
        List[str]: List of improvement suggestions
    """
    if not isinstance(critique_text, str) or not critique_text.strip():
        logger.warning("Empty or invalid critique text provided")
        return []
        
    improvements = []
    
    try:
        # Normalize line endings and multiple spaces
        text = '\n'.join(line.strip() for line in critique_text.splitlines() if line.strip())
        
        # Extract TOP IMPROVEMENT PRIORITIES section (more flexible pattern)
        priority_pattern = r'(?:##?\s*)?(?:TOP\s+)?(?:IMPROVEMENTS?|PRIORITIES?)[:.]?\s*\n(.*?)(?=\n\s*##?\s*\S|\.?\s*$)'
        priority_match = re.search(priority_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if priority_match:
            priority_text = priority_match.group(1)
            # Extract numbered or bulleted items
            priority_items = re.findall(
                r'(?:^|\n)[-*]\s*(.*?)(?=\n[-*\d]|$)',
                priority_text,
                re.DOTALL
            )
            
            # Fallback to numbered items if no bullet points found
            if not priority_items:
                priority_items = re.findall(
                    r'(?:^|\n)\d+[.)]?\s*(.*?)(?=\n\d+[.)]|$)',
                    priority_text,
                    re.DOTALL
                )
                
            improvements.extend([item.strip() for item in priority_items if item.strip()])
        
        # Extract REFINED APPROACH SUGGESTION (more flexible pattern)
        approach_pattern = r'(?:##?\s*)?(?:REFINED\s+)?(?:APPROACH|SUGGESTION|RECOMMENDATION)[:.]?\s*\n(.*?)(?=\n\s*##?\s*\S|\.?\s*$)'
        approach_match = re.search(approach_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if approach_match:
            approach_text = approach_match.group(1).strip()
            if approach_text:
                improvements.append(f"APPROACH: {approach_text}")
                
    except Exception as e:
        logger.error(f"Error parsing critique text: {str(e)}")
        # Return empty list or partial results depending on error severity
        if not improvements:  # Only return empty if we have no results
            return []
            
    return improvements

def format_improvements(improvements: List[str]) -> str:
    """
    Formats a list of improvement suggestions for inclusion in the next iteration's prompt.
    
    Args:
        improvements: List of improvement strings
        
    Returns:
        str: Formatted improvements string
    """
    if not improvements:
        return "No specific improvements were identified from the previous critique."
    
    try:
        # Filter out any non-string items and strip whitespace
        valid_improvements = [str(imp).strip() for imp in improvements if imp and str(imp).strip()]
        
        if not valid_improvements:
            return "No valid improvements were identified from the previous critique."
            
        # Format with consistent numbering and ensure each item is on a new line
        return "\n".join(f"{i}. {imp}" for i, imp in enumerate(valid_improvements, 1))
        
    except Exception as e:
        logger.error(f"Error formatting improvements: {str(e)}")
        return "Error processing improvement suggestions. Please review the previous critique manually."

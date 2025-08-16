"""
Core pipeline implementation for Lumara.

This module provides a wrapper around the external Refinery pipeline,
handling initialization, configuration, and execution of the refinement process.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import Refinery components through our core package
from . import (
    RefineryPipeline,
    SolutionJudge,
    MODEL_NAME,
    GENERATION_CONFIG,
    ADVANCED_CONFIG,
    load_prompt,
    extract_improvements,
    format_improvements,
    call_gemini_with_retry
)

# Set up logging
logger = logging.getLogger(__name__)

class LumaraPipeline:
    """Main pipeline class that wraps the Refinery pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Lumara pipeline.
        
        Args:
            config: Optional configuration overrides
        """
        from .config import get_config
        self.config = get_config(**(config or {}))
        self._setup_pipeline()
    
    def _setup_pipeline(self) -> None:
        """Set up the Refinery pipeline configuration (without API key)."""
        try:
            # Don't initialize pipeline here - we'll create it per request with user's API key
            self.pipeline = None
            logger.info("Pipeline configuration ready - will initialize per request with user API key")
            
            # Load prompts if custom prompt directory is provided
            prompt_dir = self.config.get('prompt_dir')
            if prompt_dir and Path(prompt_dir).exists():
                self._load_prompts(prompt_dir)
                
        except Exception as e:
            logger.error(f"Failed to setup pipeline configuration: {str(e)}")
            raise
    
    def _load_prompts(self, prompt_dir: str) -> None:
        """Load prompt templates from the specified directory.
        
        Args:
            prompt_dir: Directory containing prompt template files
        """
        prompt_path = Path(prompt_dir)
        if not prompt_path.exists():
            logger.warning(f"Prompt directory not found: {prompt_dir}")
            return
        
        # Map of prompt file names to their corresponding attributes
        prompt_files = {
            'solution_template.txt': 'solution_template',
            'first_iteration_context.txt': 'first_iteration_context',
            'subsequent_iteration_context.txt': 'subsequent_iteration_context',
            'critique_template.txt': 'critique_template'
        }
        
        # Load each prompt file
        for filename, attr_name in prompt_files.items():
            file_path = prompt_path / filename
            if file_path.exists():
                try:
                    prompt_content = load_prompt(str(file_path))
                    setattr(self.pipeline, f'_{attr_name}', prompt_content)
                    logger.info(f"Loaded prompt: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load prompt {filename}: {str(e)}")
            else:
                logger.warning(f"Prompt file not found: {file_path}")
    
    def refine(
        self,
        prompt: str,
        model_output: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Refine a model output using the Refinery pipeline.
        
        Args:
            prompt: The original user prompt
            model_output: The initial model output to refine
            context: Additional context for refinement
            **kwargs: Additional arguments for the refinement process
            
        Returns:
            Dictionary containing the refined output and metadata
        """
        try:
            # Get API key from config (user-provided) instead of environment
            api_key = self.config.get('api_key')
            if not api_key:
                raise ValueError(
                    "API key not found in configuration. "
                    "Users must provide their own Google Gemini API key."
                )
            
            # Initialize the Refinery pipeline with user's API key
            self.pipeline = RefineryPipeline(api_key=api_key)
            logger.info("Successfully initialized Refinery pipeline with user-provided API key")
            
            # Run the Refinery pipeline with initial solution
            result = self.pipeline.run(
                original_prompt=prompt,
                initial_solution=model_output,
                max_iterations=self.config.max_iterations
            )
            
            # Format the result
            iterations_list = result.get('iterations', [])
            return {
                'refined_output': result.get('best_solution', model_output),
                'iterations': len(iterations_list),
                'iterations_data': iterations_list,  # Include raw iterations for frontend
                'scores': {
                    'overall': result.get('best_score', 0),
                    'details': iterations_list[-1].get('evaluation', {}) if iterations_list else {}
                },
                'metadata': {
                    'session_id': result.get('session_id'),
                    'duration_seconds': result.get('duration_seconds', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in refinement pipeline: {str(e)}", exc_info=True)
            # Return the original output if refinement fails
            return {
                'refined_output': model_output,
                'error': str(e),
                'iterations': 0,
                'scores': {},
                'metadata': {}
            }


def create_pipeline(config: Optional[Dict[str, Any]] = None) -> 'LumaraPipeline':
    """Create a new instance of the Lumara pipeline.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured LumaraPipeline instance
    """
    return LumaraPipeline(config=config)

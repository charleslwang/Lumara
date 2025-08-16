import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, RetryError

from config import MODEL_NAME, GENERATION_CONFIG, ADVANCED_CONFIG
from utils import (
    generate_session_id,
    call_gemini_with_retry,
    extract_improvements,
    format_improvements,
    load_prompt,
    get_absolute_path
)
from judge import SolutionJudge

# Configure logging
logger = logging.getLogger(__name__)

class RecursiveImprovementPipeline:
    """
    Manages the core recursive improvement pipeline, orchestrating the generation
    of solutions and critiques.
    """
    def __init__(self, api_key: str):
        """
        Initialize the pipeline with API key and configuration.
        
        Args:
            api_key: Google API key for Gemini
            
        Raises:
            RuntimeError: If initialization fails
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(MODEL_NAME)
            self.generation_config = genai.types.GenerationConfig(**GENERATION_CONFIG)
            self.judge = SolutionJudge(api_key)
            self._load_prompts()
            logger.info("Pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            raise RuntimeError(f"Pipeline initialization failed: {str(e)}") from e

    def _load_prompts(self):
        """
        Load prompt templates from the filesystem.
        
        Raises:
            RuntimeError: If any required prompt file is missing or invalid
        """
        try:
            # Load prompts using relative paths from project root
            self.solution_template = load_prompt("prompts/solution_template.txt")
            self.first_iteration_context = load_prompt("prompts/first_iteration_context.txt")
            self.subsequent_iteration_context = load_prompt("prompts/subsequent_iteration_context.txt")
            self.critique_template = load_prompt("prompts/critique_template.txt")
            
            # Validate that all prompts are non-empty
            prompts = {
                'solution_template': self.solution_template,
                'first_iteration_context': self.first_iteration_context,
                'subsequent_iteration_context': self.subsequent_iteration_context,
                'critique_template': self.critique_template
            }
            
            for name, prompt in prompts.items():
                if not prompt or not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError(f"Prompt '{name}' is empty or invalid")
                    
        except Exception as e:
            logger.error(f"Failed to load prompts: {str(e)}")
            raise RuntimeError(f"Failed to load prompt templates: {str(e)}") from e

    def run(self, original_prompt: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run the recursive improvement pipeline.
        
        Args:
            original_prompt: The original user prompt
            max_iterations: Maximum number of iterations to run
            
        Returns:
            Dict containing the best solution and iteration history
        """
        logger.info(f"Starting pipeline with {max_iterations} iterations")
        print(f"Starting recursive improvement pipeline with {max_iterations} iterations.")
        print(f"Prompt: {original_prompt[:100]}...")
        print("Detailed logs are being written to the logs directory.\n")
        
        session_id = f"recursive_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting pipeline with session ID: {session_id}")
        
        session_data = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'original_prompt': original_prompt,
            'iterations': [],
            'best_solution': None,
            'best_score': -1
        }
        
        previous_solution = None
        previous_critique = None
        
        for i in range(1, max_iterations + 1):
            iteration_start = time.time()
            logger.info(f"Starting iteration {i}/{max_iterations}")
            print(f"\nIteration {i}/{max_iterations}...")
            
            try:
                # Generate solution
                logger.debug("Generating solution...")
                solution = self._generate_solution(
                    original_prompt=original_prompt,
                    previous_solution=previous_solution,
                    previous_critique=previous_critique,
                    iteration=i,
                    total_iterations=max_iterations
                )
                
                # Evaluate solution
                logger.debug("Evaluating solution...")
                evaluation = self.judge.evaluate_solution(
                    prompt=original_prompt,
                    solution=solution,
                    iteration=i
                )
                
                # Generate critique (except for final iteration)
                if i < max_iterations:
                    logger.debug("Generating critique...")
                    print("   Generating critique...")
                    critique = self._generate_critique(
                        original_prompt=original_prompt,
                        current_solution=solution,
                        previous_critique=previous_critique,
                        iteration=i,
                        total_iterations=max_iterations
                    )
                else:
                    critique = None
                
                # Store iteration data
                iteration_data = {
                    'iteration': i,
                    'solution': solution,
                    'evaluation': evaluation,
                    'critique': critique,
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': time.time() - iteration_start
                }
                
                session_data['iterations'].append(iteration_data)
                
                # Update best solution if current is better
                current_score = evaluation.get('overall_score', 0)
                if current_score > session_data['best_score']:
                    session_data['best_solution'] = solution
                    session_data['best_score'] = current_score
                
                previous_solution = solution
                if critique:
                    previous_critique = critique
                
                logger.info(f"Completed iteration {i} in {iteration_data['duration_seconds']:.2f}s. Score: {current_score}")
                
            except Exception as e:
                logger.error(f"Error in iteration {i}: {str(e)}", exc_info=True)
                print(f"Error in iteration {i}: {str(e)}")
                continue
        
        # Finalize session data
        session_data['end_time'] = datetime.now().isoformat()
        session_data['duration_seconds'] = (
            datetime.fromisoformat(session_data['end_time']) - 
            datetime.fromisoformat(session_data['start_time'])
        ).total_seconds()
        
        # Print summary
        self._print_summary(session_data)
        
        # Return results without saving to file - main.py will handle saving
        logger.info("Pipeline execution completed successfully")
        return session_data
    
    def _print_summary(self, session_data: Dict[str, Any]) -> None:
        """Print a summary of the pipeline execution."""
        print("\n" + "="*80)
        print(f"{'AI REFINERY - PIPELINE SUMMARY':^80}")
        print("="*80)
        
        print(f"\n{'Session ID:':<20} {session_data.get('session_id', 'N/A')}")
        print(f"{'Timestamp:':<20} {session_data.get('start_time', 'N/A')}")
        print(f"{'Prompt:':<20} {session_data.get('original_prompt', 'N/A')}")
        print(f"{'Iterations:':<20} {len(session_data.get('iterations', []))}/{session_data.get('total_iterations', 0)}\n")
        
        print("-"*40)
        print(f"{'ITERATION SUMMARIES':^40}")
        print("-"*40)
        
        for i, iteration in enumerate(session_data.get('iterations', []), 1):
            print(f"\nIteration {i}:")
            print(f"  - Score: {iteration.get('evaluation', {}).get('overall_score', 'N/A')}")
            print(f"  - Duration: {iteration.get('duration_seconds', 0):.2f}s")
        
        print("\n" + "="*80)
        print(f"{'PIPELINE COMPLETED SUCCESSFULLY':^80}")
        print("="*80 + "\n")

    def _generate_solution(
        self,
        original_prompt: str,
        previous_solution: Optional[str],
        previous_critique: Optional[str],
        iteration: int,
        total_iterations: int
    ) -> str:
        """
        Generate a solution for the given prompt and iteration.
        
        Args:
            original_prompt: The original user prompt
            previous_solution: The solution from the previous iteration, if any
            previous_critique: The critique from the previous iteration, if any
            iteration: Current iteration number (1-based)
            total_iterations: Total number of iterations
            
        Returns:
            str: The generated solution
            
        Raises:
            RuntimeError: If solution generation fails
        """
        logger.info(f"Generating solution for iteration {iteration}/{total_iterations}")
        
        try:
            # Build the prompt for solution generation
            prompt = self._build_solution_prompt(
                original_prompt=original_prompt,
                iteration=iteration - 1,  # Convert to 0-based for the method
                previous_solutions=[previous_solution] if previous_solution else [],
                previous_critiques=[previous_critique] if previous_critique else []
            )
            
            logger.debug(f"Solution prompt for iteration {iteration}:\n{prompt[:500]}...")
            
            # Call the Gemini API with retry logic
            logger.info(f"Calling Gemini API for solution generation (iteration {iteration})")
            solution = call_gemini_with_retry(
                model=self.model,
                prompt=prompt,
                call_type=f'solution_gen_iter_{iteration}',
                max_retries=3,
                initial_delay=1,
                max_delay=10
            )
            
            if not solution or not solution.strip():
                raise ValueError("Received empty solution from the model")
                
            logger.info(f"Successfully generated solution for iteration {iteration}")
            logger.debug(f"Solution (first 200 chars): {solution[:200]}...")
            
            return solution.strip()
            
        except Exception as e:
            error_msg = f"Failed to generate solution for iteration {iteration}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def _build_solution_prompt(self, original_prompt: str, iteration: int, previous_solutions: List[str], previous_critiques: List[str]) -> str:
        """
        Build the prompt for generating a solution.
        
        Args:
            original_prompt: The original user prompt
            iteration: Current iteration number (0-based)
            previous_solutions: List of previous solutions
            previous_critiques: List of previous critiques
            
        Returns:
            str: Formatted prompt for solution generation
        """
        # For first iteration, use first_iteration_context, otherwise use subsequent
        if iteration == 0:
            context = self.first_iteration_context
            template_vars = {
                'original_prompt': original_prompt,
                'context': context,
                'iteration_context': f"This is iteration 1 of your refinement process.",
                'iteration': 1,
                'total_iterations': len(previous_solutions) + 1,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            # For subsequent iterations, we need to format the context template first
            previous_solution = previous_solutions[-1] if previous_solutions else ""
            previous_critique = previous_critiques[-1] if previous_critiques else ""
            
            # Extract improvement suggestions from the critique
            improvements = extract_improvements(previous_critique)
            improvement_suggestions = "\n".join(f"- {imp}" for imp in improvements) if improvements else "No specific improvements identified."
            
            # Format the subsequent iteration context
            context_vars = {
                'previous_solution': previous_solution,
                'previous_critique': previous_critique,
                'improvement_suggestions': improvement_suggestions,
                'iteration_number': iteration + 1
            }
            
            try:
                context = self.subsequent_iteration_context.format(**context_vars)
            except KeyError as ke:
                logger.warning(f"Missing template variable in subsequent_iteration_context: {ke}")
                # Set missing variable to empty string and try again
                context_vars[str(ke).strip("'")] = ""
                context = self.subsequent_iteration_context.format(**context_vars)
            
            # Now prepare the full solution template variables
            template_vars = {
                'original_prompt': original_prompt,
                'context': context,
                'iteration_context': f"This is iteration {iteration + 1} of your refinement process.",
                'iteration': iteration + 1,
                'total_iterations': len(previous_solutions) + 1,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        try:
            return self.solution_template.format(**template_vars)
        except KeyError as ke:
            logger.warning(f"Missing template variable in solution template: {ke}")
            # Set missing variable to empty string and try again
            template_vars[str(ke).strip("'")] = ""
            return self.solution_template.format(**template_vars)

    def _build_critique_prompt(self, original_prompt: str, current_solution: str, iteration_count: int, total_iterations: int) -> str:
        """
        Builds a detailed critique prompt for analyzing the current solution.
        
        Args:
            original_prompt: The original user prompt
            current_solution: The current solution to critique
            iteration_count: Current iteration number (1-based)
            total_iterations: Total number of iterations
            
        Returns:
            str: Formatted critique prompt
        """
        try:
            logger.info("\n" + "#" * 80)
            logger.info(f"GENERATING CRITIQUE - ITERATION {iteration_count}/{total_iterations}")
            logger.info("#" * 80 + "\n")
            
            # Add iteration context
            iteration_context = f"""
            This is iteration {iteration_count} of {total_iterations}.
            Please provide a detailed critique of the following solution.
            """.strip()
            
            # Prepare all template variables
            template_vars = {
                'original_prompt': original_prompt,
                'current_solution': current_solution,
                'iteration_context': iteration_context,
                'iteration': iteration_count,  # For backward compatibility
                'iteration_count': iteration_count,
                'total_iterations': total_iterations,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add any missing variables as empty strings to prevent KeyError
            try:
                return self.critique_template.format(**template_vars)
            except KeyError as ke:
                missing_key = str(ke).strip("'")
                logger.warning(f"Missing template variable in critique template: {missing_key}")
                template_vars[missing_key] = ""
                return self.critique_template.format(**template_vars)
                
        except Exception as e:
            error_msg = f"\n!!! ERROR BUILDING CRITIQUE PROMPT (ITERATION {iteration_count}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.error("\n" + "!" * 80 + "\n")
            raise RuntimeError(error_msg) from e
    
    def _adjust_prompts_by_iteration(self, iteration: int, total: int):
        """
        Dynamically adjust prompt focus based on iteration progress.
        
        Args:
            iteration: Current iteration number (1-based)
            total: Total number of iterations
            
        Returns:
            Dict: Adjusted configuration parameters
        """
        try:
            progress = iteration / total
            adjusted_config = {}
            
            # Example: Gradually increase temperature for more creativity
            if 'solution_temperature' in self.config:
                base_temp = self.config['solution_temperature']
                # Ramp up temperature in the first half, then stabilize
                if progress < 0.5:
                    adjusted_temp = base_temp + (0.4 * (progress * 2))
                else:
                    adjusted_temp = base_temp + 0.4
                
                adjusted_temp = min(0.9, max(0.1, adjusted_temp))  # Keep within bounds
                self.generation_config.temperature = adjusted_temp
                adjusted_config['temperature'] = adjusted_temp
            
            # Adjust other parameters based on progress
            # ... (add more dynamic adjustments as needed)
            
            logger.debug(
                "Adjusted parameters for iteration %d/%d: %s",
                iteration, total, adjusted_config
            )
            
            return adjusted_config
            
        except Exception as e:
            logger.warning("Error adjusting prompts: %s", str(e))
            return {}
    # You would override run() or other methods to use this advanced logic.

    def _generate_critique(
        self,
        original_prompt: str,
        current_solution: str,
        previous_critique: Optional[str],
        iteration: int,
        total_iterations: int
    ) -> str:
        """
        Generate a critique for the given solution and iteration.
        
        Args:
            original_prompt: The original user prompt
            current_solution: The current solution to critique
            previous_critique: The critique from the previous iteration, if any
            iteration: Current iteration number (1-based)
            total_iterations: Total number of iterations
            
        Returns:
            str: The generated critique
            
        Raises:
            RuntimeError: If critique generation fails
        """
        logger.info(f"Generating critique for iteration {iteration}/{total_iterations}")
        
        try:
            # Build the prompt for critique generation
            prompt = self._build_critique_prompt(
                original_prompt=original_prompt,
                current_solution=current_solution,
                iteration_count=iteration,
                total_iterations=total_iterations
            )
            
            logger.debug(f" Critique prompt for iteration {iteration}:\n{prompt[:500]}...")
            
            # Call the Gemini API with retry logic
            logger.info(f"Calling Gemini API for critique generation (iteration {iteration})")
            critique = call_gemini_with_retry(
                model=self.model,
                prompt=prompt,
                call_type=f'critique_iter_{iteration}',
                max_retries=3,
                initial_delay=1,
                max_delay=10
            )
            
            if not critique or not critique.strip():
                raise ValueError("Received empty critique from the model")
                
            logger.info(f"Successfully generated critique for iteration {iteration}")
            logger.debug(f" Critique (first 200 chars): {critique[:200]}...")
            
            return critique.strip()
            
        except Exception as e:
            error_msg = f"Failed to generate critique for iteration {iteration}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

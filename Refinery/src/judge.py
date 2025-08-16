"""
Judge component for evaluating solution quality in the AI Refinery pipeline.
"""

import json
from typing import Dict, Any, List
import logging
import google.generativeai as genai
from config import MODEL_NAME, GENERATION_CONFIG
from utils import call_gemini_with_retry

logger = logging.getLogger(__name__)

class SolutionJudge:
    """
    Evaluates the quality of solutions based on predefined criteria.
    """
    
    def __init__(self, api_key: str):
        """Initialize the judge with the Gemini model."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.generation_config = genai.types.GenerationConfig(**GENERATION_CONFIG)
        
        # Define evaluation criteria
        self.criteria = [
            "Novelty and creativity",
            "Clarity and specificity",
            "Feasibility and practicality",
            "Engagement and fun factor",
            "Balance and fairness"
        ]
    
    def evaluate_solution(self, prompt: str, solution: str, iteration: int) -> Dict[str, Any]:
        """
        Evaluate a solution based on the original prompt and criteria.
        
        Args:
            prompt: The original user prompt
            solution: The solution to evaluate
            iteration: Current iteration number
            
        Returns:
            Dict containing evaluation scores and feedback
        """
        try:
            evaluation_prompt = """You are an expert judge evaluating a solution. 
            Your response MUST be a valid JSON object with the following structure:
            {
                "scores": {
                    "Novelty and creativity": 0,
                    "Clarity and specificity": 0,
                    "Feasibility and practicality": 0,
                    "Engagement and fun factor": 0,
                    "Balance and fairness": 0
                },
                "overall_score": 0,
                "feedback": "Your detailed feedback here"
            }
            
            Evaluation Criteria (rate each 1-10):
            1. Novelty and creativity: How original and innovative is the solution?
            2. Clarity and specificity: How clear and well-defined is the solution?
            3. Feasibility and practicality: How practical and implementable is the solution?
            4. Engagement and fun factor: How engaging and interesting is the solution?
            5. Balance and fairness: How well-balanced and fair is the solution?
            
            PROMPT TO EVALUATE:
            """ + prompt + """
            
            SOLUTION TO EVALUATE:
            """ + solution[:2000] + """
            
            Please provide your evaluation in valid JSON format as specified above.
            """

            # Call the Gemini API with retry and timeout
            response = call_gemini_with_retry(
                model=self.model,
                prompt=evaluation_prompt,
                call_type=f'solution_eval_iter_{iteration}',
                max_retries=3,
                initial_delay=1,
                max_delay=10
            )
            
            # Clean the response to extract JSON
            try:
                # First, try to parse the entire response as JSON
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
                
                # If that fails, try to extract JSON from the response
                lines = response.split('\n')
                json_blocks = []
                in_json = False
                json_block = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('{') or in_json:
                        in_json = True
                        json_block.append(line)
                        if line.endswith('}'):
                            in_json = False
                            json_blocks.append('\n'.join(json_block))
                            json_block = []
                
                # Try to parse each potential JSON block
                for block in json_blocks:
                    try:
                        evaluation = json.loads(block)
                        # Validate the structure before returning
                        if all(key in evaluation for key in ["scores", "overall_score", "feedback"]):
                            return evaluation
                    except json.JSONDecodeError:
                        continue
                
                # If we get here, no valid JSON was found
                raise ValueError("No valid JSON found in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse evaluation response: {str(e)}")
                # Return a default evaluation on parse failure
                return {
                    "scores": {criterion: 5 for criterion in self.criteria},
                    "overall_score": 5,
                    "feedback": f"Evaluation failed - could not parse response: {str(e)}",
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error in evaluate_solution: {str(e)}", exc_info=True)
            # Return a default evaluation on error
            return {
                "scores": {criterion: 5 for criterion in self.criteria},
                "overall_score": 5,
                "feedback": f"Evaluation failed due to an error: {str(e)}",
                "error": str(e)
            }
    
    def _format_criteria(self) -> str:
        """Format the evaluation criteria as a string."""
        return "\n".join([f"- {criterion}" for criterion in self.criteria])
    
    def compare_solutions(self, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple solutions and return the best one.
        
        Args:
            solutions: List of solutions with their evaluations
            
        Returns:
            Dict containing the best solution and comparison results
        """
        if not solutions:
            return {"best_solution": None, "comparison": {}}
            
        # Find the solution with the highest overall score
        best_solution = max(solutions, key=lambda x: x.get('evaluation', {}).get('overall_score', 0))
        
        return {
            "best_solution": best_solution,
            "comparison": {
                "total_solutions": len(solutions),
                "average_score": sum(sol.get('evaluation', {}).get('overall_score', 0) 
                                   for sol in solutions) / len(solutions),
                "max_score": best_solution.get('evaluation', {}).get('overall_score', 0)
            }
        }

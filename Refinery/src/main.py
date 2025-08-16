#!/usr/bin/env python3
"""
Main entry point for the AI Refinery pipeline.

This script initializes and runs the recursive improvement pipeline with the
specified configuration and handles the results.
"""

import argparse
import json
import logging
import logging.handlers
import multiprocessing
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import partial

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Main log file
log_file = log_dir / f"refinery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Clear any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
    if hasattr(handler, 'close'):
        handler.close()

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8',
            mode='w'  # Overwrite existing log file for this run
        )
    ]
)

# Add console handler for warnings and above
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.WARNING)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Main process started. Logging to: {log_file.absolute()}")

def setup_worker_logging(worker_id: str) -> logging.Logger:
    """Set up logging for a worker process."""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        if hasattr(handler, 'close'):
            handler.close()
    
    # Create worker-specific log file
    worker_log_file = log_dir / f"worker_{worker_id}.log"
    
    # Configure root logger for this worker
    logging.basicConfig(
        level=logging.DEBUG,
        format=f'%(asctime)s - worker_{worker_id} - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                worker_log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=2,
                encoding='utf-8',
                mode='w'
            )
        ]
    )
    
    # Also log to the main log file
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        f'%(asctime)s - worker_{worker_id} - %(levelname)s - %(message)s'
    ))
    logging.getLogger('').addHandler(file_handler)
    
    return logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Now import project modules
try:
    from config import API_KEY, GENERATION_CONFIG
    from pipeline import RecursiveImprovementPipeline
except ImportError as e:
    logger.critical("Failed to import project modules: %s", str(e))
    logger.critical("Please ensure all dependencies are installed and the project structure is intact.")
    sys.exit(1)

def get_user_prompt() -> str:
    """
    Prompt the user for the initial prompt.
    
    Returns:
        str: The user's input prompt
    """
    print("\n" + "="*80)
    print("AI REFINERY - RECURSIVE IMPROVEMENT PIPELINE".center(80))
    print("="*80)
    print("\nEnter your initial prompt (press Enter on an empty line to finish):\n")
    
    lines = []
    empty_lines = 0
    
    while True:
        try:
            line = input()
            if not line.strip():
                # Just one empty line is enough to finish
                break
            else:
                empty_lines = 0
                lines.append(line)
        except EOFError:
            break
    
    prompt = '\n'.join(lines).strip()
    if not prompt:
        logger.warning("No prompt provided. Using default prompt.")
        prompt = "Explain the concept of artificial intelligence in simple terms."
    
    print(f"\nUsing prompt: {prompt}")
    return prompt

def run_pipeline_worker(worker_args) -> Optional[str]:
    """
    A wrapper function to run a single pipeline instance for a given prompt.
    
    Args:
        worker_args: Tuple containing (worker_id, prompt, args)
        
    Returns:
        str: Path to the saved results file, or None if failed
    """
    worker_id, prompt, args = worker_args
    
    # Set up logging for this worker
    worker_logger = setup_worker_logging(worker_id)
    worker_logger.info(f"Starting pipeline for prompt: '{prompt[:50]}...'")
    
    try:
        # Initialize the pipeline
        pipeline = RecursiveImprovementPipeline(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Run the pipeline with the prompt
        results = pipeline.run(
            original_prompt=prompt,
            max_iterations=args.iterations
        )
        
        # Save results
        output_dir = ensure_output_dir(args.output_dir)
        results_file = save_results(results, output_dir)
        worker_logger.info(f"Results for prompt '{prompt[:50]}...' saved to {results_file}")
        
        return str(results_file)
        
    except Exception as e:
        worker_logger.error(f"Error processing prompt '{prompt[:50]}...': {e}", exc_info=True)
        return None

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='AI Refinery: Recursive Improvement Pipeline',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='Example: python main.py --iterations 3'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=3,
        help='Number of improvement iterations to perform'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory to save results'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()

def ensure_output_dir(output_dir: str) -> Path:
    """Ensure the output directory exists and is writable."""
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Test if directory is writable
    test_file = output_path / '.write_test'
    try:
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        logger.error("Output directory is not writable: %s", output_dir)
        raise RuntimeError(f"Cannot write to output directory: {output_dir}") from e
    
    return output_path

def run_pipeline(args, prompt=None) -> dict:
    """
    Initialize and run the pipeline with the given arguments.
    
    Args:
        args: Parsed command line arguments
        prompt: Optional prompt string (if None, will call get_user_prompt)
        
    Returns:
        dict: Results from the pipeline
    """
    logger.info("Initializing standard pipeline...")
    
    try:
        # Initialize the pipeline
        pipeline = RecursiveImprovementPipeline(api_key=API_KEY)
        
        # Get the prompt if not provided
        if prompt is None:
            prompt = get_user_prompt()
        
        # Run the pipeline with the user's prompt
        logger.info("Starting pipeline with %d iterations", args.iterations)
        logger.debug("Prompt: %s", prompt)
        
        # Run the pipeline with the user's prompt
        results = pipeline.run(
            original_prompt=prompt,  # Use the prompt directly
            max_iterations=args.iterations
        )
        
        return results
        
    except Exception as e:
        logger.error("Pipeline execution failed: %s", str(e), exc_info=args.debug)
        raise

def save_results(results: dict, output_dir: Path) -> Path:
    """
    Save the pipeline results to a JSON file.
    
    Args:
        results: Results from the pipeline
        output_dir: Directory to save the results
        
    Returns:
        Path: Path to the saved results file
    """
    try:
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"refinery_{results.get('session_id', timestamp)}.json"
        output_path = output_dir / filename
        
        # Save the results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("Results saved to: %s", output_path)
        return output_path
        
    except Exception as e:
        logger.error("Failed to save results: %s", str(e))
        raise

def print_summary(results: Dict[str, Any]) -> None:
    """Print a summary of the pipeline results."""
    print("\n" + "="*80)
    print(f"{'AI REFINERY - PIPELINE SUMMARY':^80}")
    print("="*80)
    
    print(f"\n{'Session ID:':<20} {results.get('session_id', 'N/A')}")
    print(f"{'Timestamp:':<20} {results.get('timestamp', 'N/A')}")
    print(f"{'Prompt:':<20} {results.get('original_prompt', 'N/A')[:100]}...")
    print(f"{'Iterations:':<20} {len(results.get('iterations', []))}/{results.get('max_iterations', 0)}")
    
    # Iteration summaries
    print("\n" + "-"*40)
    print("ITERATION SUMMARIES".center(40))
    print("-"*40)
    
    for i, iteration in enumerate(results.get('iterations', []), 1):
        print(f"\n[ITERATION {i}]")
        
        # Solution summary
        solution = iteration.get('solution', '')
        if solution is not None:
            solution_summary = ' '.join(solution.split()[:30]) if solution else "[Empty solution]"
            print(f"  Solution: {solution_summary}...")
        else:
            print(f"  Solution: [No solution available]")
        
        # Critique summary if available
        if 'critique' in iteration and iteration['critique'] is not None:
            critique = iteration['critique']
            critique_summary = ' '.join(critique.split()[:20]) if critique else "[Empty critique]"
            print(f"  Critique: {critique_summary}...")
        elif 'critique' in iteration:
            print(f"  Critique: [No critique available]")
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETED SUCCESSFULLY".center(80))
    print("="*80)

def main():
    """Main entry point for the AI Refinery pipeline."""
    try:
        parser = argparse.ArgumentParser(description='AI Refinery: Recursive Improvement Pipeline')
        parser.add_argument('--prompt', type=str, help='The initial prompt to start the refinement process.')
        parser.add_argument('--prompt-file', type=str, help='Path to a text file containing the initial prompt.')
        parser.add_argument('--iterations', type=int, default=3, help='The number of refinement iterations to run.')
        parser.add_argument('--output-dir', type=str, default='output', help='Directory to save the output JSON file.')
        parser.add_argument('--debug', action='store_true', help='Enable detailed debug logging to the console.')
        parser.add_argument('--batch-file', type=str, help='Path to a text file with one prompt per line for batch processing.')
        parser.add_argument('--workers', type=int, default=min(4, os.cpu_count() or 1), 
                          help='Number of parallel processes for batch mode (default: min(4, CPU count))')

        args = parser.parse_args()

        # Configure debug logging if requested
        if args.debug:
            console.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        if args.batch_file:
            # --- BATCH PROCESSING MODE ---
            try:
                with open(args.batch_file, 'r', encoding='utf-8') as f:
                    prompts = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                logger.error(f"Batch file not found: {args.batch_file}")
                return 1

            if not prompts:
                logger.warning("Batch file is empty. No prompts to process.")
                return 0

            logger.info(f"Starting batch processing for {len(prompts)} prompts with {args.workers} workers.")
            logger.info(f"Main log: {log_file.absolute()}")
            
            # Prepare worker arguments
            worker_args = [(i, prompt, args) for i, prompt in enumerate(prompts)]
            
            # Process in parallel
            with multiprocessing.Pool(processes=args.workers) as pool:
                results = pool.map(run_pipeline_worker, worker_args)
            
            # Log completion
            successful_runs = [res for res in results if res is not None]
            logger.info(f"Batch processing complete. {len(successful_runs)}/{len(prompts)} runs succeeded.")
            print(f"\nBatch processing complete. See logs for details.")
            print(f"Results for {len(successful_runs)} successful runs saved in: {args.output_dir}")
            print(f"Main log: {log_file.absolute()}")

        else:
            # --- SINGLE PROMPT MODE ---
            if args.prompt:
                initial_prompt = args.prompt
            elif args.prompt_file:
                try:
                    with open(args.prompt_file, 'r', encoding='utf-8') as f:
                        initial_prompt = f.read().strip()
                except FileNotFoundError:
                    logger.error(f"Prompt file not found: {args.prompt_file}")
                    return 1
            else:
                initial_prompt = get_user_prompt()

            if not initial_prompt:
                logger.warning("No prompt provided. Exiting.")
                return 0

            # Run the pipeline
            results = run_pipeline(args, prompt=initial_prompt)
            
            # Save and show results
            output_dir = ensure_output_dir(args.output_dir)
            results_file = save_results(results, output_dir)
            print_summary(results)
            print(f"\nResults saved to: {results_file}")
            
        return 0
            
    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        return 1
        
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    if sys.platform in ["win32", "darwin"]:
        multiprocessing.set_start_method('spawn', force=True)
    sys.exit(main())

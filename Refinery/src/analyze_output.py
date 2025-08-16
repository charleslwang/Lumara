#!/usr/bin/env python3
"""
Output Analysis and Cleaning Utility for AI Refinery Pipeline

This script processes the JSON output files from the refinement pipeline.
It can either display a summary in the console or convert JSON files
into clean, human-readable .txt summaries and save them to a directory.

For each JSON file, it creates a subfolder and splits the content into
separate files for each solution and critique pairing.

Examples:

# Convert all files in 'output' to .txt files in 'cleaned_output'
python src/analyze_output.py

# Convert a single file and print its summary to the console
python src/analyze_output.py --file src/output/refinery_...json

# Convert a single file and also view details for a specific iteration
python src/analyze_output.py --file src/output/refinery_...json --iteration 2

"""

import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# ANSI color codes for better console output
COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
}

def color_text(text: str, color: str) -> str:
    """Apply color to text for console output."""
    return f"{COLORS.get(color, '')}{text}{COLORS['ENDC']}"


def generate_summary_text(data: Dict[str, Any], specific_iteration: Optional[int] = None) -> str:
    """Generate a clean, human-readable text summary from the JSON data."""
    lines = []

    def add_line(text="", indent=0):
        lines.append(" " * indent + text)

    add_line("=" * 80)
    add_line("AI REFINERY - SESSION SUMMARY")
    add_line("=" * 80)
    
    start_time_str = data.get('start_time', 'N/A')
    end_time_str = data.get('end_time', 'N/A')
    duration_str = "N/A"
    if start_time_str != 'N/A' and end_time_str != 'N/A':
        try:
            duration = (datetime.fromisoformat(end_time_str) - datetime.fromisoformat(start_time_str)).total_seconds()
            duration_str = f"{duration:.1f} seconds"
        except ValueError:
            pass # Keep duration as N/A if parsing fails

    add_line(f"Session ID: {data.get('session_id', 'N/A')}")
    add_line(f"Start Time: {start_time_str}")
    add_line(f"Duration:   {duration_str}")
    add_line()
    add_line("ORIGINAL PROMPT:")
    add_line(data.get('original_prompt', 'N/A'))
    add_line()

    iterations = data.get('iterations', [])
    if specific_iteration is not None:
        if 1 <= specific_iteration <= len(iterations):
            iterations = [iterations[specific_iteration - 1]]
        else:
            add_line(f"ERROR: Iteration {specific_iteration} not found.")
            return "\n".join(lines)

    for i, it in enumerate(iterations, 1):
        iteration_num = specific_iteration if specific_iteration is not None else i
        add_line("-" * 80)
        add_line(f"ITERATION {iteration_num} DETAILS")
        add_line("-" * 80)
        
        add_line("SOLUTION:")
        add_line(it.get('solution', 'N/A'))
        add_line()

        eval_data = it.get('evaluation', {})
        if eval_data:
            add_line("EVALUATION:")
            add_line(f"  Overall Score: {eval_data.get('overall_score', 'N/A')}")
            scores = eval_data.get('scores', {})
            if scores:
                add_line("  Scores:")
                for criterion, score in scores.items():
                    add_line(f"    - {criterion}: {score}")
            feedback = eval_data.get('feedback')
            if feedback:
                add_line("\n  Feedback:")
                add_line(f"  {feedback}")
        add_line()

        if 'critique' in it and it.get('critique') is not None:
            add_line("CRITIQUE FOR NEXT ITERATION:")
            add_line(it['critique'])
            add_line()

    return "\n".join(lines)


def generate_iteration_files(data: Dict[str, Any], output_dir: Path) -> None:
    """
    Generate separate files for each iteration's solution and critique.
    
    Args:
        data: The JSON data from the pipeline output
        output_dir: Directory to save the individual files
    """
    # Extract session info
    session_id = data.get('session_id', 'unknown')
    original_prompt = data.get('original_prompt', 'No prompt provided')
    
    # Write the original prompt to a file
    with open(output_dir / "00_original_prompt.txt", 'w', encoding='utf-8') as f:
        f.write("ORIGINAL PROMPT:\n")
        f.write("=" * 80 + "\n\n")
        f.write(original_prompt)
    
    # Process each iteration
    iterations = data.get('iterations', [])
    for i, iteration in enumerate(iterations, 1):
        # Create solution file
        solution = iteration.get('solution', 'No solution provided')
        with open(output_dir / f"{i:02d}_solution.txt", 'w', encoding='utf-8') as f:
            f.write(f"ITERATION {i} SOLUTION:\n")
            f.write("=" * 80 + "\n\n")
            f.write(solution)
        
        # Create evaluation file if available
        eval_data = iteration.get('evaluation', {})
        if eval_data:
            with open(output_dir / f"{i:02d}_evaluation.txt", 'w', encoding='utf-8') as f:
                f.write(f"ITERATION {i} EVALUATION:\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Overall Score: {eval_data.get('overall_score', 'N/A')}\n\n")
                
                scores = eval_data.get('scores', {})
                if scores:
                    f.write("Scores:\n")
                    for criterion, score in scores.items():
                        f.write(f"- {criterion}: {score}\n")
                    f.write("\n")
                
                feedback = eval_data.get('feedback')
                if feedback:
                    f.write("Feedback:\n")
                    f.write(feedback)
        
        # Create critique file if available
        critique = iteration.get('critique')
        if critique:
            with open(output_dir / f"{i:02d}_critique.txt", 'w', encoding='utf-8') as f:
                f.write(f"ITERATION {i} CRITIQUE:\n")
                f.write("=" * 80 + "\n\n")
                f.write(critique)


def process_file(file_path: Path, cleaned_dir: Path, specific_iteration: Optional[int] = None, console_output: bool = False) -> Optional[str]:
    """
    Process a single JSON file and save its cleaned version.
    
    Args:
        file_path: Path to the JSON file to process
        cleaned_dir: Base directory for cleaned output
        specific_iteration: Optional iteration number to focus on
        console_output: Whether to return the summary text for console output
        
    Returns:
        Optional[str]: Summary text if console_output is True, otherwise None
    """
    # Create a subfolder for this specific output file
    subfolder_name = file_path.stem
    output_subfolder = cleaned_dir / subfolder_name
    
    # Skip if already processed
    if output_subfolder.exists():
        print(f"Skipping, folder already exists: {output_subfolder}")
        return None if not console_output else "Folder already exists, skipping processing."

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create the subfolder
        output_subfolder.mkdir(parents=True, exist_ok=True)
        
        # Generate individual files for each iteration
        generate_iteration_files(data, output_subfolder)
        
        # Generate the summary text
        summary_text = generate_summary_text(data, specific_iteration)
        
        # Save the full summary
        with open(output_subfolder / "full_summary.txt", 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        print(f"Successfully processed: {file_path.name} -> {output_subfolder}")
        
        return summary_text if console_output else None

    except json.JSONDecodeError:
        print(color_text(f"Error: Invalid JSON in file {file_path}", 'RED'))
    except Exception as e:
        print(color_text(f"An unexpected error occurred while processing {file_path}: {e}", 'RED'))
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Analyze and clean AI Refinery output files.')
    parser.add_argument('--file', type=str, help='Path to a specific output JSON file to process.')
    parser.add_argument('--input-dir', type=str, default='output', help='Directory containing raw output JSON files.')
    parser.add_argument('--cleaned-dir', type=str, default='cleaned_output', help='Directory to save cleaned text files.')
    parser.add_argument('--iteration', type=int, help='Display details for a specific iteration.')
    parser.add_argument('--force', action='store_true', help='Force overwrite of existing output files.')
    
    args = parser.parse_args()
    
    cleaned_dir = Path(args.cleaned_dir)
    
    if args.file:
        # Process a single file and print to console
        file_path = Path(args.file)
        if not file_path.exists():
            print(color_text(f"Error: File not found: {file_path}", 'RED'))
            return
        
        # If force flag is set, remove existing output folder
        output_subfolder = cleaned_dir / file_path.stem
        if args.force and output_subfolder.exists():
            shutil.rmtree(output_subfolder)
            print(f"Removed existing folder: {output_subfolder}")
        
        summary_text = process_file(file_path, cleaned_dir, args.iteration, console_output=True)
        if summary_text:
            print("\n" + "="*80)
            print("CONSOLE OUTPUT:")
            print("="*80 + "\n")
            print(summary_text)

    else:
        # Batch process all files in the input directory
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(color_text(f"Error: Input directory not found: {input_dir}", 'RED'))
            return

        print(f"Processing all files in '{input_dir}'...\n")
        json_files = list(input_dir.glob('refinery_*.json'))
        if not json_files:
            print("No 'refinery_*.json' files found to process.")
            return
        
        # Create the base cleaned output directory if it doesn't exist
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file
        for file_path in json_files:
            # If force flag is set, remove existing output folder
            output_subfolder = cleaned_dir / file_path.stem
            if args.force and output_subfolder.exists():
                shutil.rmtree(output_subfolder)
                print(f"Removed existing folder: {output_subfolder}")
            
            process_file(file_path, cleaned_dir)
        
        print(f"\nProcessing complete. Results saved in: {cleaned_dir}")


if __name__ == "__main__":
    main()

"""
Lumara Core - Main package for the Lumara refinement pipeline.

This package provides the core functionality for the Lumara refinement pipeline,
which acts as a wrapper around the external Refinery pipeline.
"""

__version__ = "0.1.0"

import sys
from pathlib import Path

# Find and add the Refinery module to the path
refinery_path = Path(__file__).parent.parent.parent / 'Refinery' / 'src'
if not refinery_path.exists():
    raise ImportError(
        "Refinery source code not found at expected location. "
        f"Expected path: {refinery_path}\n"
        "Please ensure the Refinery repository is cloned at the correct location "
        "or set the REFINERY_PATH environment variable to point to the Refinery src directory."
    )
sys.path.append(str(refinery_path))

# Import Refinery components
from pipeline import RecursiveImprovementPipeline as RefineryPipeline
from judge import SolutionJudge
from config import MODEL_NAME, GENERATION_CONFIG, ADVANCED_CONFIG
from utils import load_prompt, extract_improvements, format_improvements, call_gemini_with_retry

# Re-export the important components
__all__ = [
    'RefineryPipeline',
    'SolutionJudge',
    'MODEL_NAME',
    'GENERATION_CONFIG',
    'ADVANCED_CONFIG',
    'load_prompt',
    'extract_improvements',
    'format_improvements',
    'call_gemini_with_retry'
]

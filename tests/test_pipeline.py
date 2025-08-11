"""
Test script for the Lumara pipeline.

This script provides a simple way to test the core pipeline functionality.
It includes multiple test cases to verify different aspects of the pipeline.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file if it exists
dotenv_path = Path(__file__).parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Import the pipeline after setting up the path
from core.pipeline import create_pipeline

class PipelineTester:
    """Helper class to test the Lumara pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the tester with optional config overrides."""
        self.config = {
            'max_iterations': 2,  # Keep it short for testing
            'debug': True,
            **(config or {})
        }
        self.pipeline = create_pipeline(self.config)
    
    async def test_refinement(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """Test the refinement pipeline with a given test case."""
        print(f"\n{'='*80}")
        print(f"TEST CASE: {test_case['name']}")
        print(f"{'='*80}")
        
        try:
            result = await self.pipeline.refine(
                prompt=test_case['prompt'],
                model_output=test_case['model_output']
            )
            
            self._print_result(result)
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_exc()
            return {'error': str(e)}
    
    def _print_result(self, result: Dict[str, Any]) -> None:
        """Print the test result in a readable format."""
        print(f"\n✅ Refinement successful!")
        print(f"Iterations: {result['iterations']}")
        
        if 'scores' in result and 'overall' in result['scores']:
            print(f"Overall score: {result['scores']['overall']:.1f}/10")
        
        print("\nOriginal output:")
        print("-" * 40)
        print(result.get('original_output', 'N/A'))
        
        print("\nRefined output:")
        print("-" * 40)
        print(result['refined_output'])
        
        if 'scores' in result and 'details' in result['scores']:
            print("\nEvaluation details:")
            print("-" * 40)
            for criterion, score in result['scores']['details'].get('scores', {}).items():
                print(f"- {criterion}: {score}/10")
        
        if 'error' in result:
            print(f"\n⚠️  Warning: {result['error']}")


# Define test cases
TEST_CASES = [
    {
        'name': 'Haiku Refinement',
        'prompt': 'Write a haiku about artificial intelligence',
        'model_output': 'AI learns and grows fast\nMachines think like humans now\nThe future is here'
    },
    {
        'name': 'Code Explanation',
        'prompt': 'Explain this Python function: def add(a, b): return a + b',
        'model_output': 'This function adds two numbers together and returns the result.'
    },
    {
        'name': 'Story Completion',
        'prompt': 'Complete this story: The last robot on Earth sat alone in a room.',
        'model_output': 'It wondered what had happened to all the other robots.'
    }
]

async def main():
    """Run all test cases."""
    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your Google API key:")
        print("1. Get an API key from: https://aistudio.google.com/app/apikey")
        print("2. Create a .env file in the project root and add:")
        print("   GOOGLE_API_KEY=your_api_key_here")
        return
    
    print("🚀 Starting Lumara Pipeline Tests")
    print("=" * 40)
    print(f"Model: gemini-pro")
    print(f"Max iterations: 2 (for testing)")
    print("-" * 40)
    
    tester = PipelineTester()
    
    # Run all test cases
    for test_case in TEST_CASES:
        await tester.test_refinement(test_case)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

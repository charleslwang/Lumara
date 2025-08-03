import sys
import os
from pathlib import Path

class RefineryWrapper:
    def __init__(self, api_key, refinery_project_path):
        self.api_key = api_key
        self.refinery_project_path = refinery_project_path
        self._pipeline = None

        if str(self.refinery_project_path) not in sys.path:
            sys.path.insert(0, str(self.refinery_project_path))

    def _get_pipeline(self):
        if self._pipeline is None:
            try:
                from pipeline import RecursiveImprovementPipeline
                self._pipeline = RecursiveImprovementPipeline(api_key=self.api_key)
            except ImportError as e:
                raise RuntimeError(f"Could not import the Refinery pipeline. Make sure the path is correct. Error: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize the Refinery pipeline: {e}")
        return self._pipeline

    def run(self, prompt, iterations=3):
        pipeline = self._get_pipeline()
        try:
            results = pipeline.run(
                original_prompt=prompt,
                max_iterations=iterations
            )
            return results
        except Exception as e:
            # Log the exception
            print(f"Error running refinery pipeline: {e}")
            raise e

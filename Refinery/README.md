# Refinery: Recursive Self-Improvement Pipeline

Refinery is a Python-based framework designed to autonomously improve and refine text-based solutions through a recursive process of generation, critique, and evaluation. By leveraging generative AI models like Google's Gemini, this pipeline can take an initial prompt and iteratively enhance the output to meet a set of defined quality criteria.

It is ideal for tasks that benefit from iterative refinement, such as creative writing, code generation, complex problem-solving, and detailed content creation.

## Key Features

- **Recursive Improvement**: Automatically refines solutions over multiple iterations.
- **AI-Powered Critique**: Generates actionable feedback to guide improvements.
- **Quantitative Evaluation**: Scores solutions based on predefined criteria (e.g., novelty, clarity, feasibility) using an AI judge.
- **Configurable Pipeline**: Easily customize prompts, models, and iteration counts.
- **Robust Error Handling**: Includes retry logic with exponential backoff for API calls.
- **Detailed Logging**: Captures all pipeline activity into timestamped log files.
- **Output Analysis Utility**: A powerful script to analyze, summarize, and clean up pipeline results.

## Directory Structure

```
/Refinery
|-- src/
|   |-- main.py             # Main entry point to run the pipeline
|   |-- pipeline.py         # Core recursive improvement logic
|   |-- judge.py            # AI-powered solution evaluation
|   |-- config.py           # Configuration (models, paths)
|   |-- utils.py            # Utility functions (API calls, retries)
|   `-- analyze_output.py   # Script to analyze and clean results
|
|-- prompts/
|   |-- solution_template.txt
|   |-- critique_template.txt
|   `-- ...                 # Prompt templates for the AI models
|
|-- output/                 # Raw JSON output files from each run
|-- cleaned_output/         # Human-readable .txt summaries
|-- logs/                   # Detailed log files for debugging
|
`-- README.md
```

## Setup and Installation

1.  **Clone the Repository**

    ```bash
    git clone <repository_url>
    cd Refinery
    ```

2.  **Install Dependencies**

    Ensure you have Python 3.8+ installed. Then, install the required packages:

    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If a `requirements.txt` file is not available, you will need `pip install google-generativeai`)*

3.  **Set Up API Key**

    The pipeline requires a Google Gemini API key. Set it as an environment variable:

    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

## How to Run the Pipeline

Execute the main script from the project's root directory. The script will guide you to enter a prompt.

```bash
python src/main.py
```

### Command-Line Arguments

-   `--prompt-file`: Path to a text file containing the initial prompt.
-   `--max-iterations`: The number of improvement cycles to run (default: 3).
-   `--output-dir`: Directory to save the raw JSON results (default: `output`).
-   `--debug`: Enable detailed debug logging to the console.

**Example:**

```bash
python src/main.py --prompt-file prompts/my_prompt.txt --max-iterations 5
```

## Analyzing Results

The `analyze_output.py` script is a powerful tool for processing the pipeline's results.

### 1. Batch Convert All Results to Clean Summaries

This is the primary use case. Run the script without arguments to convert all JSON files from the `output` directory into clean `.txt` summaries in the `cleaned_output` directory. It will not overwrite existing files.

```bash
python src/analyze_output.py
```

### 2. View a Specific File in the Console

To quickly view a summary of a specific run without creating a file, use the `--file` flag.

```bash
python src/analyze_output.py --file src/output/refinery_recursive_session_...json
```

### 3. View a Specific Iteration

To see the full solution, critique, and evaluation for a single iteration from a specific file, use the `--iteration` flag.

```bash
python src/analyze_output.py --file src/output/refinery_...json --iteration 2
```

## How It Works

1.  **Initialization**: The user provides an initial prompt.
2.  **Generate Solution**: The AI generates the first version of the solution.
3.  **Recursive Loop**:
    a.  **Evaluate Solution**: An AI "judge" scores the current solution against defined criteria.
    b.  **Generate Critique**: A separate AI instance critiques the solution, providing specific, actionable feedback for improvement.
    c.  **Refine Solution**: The original AI uses the solution, critique, and evaluation feedback to generate a new, improved version.
4.  **Completion**: The loop continues for the specified number of iterations, with the final, refined solution as the primary output.

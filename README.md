# Lumara - AI Content Refinement Platform

Lumara is a sophisticated platform that leverages advanced AI models to iteratively refine and improve content. The platform uses a recursive improvement pipeline that evaluates and enhances content through multiple iterations.

## Features

- **Elegant UI**: A clean, sophisticated interface with subtle purple palette and modern design elements
- **Multiple AI Models**: Support for GPT-4o, Gemini 2.5 Pro, and Gemini 2.5 Flash
- **Iterative Refinement**: Content is improved through multiple iterations with detailed feedback
- **Comprehensive Evaluation**: Each refinement is scored across multiple dimensions
- **API Integration**: Seamless connection between frontend and backend

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (get one from https://aistudio.google.com/app/apikey)
- Virtual environment tool (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/lumara.git
   cd lumara
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv lumara_venv
   source lumara_venv/bin/activate  # On Windows: lumara_venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

### Running the Application

1. Activate the virtual environment if not already activated:
   ```
   source lumara_venv/bin/activate  # On Windows: lumara_venv\Scripts\activate
   ```

2. Start the application:
   ```
   python api.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Enter your original prompt in the "Original Prompt" field
2. Paste the AI model output you want to refine in the "AI Model Output" field
3. Select your preferred AI model from the dropdown (GPT-4o, Gemini 2.5 Pro, or Gemini 2.5 Flash)
4. Enter your API key
5. Click "Refine Output" to start the refinement process
6. View the refined output, iteration details, and evaluation scores in the results section

## Project Structure

```
lumara/
├── api.py                # Flask API server connecting frontend to core
├── core/                 # Core refinement pipeline
│   ├── __init__.py       # Package initialization and imports
│   ├── config.py         # Configuration settings
│   └── pipeline.py       # Main pipeline implementation
├── frontend/             # Web interface
│   ├── index.html        # Main HTML file
│   ├── script.js         # Frontend JavaScript
│   └── styles.css        # CSS styling
├── prompts/              # Prompt templates for the pipeline
├── requirements.txt      # Python dependencies
└── run.sh               # Convenience script for running the application
```

## Architecture

Lumara consists of two main components:

1. **Frontend**: A modern web interface built with HTML, CSS, and JavaScript that provides a user-friendly way to interact with the refinement pipeline.

2. **Backend**: A Python-based API server that connects to the core refinement pipeline, which uses the Google Gemini API to process and improve content.

The core pipeline uses a recursive improvement approach that:
1. Evaluates the current solution
2. Generates critiques and improvement suggestions
3. Creates a refined solution
4. Repeats until reaching the maximum iterations or quality threshold

## License

This project is licensed under the MIT License - see the LICENSE file for details.

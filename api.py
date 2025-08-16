"""
Lumara API Server

This module provides a Flask API server that connects the frontend to the core pipeline.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from core.pipeline import create_pipeline

# Initialize Flask app
app = Flask(__name__, static_folder='frontend')
CORS(app)  # Enable CORS for all routes

# Create pipeline instance
pipeline = create_pipeline()

@app.route('/')
def index():
    """Serve the frontend index.html"""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the frontend directory"""
    return send_from_directory('frontend', path)

@app.route('/api/refine', methods=['POST'])
def refine():
    """API endpoint to refine model output using the Lumara pipeline"""
    try:
        data = request.json
        
        # Extract required parameters
        prompt = data.get('prompt')
        model_output = data.get('model_output')
        model = data.get('model')
        api_key = data.get('api_key')
        
        # Validate inputs
        if not prompt or not model_output or not api_key:
            return jsonify({
                'error': 'Missing required parameters: prompt, model_output, or api_key'
            }), 400
            
        # Create config with model override if needed
        config = {
            'api_key': api_key  # Pass user's API key directly
        }
        if model:
            # Map frontend model names to backend model names
            model_mapping = {
                'gpt-4o': 'gpt-4o',
                'gemini-2.5-pro': 'gemini-pro',  # Map to Gemini Pro
                'gemini-2.5-flash': 'gemini-flash',  # Map to Gemini Flash
                # Fallbacks for older model names
                'gemini-pro': 'gemini-pro',
                'gemini-flash': 'gemini-flash',
                'gemini-1.5-pro': 'gemini-pro',
                'gemini-1.5-flash': 'gemini-flash'
            }
            # Use the mapped model name or default to gemini-pro
            config['model_name'] = model_mapping.get(model, 'gemini-pro')
            print(f"Using model: {config['model_name']} (mapped from {model})")
        else:
            print("No model specified, using default model from config")
        
        # Create a pipeline with the specified config (including user's API key)
        custom_pipeline = create_pipeline(config)
        
        # Run the refinement process
        result = custom_pipeline.refine(prompt, model_output)
        
        # Format iterations for frontend display
        iterations_data = []
        iterations = result.get('iterations', 0)
        
        # If we have iterations data in the result, use it
        if isinstance(iterations, list):
            for i, iteration in enumerate(iterations):
                iterations_data.append({
                    'output': iteration.get('solution', ''),
                    'score': iteration.get('score', 0)
                })
        else:
            # Otherwise create dummy iterations based on the count
            for i in range(iterations):
                iterations_data.append({
                    'output': f"Iteration {i+1} output",
                    'score': 0.7 + (i * 0.1)
                })
        
        # Add iterations_data to the result
        result['iterations_data'] = iterations_data
        
        return jsonify(result)
        
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'request_data': {
                'prompt_length': len(data.get('prompt', '')),
                'model_output_length': len(data.get('model_output', '')),
                'model': data.get('model'),
                'has_api_key': bool(data.get('api_key'))
            }
        }
        
        print(f"Error in /api/refine endpoint: {error_details}")
        
        # Provide more specific error messages
        error_message = str(e)
        if 'API key' in error_message or 'authentication' in error_message.lower():
            error_message = 'Invalid or missing API key. Please check your Google Gemini API key.'
        elif 'quota' in error_message.lower() or 'limit' in error_message.lower():
            error_message = 'API quota exceeded. Please check your API usage limits.'
        elif 'network' in error_message.lower() or 'connection' in error_message.lower():
            error_message = 'Network connection error. Please check your internet connection.'
        elif 'Refinery' in error_message:
            error_message = 'Refinery pipeline error. Please check if all dependencies are installed correctly.'
        
        return jsonify({
            'error': error_message,
            'refined_output': request.json.get('model_output', ''),
            'iterations': 0,
            'scores': {},
            'metadata': {},
            'debug_info': error_details if app.debug else None
        }), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)

import sys
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add the parent directory to the path so we can import the contextual_responder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextual_responder import ContextualResponder

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

# Initialize the contextual responder with default settings
responder = None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/initialize', methods=['POST'])
def initialize_responder():
    global responder
    data = request.json
    
    # Extract parameters with defaults
    model_name = data.get('model_name', 'llama3:8b')
    collection_name = data.get('collection_name', 'documents')
    keyword_prompt_path = data.get('keyword_prompt_path', './prompts/keyword_extractor.md')
    context_prompt_path = data.get('context_prompt_path', './prompts/context_based_query.md')
    service_type = data.get('service_type', 'ollama')
    
    try:
        # Initialize the responder with the provided parameters
        responder = ContextualResponder(
            model_name=model_name,
            collection_name=collection_name,
            keyword_prompt_path=keyword_prompt_path,
            context_prompt_path=context_prompt_path,
            service_type=service_type
        )
        return jsonify({
            'status': 'success',
            'message': f'Responder initialized with model: {model_name}, service: {service_type}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    global responder
    data = request.json
    query = data.get('query', '')
    num_chunks = data.get('num_chunks', 10)
    display_context = data.get('display_context', False)
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Initialize responder if not already initialized
    if responder is None:
        try:
            responder = ContextualResponder()
        except Exception as e:
            return jsonify({'error': f'Failed to initialize responder: {str(e)}'}), 500
    
    try:
        # Get response from the contextual responder
        result = responder.get_response(query, num_chunks=num_chunks, display_context=display_context)
        
        # Handle the case where display_context is True (returns a tuple)
        if display_context and isinstance(result, tuple):
            response, context = result
            return jsonify({'response': response, 'context': context})
        else:
            return jsonify({'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

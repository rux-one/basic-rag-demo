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

# Initialize the contextual responder
responder = ContextualResponder()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Get response from the contextual responder
        response = responder.get_response(query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

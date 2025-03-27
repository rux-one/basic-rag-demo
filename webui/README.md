# RAG Chat Web UI

This is a simple HTML5 chat interface that interacts with the `contextual_responder.py` functionality via HTTP requests.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the Flask API server:

```bash
python api.py
```

3. Open your browser and navigate to `http://localhost:8080`

## Features

- Clean, responsive chat interface
- Real-time interaction with the contextual responder
- Support for markdown-like formatting in messages (code blocks, links)
- Typing indicators while waiting for responses
- Configurable settings for the ContextualResponder:
  - Model name (e.g., "llama3:8b", "gpt-3.5-turbo")
  - Collection name for document retrieval
  - Keyword and context prompt paths
  - Service type (Ollama or OpenAI)
  - Number of chunks to retrieve
  - Option to display context used for responses

## How It Works

The web UI sends user queries to the Flask API, which then uses the `ContextualResponder` class to generate contextual responses based on the documents in the system. The responses are then displayed in the chat interface.

You can customize the behavior of the responder by clicking the settings icon in the top-right corner of the chat interface. This allows you to change the model, service type, and other parameters without modifying the code.

## Files

- `index.html`: The main HTML file that defines the structure of the chat interface
- `styles.css`: CSS styles for the chat interface
- `script.js`: JavaScript code that handles the chat functionality
- `api.py`: Flask API that interfaces with the `ContextualResponder`
- `requirements.txt`: List of Python dependencies

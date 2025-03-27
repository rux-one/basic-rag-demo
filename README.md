# Simple RAG Demo

This is a simple Retrieval-Augmented Generation (RAG) demo using Qdrant as the vector database.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Local Ollama OR OpenAI api key

### General flow

See `./rag-demo.drawio` for a high-level overview of the workflow.

### Installation

See .env.example for instructions on setting up your environment variables.

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Starting the Qdrant Vector Database

To start the Qdrant vector database, run:

```bash
docker compose up -d
```

This will start Qdrant on:
- REST API: http://localhost:6333
- gRPC API: localhost:6334
- Dashboard: http://localhost:6333/dashboard

### Running the Demo
 
To start the document feeder: `python agent.py` - it will scan `./storage/input` for documents every N seconds. (Default is 10 seconds)

To respond to user queries: `python contextual_responder.py [--service openai] --query "<your question goes here>"`
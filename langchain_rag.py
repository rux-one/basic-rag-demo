import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader

# Initialize embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load and process documents
def load_documents():
    # Load documents
    loader = TextLoader("data/knowledge.md")
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=0)
    chunks = text_splitter.split_documents(documents)
    
    print(f"Split documents into {len(chunks)} chunks")
    return chunks

# Create vector store
def create_vector_store(chunks):
    # Create Qdrant vector store
    vector_store = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        url="http://localhost:6333",
        collection_name="langchain_docs",
        force_recreate=True
    )
    
    print("Created Qdrant vector store with documents")
    return vector_store

# Search for similar documents
def search_documents(vector_store, query, k=2):
    # Search for similar documents
    docs = vector_store.similarity_search(query, k=k)
    
    print(f"\nQuery: {query}")
    print("Results:")
    for i, doc in enumerate(docs):
        print(f"{i+1}. {doc.page_content}")

# Main function
def main():
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Search documents using RAG')
    parser.add_argument('--query', type=str, required=True, help='Query to search for')
    args = parser.parse_args()
    
    # Load and process documents
    chunks = load_documents()
    
    # Create vector store
    vector_store = create_vector_store(chunks)
    
    # Search for the query
    search_documents(vector_store, args.query)

if __name__ == "__main__":
    main()

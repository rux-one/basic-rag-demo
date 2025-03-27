import logging
from typing import List, Optional

from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChunkFinder')

# Initialize embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

class ChunkFinder:
    def __init__(self, 
                 collection_name: str = "documents",
                 qdrant_url: str = "http://localhost:6333"):
        """
        Initialize the ChunkFinder.
        
        Args:
            collection_name (str): Name of the Qdrant collection to search in. Defaults to "documents".
            qdrant_url (str): URL of the Qdrant server. Defaults to "http://localhost:6333".
        """
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        
        try:
            # Create a simple placeholder document to ensure there's at least one embedding
            placeholder_doc = Document(page_content="This is a placeholder document for initialization.")
            
            # Connect to Qdrant collection for similarity search
            self.vector_store = Qdrant.from_documents(
                documents=[placeholder_doc],  # Use a placeholder document
                embedding=embeddings,
                url=qdrant_url,
                collection_name=collection_name,
                force_recreate=False  # Don't recreate the collection
            )
            logger.info(f"Connected to Qdrant collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {str(e)}")
            logger.error("Make sure the Qdrant server is running and accessible.")
            raise
        
        logger.info("ChunkFinder initialized")
    
    def find_chunks(self, keywords: str, num_chunks: int = 5) -> List[Document]:
        """
        Find chunks related to the given keywords.
        
        Args:
            keywords (str): Comma-separated list of keywords
            num_chunks (int): Number of chunks to retrieve. Defaults to 5.
            
        Returns:
            List[Document]: List of relevant document chunks
        """
        # Process the keywords
        if isinstance(keywords, str):
            # Split the comma-separated string into a list
            keyword_list = [k.strip() for k in keywords.split(',')]
        else:
            # Assume it's already a list
            keyword_list = keywords
        
        # Join the keywords into a search query
        search_query = " ".join(keyword_list)
        logger.info(f"Searching for chunks related to: {search_query}")
        
        try:
            # Search for relevant documents
            docs = self.vector_store.similarity_search(search_query, k=num_chunks)
            
            # Filter out the placeholder document if it exists in the results
            filtered_docs = [doc for doc in docs if "This is a placeholder document for initialization." not in doc.page_content]
            
            logger.info(f"Retrieved {len(filtered_docs)} document chunks")
            return filtered_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def find_chunks_by_query(self, query: str, num_chunks: int = 5) -> List[Document]:
        """
        Find chunks related to the given query.
        
        Args:
            query (str): Search query
            num_chunks (int): Number of chunks to retrieve. Defaults to 5.
            
        Returns:
            List[Document]: List of relevant document chunks
        """
        logger.info(f"Searching for chunks related to query: {query}")
        
        try:
            # Search for relevant documents
            docs = self.vector_store.similarity_search(query, k=num_chunks)
            
            # Filter out the placeholder document if it exists in the results
            filtered_docs = [doc for doc in docs if "This is a placeholder document for initialization." not in doc.page_content]
            
            logger.info(f"Retrieved {len(filtered_docs)} document chunks")
            return filtered_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Find chunks related to keywords')
    parser.add_argument('--keywords', type=str, required=True, help='Comma-separated list of keywords')
    parser.add_argument('--collection', type=str, default="documents", help='Qdrant collection name')
    parser.add_argument('--num-chunks', type=int, default=3, help='Number of chunks to retrieve')
    args = parser.parse_args()
    
    # Create chunk finder
    chunk_finder = ChunkFinder(collection_name=args.collection)
    
    # Find chunks related to the keywords
    docs = chunk_finder.find_chunks(args.keywords, num_chunks=args.num_chunks)
    
    # Print the results
    print(f"\nKeywords: {args.keywords}")
    print(f"Retrieved {len(docs)} document chunks:")
    for i, doc in enumerate(docs):
        print(f"\nChunk {i+1}:")
        print(f"{doc.page_content}")
        if hasattr(doc, 'metadata') and doc.metadata:
            print(f"Metadata: {doc.metadata}")

import logging
import warnings
from typing import List, Optional

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant

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
    
    def find_chunks(self, keywords: str, num_chunks: int = 10) -> List[Document]:
        """
        Find chunks related to the given keywords.
        
        Args:
            keywords (str): Comma-separated list of keywords
            num_chunks (int): Total number of chunks to retrieve. Defaults to 10.
            
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
        
        # Remove empty keywords
        keyword_list = [k for k in keyword_list if k]
        
        if not keyword_list:
            logger.warning("No valid keywords provided")
            return []
        
        logger.info(f"Searching for chunks related to keywords: {keyword_list}")
        
        # Calculate chunks per keyword to ensure fair distribution
        chunks_per_keyword = max(1, num_chunks // len(keyword_list))
        # Calculate extra chunks to distribute (remainder)
        extra_chunks = num_chunks % len(keyword_list)
        
        logger.info(f"Allocating approximately {chunks_per_keyword} chunks per keyword")
        
        # Dictionary to store documents per keyword
        keyword_docs = {}
        
        try:
            # Search for each keyword individually
            for keyword in keyword_list:
                logger.info(f"Searching for chunks related to keyword: {keyword}")
                
                try:
                    # Search for relevant documents for this keyword
                    # Get more chunks than needed to account for filtering and have some extras
                    search_k = chunks_per_keyword * 2
                    docs = self.vector_store.similarity_search(keyword, k=search_k)
                    
                    # Filter out the placeholder document if it exists in the results
                    filtered_docs = [doc for doc in docs if "This is a placeholder document for initialization." not in doc.page_content]
                    
                    logger.info(f"Retrieved {len(filtered_docs)} document chunks for keyword: {keyword}")
                    
                    # Store in our dictionary
                    keyword_docs[keyword] = filtered_docs
                except Exception as e:
                    logger.error(f"Error retrieving documents for keyword '{keyword}': {str(e)}")
                    keyword_docs[keyword] = []
            
            # Combine documents with fair distribution
            combined_docs = []
            seen_content = set()
            
            # First pass: take chunks_per_keyword from each keyword
            for keyword, docs in keyword_docs.items():
                added = 0
                for doc in docs:
                    if doc.page_content not in seen_content and added < chunks_per_keyword:
                        seen_content.add(doc.page_content)
                        combined_docs.append(doc)
                        added += 1
            
            # Second pass: distribute extra chunks
            if extra_chunks > 0:
                for keyword, docs in keyword_docs.items():
                    if extra_chunks <= 0:
                        break
                        
                    for doc in docs:
                        if doc.page_content not in seen_content and extra_chunks > 0:
                            seen_content.add(doc.page_content)
                            combined_docs.append(doc)
                            extra_chunks -= 1
                            
                        if extra_chunks <= 0:
                            break
            
            logger.info(f"Retrieved {len(combined_docs)} unique document chunks across all keywords")
            return combined_docs
            
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

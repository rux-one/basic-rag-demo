import os
import logging
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocumentFeeder')

# Initialize embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def feed_document_to_qdrant(markdown_file_path, collection_name, chunk_size=200, chunk_overlap=0):
    """
    Chunks a Markdown file and embeds it into a Qdrant collection.
    
    Args:
        markdown_file_path (str): Path to the Markdown file to process
        collection_name (str): Name of the Qdrant collection to add the document to
        chunk_size (int, optional): Size of text chunks. Defaults to 200.
        chunk_overlap (int, optional): Overlap between chunks. Defaults to 0.
        
    Returns:
        bool: True if the document was successfully processed and added to Qdrant, False otherwise
    """
    try:
        # Check if the file exists
        if not os.path.exists(markdown_file_path):
            logger.error(f"File not found: {markdown_file_path}")
            return False
            
        logger.info(f"Processing document: {markdown_file_path}")
        logger.info(f"Target collection: {collection_name}")
        
        # Load the document
        loader = TextLoader(markdown_file_path)
        documents = loader.load()
        logger.info(f"Loaded document with {len(documents)} pages")
        
        # Split the document into chunks
        text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = text_splitter.split_documents(documents)
        logger.info(f"✂️ Split document into {len(chunks)} chunks")
        
        # Create Qdrant vector store and add the chunks
        # Note: We're not using force_recreate=True to preserve existing documents
        vector_store = Qdrant.from_documents(
            documents=chunks,
            embedding=embeddings,
            url="http://localhost:6333",
            collection_name=collection_name,
            force_recreate=False
        )
        
        logger.info(f"💾 Successfully added document to Qdrant collection '{collection_name}'")
        return True
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return False


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Feed a document to Qdrant')
    parser.add_argument('--file', type=str, required=True, help='Path to the Markdown file')
    parser.add_argument('--collection', type=str, required=True, help='Qdrant collection name')
    parser.add_argument('--chunk-size', type=int, default=200, help='Size of text chunks')
    parser.add_argument('--chunk-overlap', type=int, default=0, help='Overlap between chunks')
    args = parser.parse_args()
    
    # Feed the document to Qdrant
    success = feed_document_to_qdrant(
        args.file,
        args.collection,
        args.chunk_size,
        args.chunk_overlap
    )
    
    if success:
        print(f"Successfully processed {args.file} and added to collection {args.collection}")
    else:
        print(f"Failed to process {args.file}")

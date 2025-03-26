import threading
import time
import os
import logging

# Import our custom modules
from documents_watcher import get_new_files_delta
from document_converter import convert_document_to_markdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocumentProcessingAgent')


class DocumentProcessingWorker:
    def __init__(self, check_interval=5):
        self.running = False
        self.thread = None
        self.check_interval = check_interval  # Time in seconds between checks for new files
        logger.info("Document Processing Worker initialized with check interval of %d seconds", check_interval)
    
    def start(self):
        if self.running:
            logger.warning("Worker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Document Processing Worker started")
    
    def stop(self):
        if not self.running:
            logger.warning("Worker is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Document Processing Worker stopped")
    
    def _run(self):
        while self.running:
            try:
                logger.debug("Checking for new documents...")
                new_files = get_new_files_delta()
                
                if new_files:
                    logger.info("Found %d new documents to process", len(new_files))
                    
                    for filename in new_files:
                        # Check if it's a PDF file (we can add more file types later if needed)
                        if filename.lower().endswith('.pdf'):
                            input_path = os.path.join('./storage/input', filename)
                            # Create output filename by replacing the extension with .md
                            output_filename = os.path.splitext(filename)[0] + '.md'
                            output_path = os.path.join('./storage/output', output_filename)
                            
                            logger.info("Processing document: %s", filename)
                            logger.info("Input path: %s", input_path)
                            logger.info("Output path: %s", output_path)
                            
                            # Convert the document
                            success = convert_document_to_markdown(input_path, output_path)
                            
                            if success:
                                logger.info("Successfully converted %s to Markdown", filename)
                            else:
                                logger.error("Failed to convert %s to Markdown", filename)
                        else:
                            logger.warning("Skipping non-PDF file: %s", filename)
                else:
                    logger.debug("No new documents found")
            except Exception as e:
                logger.error("Error in document processing: %s", str(e))
            
            # Wait before checking again
            time.sleep(self.check_interval)


# Example usage
if __name__ == "__main__":
    # Create and start the document processing worker
    worker = DocumentProcessingWorker(check_interval=10)  # Check every 10 seconds
    worker.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
        logger.info("Program terminated")

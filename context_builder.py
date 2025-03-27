import os
import re
import logging
from typing import List, Optional

from chat_service import ChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ContextBuilder')

class ContextBuilder:
    def __init__(self, 
                 model_name: str = "llama3:8b",
                 keyword_prompt_path: str = "./prompts/keyword_extractor.md"):
        """
        Initialize the ContextBuilder.
        
        Args:
            model_name (str): Name of the model to use for keyword extraction. Defaults to "llama3:8b".
            keyword_prompt_path (str): Path to the keyword extraction prompt. Defaults to "./prompts/keyword_extractor.md".
        """
        self.model_name = model_name
        self.keyword_prompt_path = keyword_prompt_path
        self.chat_service = ChatService()
        
        # Load the keyword extraction prompt
        self._load_keyword_prompt()
        
        logger.info("ContextBuilder initialized")
    
    def _load_keyword_prompt(self):
        """
        Load the keyword extraction prompt from file.
        """
        try:
            with open(self.keyword_prompt_path, 'r', encoding='utf-8') as f:
                self.keyword_prompt_template = f.read()
            logger.info(f"Loaded keyword extraction prompt from {self.keyword_prompt_path}")
        except Exception as e:
            logger.error(f"Error loading keyword prompt: {str(e)}")
            # Fallback to a simple prompt if the file can't be loaded
            self.keyword_prompt_template = """Extract the most important keywords from this query: {{USER_QUERY}}\n\nOutput only the keywords as a comma-separated list."""
    
    async def extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from the user query using the LLM.
        
        Args:
            query (str): The user's query
            
        Returns:
            List[str]: List of extracted keywords
        """
        # Replace the placeholder in the prompt template
        prompt = self.keyword_prompt_template.replace("{{USER_QUERY}}", query)
        
        logger.info(f"Extracting keywords for query: {query}")
        
        # Get response from the LLM using the chat function (which returns a generator, not an async iterator)
        response = ""
        for chunk in self.chat_service.chat(
            model=self.model_name,
            user_prompt=prompt,
            stream=True
        ):
            response += chunk
        
        # Extract keywords from the response using regex
        keywords_match = re.search(r'<keywords>(.*?)</keywords>', response, re.DOTALL)
        
        if keywords_match:
            # Extract the keywords and split by comma
            keywords_str = keywords_match.group(1).strip()
            keywords = [kw.strip() for kw in keywords_str.split(',')]
            logger.info(f"Extracted keywords: {keywords}")
            return keywords
        else:
            # If no keywords tag found, just split by comma (fallback)
            logger.warning("No <keywords> tags found in response, using fallback method")
            keywords = [kw.strip() for kw in response.split(',')]
            return keywords


# Example usage
if __name__ == "__main__":
    import asyncio
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract keywords from a query')
    parser.add_argument('--query', type=str, required=True, help='Query to extract keywords from')
    args = parser.parse_args()
    
    # Create context builder
    context_builder = ContextBuilder()
    
    # Extract keywords from the query
    async def main():
        keywords = await context_builder.extract_keywords(args.query)
        print(f"\nQuery: {args.query}")
        print(f"Extracted keywords: {keywords}")
    
    # Run the async function
    asyncio.run(main())
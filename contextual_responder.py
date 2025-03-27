import os
import re
import logging
from typing import List, Optional, Tuple, Union, Literal

from chunk_finder import ChunkFinder
from chat_service import ChatService
from openai_chat_service import OpenAIChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ContextualResponder')

class ContextualResponder:
    def __init__(self, 
                 model_name: str = "llama3:8b",
                 collection_name: str = "documents",
                 keyword_prompt_path: str = "./prompts/keyword_extractor.md",
                 context_prompt_path: str = "./prompts/context_based_query.md",
                 service_type: Literal["ollama", "openai"] = "ollama"):
        """
        Initialize the ContextualResponder.
        
        Args:
            model_name (str): Name of the model to use. Defaults to "llama3:8b" for Ollama or "gpt-3.5-turbo" for OpenAI.
            collection_name (str): Name of the Qdrant collection to search in. Defaults to "documents".
            keyword_prompt_path (str): Path to the keyword extraction prompt. Defaults to "./prompts/keyword_extractor.md".
            context_prompt_path (str): Path to the context-based query prompt. Defaults to "./prompts/context_based_query.md".
            service_type (str): Type of chat service to use ("ollama" or "openai"). Defaults to "ollama".
        """
        self.model_name = model_name
        self.collection_name = collection_name
        self.keyword_prompt_path = keyword_prompt_path
        self.context_prompt_path = context_prompt_path
        self.service_type = service_type
        
        # Initialize components
        self.chunk_finder = ChunkFinder(collection_name=collection_name)
        
        # Initialize the appropriate chat service
        if service_type == "openai":
            # Check if OpenAI API key is set
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY environment variable is not set. OpenAI service may not work properly.")
            
            # Use default OpenAI model if none specified
            if model_name == "llama3:8b":  # If still using the Ollama default
                self.model_name = "gpt-3.5-turbo"
                
            self.chat_service = OpenAIChatService()
            logger.info(f"Using OpenAI chat service with model: {self.model_name}")
        else:  # ollama
            self.chat_service = ChatService()
            logger.info(f"Using Ollama chat service with model: {self.model_name}")
        
        # Load the prompts
        self._load_keyword_prompt()
        self._load_context_prompt()
        
        logger.info("ContextualResponder initialized")
    
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
    
    def _load_context_prompt(self):
        """
        Load the context-based query prompt from file.
        """
        try:
            with open(self.context_prompt_path, 'r', encoding='utf-8') as f:
                self.context_prompt_template = f.read()
            logger.info(f"Loaded context-based query prompt from {self.context_prompt_path}")
        except Exception as e:
            logger.error(f"Error loading context prompt: {str(e)}")
            # Fallback to a simple prompt if the file can't be loaded
            self.context_prompt_template = """Answer the following question based on the provided context:\n\nContext: {{CONTEXT}}\n\nQuestion: {{USER_QUERY}}\n\nAnswer:"""
    
    def get_response(self, query: str, num_chunks: int = 10, display_context: bool = False) -> Union[str, Tuple[str, str]]:
        """
        Get a contextual response to the user query.
        
        
        Args:
            query (str): The user's query
            num_chunks (int): Number of document chunks to retrieve. Defaults to 3.
            display_context (bool): Whether to display the full prompt with context. Defaults to False.
            
        Returns:
            Union[str, Tuple[str, str]]: The contextual response, or a tuple of (response, full_prompt) if display_context is True
        """
        logger.info(f"Processing query: {query}")
        
        # Step 1: Extract keywords from the query using the sync version
        keywords_str = self.chat_service.chat_sync(
            model=self.model_name,
            user_prompt=self.keyword_prompt_template.replace("{{USER_QUERY}}", query)
        )
        
        # Extract keywords from the response using regex
        keywords_match = re.search(r'<keywords>(.*?)</keywords>', keywords_str, re.DOTALL)
        
        if keywords_match:
            # Extract the keywords and split by comma
            keywords_str = keywords_match.group(1).strip()
            keywords = [kw.strip() for kw in keywords_str.split(',')]
        else:
            # If no keywords tag found, just split by comma (fallback)
            keywords = [kw.strip() for kw in keywords_str.split(',')]
            
        logger.info(f"Extracted keywords: {keywords}")
        
        # Step 2: Find relevant document chunks using the keywords
        chunks = self.chunk_finder.find_chunks(keywords, num_chunks=num_chunks)
        
        if not chunks:
            logger.warning("No relevant document chunks found")
            # Fallback to direct query if no chunks found
            return self._get_direct_response(query, display_context)
        
        # Step 3: Build the context from the chunks
        context = self._build_context_from_chunks(chunks)
        logger.info(f"Built context with {len(chunks)} chunks")
        
        # Step 4: Generate a response using the context and query
        return self._get_contextual_response(query, context, display_context)
    
    def _build_context_from_chunks(self, chunks) -> str:
        """
        Build a context string from document chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            str: The context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            # Add the chunk content with a separator
            context_parts.append(f"Document {i+1}:\n{chunk.page_content}\n")
        
        return "\n".join(context_parts)
    
    def _get_contextual_response(self, query: str, context: str, display_context: bool = False) -> Union[str, Tuple[str, str]]:
        """
        Get a response based on the context and query.
        
        Args:
            query (str): The user's query
            context (str): The context information
            display_context (bool): Whether to display the full prompt with context
            
        Returns:
            Union[str, Tuple[str, str]]: The contextual response, or a tuple of (response, full_prompt) if display_context is True
        """
        # Replace the placeholders in the prompt template
        prompt = self.context_prompt_template\
            .replace("{{CONTEXT}}", context)\
            .replace("{{USER_QUERY}}", query)
        
        # Log the full prompt being sent to the LLM
        logger.info(f"Sending prompt to LLM:\n{'-' * 40}\n{prompt}\n{'-' * 40}")
        
        # Get response from the LLM using chat_sync
        response = self.chat_service.chat_sync(
            model=self.model_name,
            user_prompt=prompt,
            system_message=None,
            temperature=0.7
        )
        
        # Try different patterns to extract the answer from the response
        answer = None
        
        # Try <answer> tags first
        answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
        if answer_match:
            answer = answer_match.group(1).strip()
        
        # If no match, try to find content after 'Answer:' or similar patterns
        if not answer:
            answer_match = re.search(r'(?:Answer|Response):\s*(.*)', response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
        
        if answer:
            logger.info("Generated contextual response")
            return (answer, prompt) if display_context else answer
        else:
            # If no answer pattern found, return the whole response
            logger.warning(f"Could not extract answer from response, using full response. Response preview: {response[:100]}...")
            return (response, prompt) if display_context else response
    
    def _get_direct_response(self, query: str, display_context: bool = False) -> Union[str, Tuple[str, str]]:
        """
        Get a direct response to the query without context.
        
        Args:
            query (str): The user's query
            display_context (bool): Whether to display the full prompt
            
        Returns:
            Union[str, Tuple[str, str]]: The direct response, or a tuple of (response, prompt) if display_context is True
        """
        logger.info("Generating direct response without context")
        
        # Create a system message
        system_message = "You are a helpful AI assistant. Answer the user's question to the best of your ability."
        
        # Get response from the LLM using chat_sync
        response = self.chat_service.chat_sync(
            model=self.model_name,
            user_prompt=query,
            system_message=system_message,
            temperature=0.7
        )
        
        if display_context:
            prompt = f"System: {system_message}\n\nUser: {query}"
            return response, prompt
        else:
            return response


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Get a contextual response to a query')
    parser.add_argument('--query', type=str, required=True, help='Query to get a response for')
    parser.add_argument('--collection', type=str, default="documents", help='Qdrant collection name')
    parser.add_argument('--num-chunks', type=int, default=10, help='Number of document chunks to retrieve')
    parser.add_argument('--display-context', action='store_true', help='Display the full prompt with context')
    parser.add_argument('--service', type=str, choices=['ollama', 'openai'], default='ollama', help='Chat service to use')
    parser.add_argument('--model', type=str, help='Model to use (defaults depend on service)')
    args = parser.parse_args()
    
    # Create contextual responder with the specified service
    responder = ContextualResponder(
        model_name=args.model if args.model else ("llama3:8b" if args.service == "ollama" else "gpt-3.5-turbo"),
        collection_name=args.collection,
        service_type=args.service
    )
    
    # Get a response to the query
    result = responder.get_response(args.query, num_chunks=args.num_chunks, display_context=args.display_context)
    
    # Handle the result based on whether display_context is True
    if args.display_context:
        # If display_context is True, result should be a tuple of (response, full_prompt)
        response, full_prompt = result
        print(f"\nQuery: {args.query}")
        print(f"\nFull Prompt:\n{'-' * 80}\n{full_prompt}\n{'-' * 80}")
        print(f"\nResponse:\n{response}")
    else:
        # If display_context is False, result should be just the response
        print(f"\nQuery: {args.query}")
        print(f"\nResponse:\n{result}")
import os
import logging
import json
from typing import Optional, Iterator, Dict, Any
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OpenAIChatService')

class OpenAIChatService:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAIChatService with the OpenAI API key.
        
        Args:
            api_key (Optional[str]): OpenAI API key. If None, it will be loaded from environment variables.
        """
        # Use provided API key or load from environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info("OpenAIChatService initialized")
    
    def chat(self, 
             model: str = "gpt-3.5-turbo", 
             user_prompt: str = "", 
             system_message: Optional[str] = None,
             temperature: float = 0.7,
             stream: bool = True) -> Iterator[str]:
        """
        Send a chat request to the OpenAI service and stream the response.
        
        Args:
            model (str): The name of the model to use (e.g., "gpt-3.5-turbo")
            user_prompt (str): The user's prompt/question
            system_message (Optional[str]): Optional system message to set context
            temperature (float): Controls randomness of output. Defaults to 0.7.
            stream (bool): Whether to stream the response. Defaults to True.
            
        Yields:
            Iterator[str]: Streamed response chunks from the model
        """
        if not self.api_key:
            logger.error("Cannot make API call: No OpenAI API key provided")
            yield "Error: No OpenAI API key provided"
            return
        
        # Prepare the messages
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add user message
        messages.append({"role": "user", "content": user_prompt})
        
        logger.info(f"Sending chat request to OpenAI model: {model}")
        logger.debug(f"Request messages: {json.dumps(messages)}")
        
        try:
            # Send the request with streaming enabled if requested
            if stream:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=True
                )
                
                # Process the streamed response
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
            else:
                # Non-streaming response
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=False
                )
                
                if response.choices and len(response.choices) > 0:
                    yield response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            yield f"Error: {str(e)}"

    def chat_sync(self, 
                 model: str = "gpt-3.5-turbo", 
                 user_prompt: str = "", 
                 system_message: Optional[str] = None,
                 temperature: float = 0.7) -> str:
        """
        Send a chat request to the OpenAI service and return the complete response.
        
        Args:
            model (str): The name of the model to use (e.g., "gpt-3.5-turbo")
            user_prompt (str): The user's prompt/question
            system_message (Optional[str]): Optional system message to set context
            temperature (float): Controls randomness of output. Defaults to 0.7.
            
        Returns:
            str: The complete response from the model
        """
        if not self.api_key:
            logger.error("Cannot make API call: No OpenAI API key provided")
            return "Error: No OpenAI API key provided"
        
        # Prepare the messages
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add user message
        messages.append({"role": "user", "content": user_prompt})
        
        logger.info(f"Sending chat request to OpenAI model: {model}")
        
        try:
            # Send the request without streaming
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                return ""
        
        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            return f"Error: {str(e)}"


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Send a chat request to OpenAI')
    parser.add_argument('--prompt', type=str, required=True, help='User prompt to send')
    parser.add_argument('--model', type=str, default="gpt-3.5-turbo", help='OpenAI model to use')
    parser.add_argument('--system', type=str, help='Optional system message')
    parser.add_argument('--temperature', type=float, default=0.7, help='Temperature for response generation')
    parser.add_argument('--stream', action='store_true', help='Stream the response')
    args = parser.parse_args()
    
    # Create chat service instance
    chat_service = OpenAIChatService()
    
    if args.stream:
        # Example with streaming
        print("\nStreaming response:\n")
        for chunk in chat_service.chat(
            model=args.model,
            user_prompt=args.prompt,
            system_message=args.system,
            temperature=args.temperature,
            stream=True
        ):
            print(chunk, end='', flush=True)
        print("\n")
    else:
        # Example with synchronous response
        print("\nSynchronous response:\n")
        response = chat_service.chat_sync(
            model=args.model,
            user_prompt=args.prompt,
            system_message=args.system,
            temperature=args.temperature
        )
        print(response)

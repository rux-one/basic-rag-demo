import requests
import logging
import json
from typing import Optional, Iterator, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChatService')

class ChatService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the ChatService with the Ollama API URL.
        
        Args:
            base_url (str): Base URL for the Ollama API. Defaults to "http://localhost:11434".
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        logger.info(f"ChatService initialized with API URL: {self.api_url}")
    
    def chat(self, 
             model: str, 
             user_prompt: str, 
             system_message: Optional[str] = None,
             temperature: float = 0.7,
             stream: bool = True) -> Iterator[str]:
        """
        Send a chat request to the Ollama service and stream the response.
        
        Args:
            model (str): The name of the model to use (e.g., "llama2")
            user_prompt (str): The user's prompt/question
            system_message (Optional[str]): Optional system message to set context
            temperature (float): Controls randomness of output. Defaults to 0.7.
            stream (bool): Whether to stream the response. Defaults to True.
            
        Yields:
            Iterator[str]: Streamed response chunks from the model
        """
        # Prepare the request payload
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "stream": stream,
            "temperature": temperature
        }
        
        # Add system message if provided
        if system_message:
            payload["messages"].insert(0, {"role": "system", "content": system_message})
        
        logger.info(f"Sending chat request to model: {model}")
        logger.debug(f"Request payload: {json.dumps(payload)}")
        
        try:
            # Send the request with streaming enabled
            with requests.post(self.api_url, json=payload, stream=True) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Process the streamed response
                for line in response.iter_lines():
                    if line:
                        # Decode the line and parse JSON
                        data = json.loads(line.decode('utf-8'))
                        
                        # Extract the message content from the response
                        if 'message' in data and 'content' in data['message']:
                            content = data['message']['content']
                            yield content
                        
                        # Check if this is the final message
                        if data.get('done', False):
                            logger.info("Chat response completed")
                            break
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama API: {str(e)}")
            yield f"Error: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {str(e)}")
            yield f"Error decoding response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            yield f"Unexpected error: {str(e)}"

    def chat_sync(self, 
                 model: str, 
                 user_prompt: str, 
                 system_message: Optional[str] = None,
                 temperature: float = 0.7) -> str:
        """
        Send a chat request to the Ollama service and return the complete response.
        
        Args:
            model (str): The name of the model to use (e.g., "llama2")
            user_prompt (str): The user's prompt/question
            system_message (Optional[str]): Optional system message to set context
            temperature (float): Controls randomness of output. Defaults to 0.7.
            
        Returns:
            str: The complete response from the model
        """
        # Collect all streamed chunks into a single response
        response_chunks = list(self.chat(
            model=model,
            user_prompt=user_prompt,
            system_message=system_message,
            temperature=temperature,
            stream=True
        ))
        
        # Join all chunks into a single string
        return ''.join(response_chunks)


# Example usage
if __name__ == "__main__":
    # Create a chat service instance
    chat_service = ChatService()
    
    # Example with streaming
    print("\nStreaming response:\n")
    for chunk in chat_service.chat(
        model="llama3:8b",
        user_prompt="What is the meaning of life?",
        system_message="You are a helpful AI assistant that provides the most accurate response."
    ):
        print(chunk, end='', flush=True)
    
    print("\n\nSynchronous response:\n")
    # Example with synchronous response
    response = chat_service.chat_sync(
        model="llama3:8b",
        user_prompt="What is the meaning of life?",
        system_message="You are a helpful AI assistant that provides the most accurate response."
    )
    print(response)

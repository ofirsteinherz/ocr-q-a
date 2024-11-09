import requests
import base64
import json
from typing import List, Union, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class GPTResponseError(Exception):
    """Custom exception for GPT API response errors"""
    pass

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    role: MessageRole
    content: Union[str, List[Dict]]

class GPTClient:
    def __init__(
        self,
        api_key: str,
        endpoint: str
    ):
        """Initialize GPT client with API key and endpoint"""
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }

    def _encode_image(self, image_source: Union[str, Path]) -> str:
        """Encode image from either URL or local path to base64"""
        try:
            if str(image_source).startswith(('http://', 'https://')):
                response = requests.get(image_source, timeout=10)
                response.raise_for_status()
                image_content = response.content
            else:
                with open(image_source, 'rb') as image_file:
                    image_content = image_file.read()
            
            return base64.b64encode(image_content).decode('utf-8')
        except requests.RequestException as e:
            raise GPTResponseError(f"Failed to fetch image from URL: {e}")
        except IOError as e:
            raise GPTResponseError(f"Failed to read local image file: {e}")
        except Exception as e:
            raise GPTResponseError(f"Unexpected error processing image: {e}")

    def _handle_api_response(self, response: requests.Response) -> Dict:
        """Handle API response and common error cases"""
        try:
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise GPTResponseError(f"API Error: {result['error'].get('message', 'Unknown error')}")
            
            if 'choices' not in result or not result['choices']:
                raise GPTResponseError("No completion choices returned")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', str(e))
            except json.JSONDecodeError:
                error_msg = response.text
            
            if response.status_code == 401:
                raise GPTResponseError("Authentication error: Invalid API key")
            elif response.status_code == 429:
                raise GPTResponseError("Rate limit exceeded")
            elif response.status_code >= 500:
                raise GPTResponseError("OpenAI server error")
            else:
                raise GPTResponseError(f"HTTP error occurred: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            raise GPTResponseError("Connection error: Failed to connect to the API")
        except requests.exceptions.Timeout:
            raise GPTResponseError("Request timed out")
        except json.JSONDecodeError:
            raise GPTResponseError("Failed to parse API response")
        except Exception as e:
            raise GPTResponseError(f"Unexpected error: {str(e)}")

    def analyze_image(
        self,
        image_source: Union[str, Path],
        prompt: str,
        system_prompt: Optional[str] = None,
        json_response: bool = False
    ) -> str:
        """Analyze a single image with an optional system prompt"""
        messages = []
        
        if system_prompt:
            messages.append(Message(
                role=MessageRole.SYSTEM,
                content=system_prompt
            ))

        try:
            encoded_image = self._encode_image(image_source)
            image_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded_image}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            messages.append(Message(
                role=MessageRole.USER,
                content=image_content
            ))
            
            return self._send_request(messages, json_response)
            
        except Exception as e:
            raise GPTResponseError(f"Failed to analyze image: {str(e)}")

    def chat(self, messages: List[Message], json_response: bool = False) -> str:
        """Have a text-only conversation with multiple messages"""
        try:
            return self._send_request(messages, json_response)
        except Exception as e:
            raise GPTResponseError(f"Chat error: {str(e)}")

    def _send_request(self, messages: List[Message], json_response: bool = False) -> str:
        """Send request to GPT API"""
        payload = {
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content
                } for msg in messages
            ],
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 4096
        }

        if json_response:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(
                self.endpoint, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            
            result = self._handle_api_response(response)
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            raise GPTResponseError(f"Request failed: {str(e)}")
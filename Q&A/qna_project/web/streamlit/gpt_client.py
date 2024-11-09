import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class GPTClient:
    def __init__(self, api_key: str, endpoint: str, tools: Dict[str, Dict[str, Any]]):
        self.api_key = api_key
        self.endpoint = endpoint
        self.tools = tools
        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }

    def _format_messages(self, messages: List[Message]) -> List[Dict]:
        formatted_messages = []
        
        for msg in messages:
            message_dict = {
                "role": msg.role.value
            }
            
            if msg.content is not None:
                message_dict["content"] = msg.content
            
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                message_dict["name"] = msg.name
            
            formatted_messages.append(message_dict)
        
        return formatted_messages

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in registered tools")
            
        # Import tools dynamically
        from tools import update_user_data, get_healthcare_services
        
        # Map tool names to functions
        tool_functions = {
            'update_user_data': update_user_data,
            'get_healthcare_services': get_healthcare_services
        }
        
        if tool_name not in tool_functions:
            raise ValueError(f"Tool function {tool_name} not implemented")
            
        # Execute the tool function with the provided arguments
        return tool_functions[tool_name](**arguments)

    def _validate_tool_response(self, response: str) -> bool:
        """Basic validation of tool response"""
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False

    def chat(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Send a chat request with optional tool calls
        """
        payload = {
            "messages": self._format_messages(messages),
            "tools": list(self.tools.values()),
            "tool_choice": "auto",
            "temperature": 0.7,
            "max_tokens": 800
        }

        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json=payload
        )
        
        # Parse and check the response
        try:
            result = response.json()
            if 'choices' not in result:
                raise ValueError("API response missing 'choices' field. Full response: " + json.dumps(result, indent=2))

            message = result['choices'][0]['message']
        
            # Process tool calls if present
            if 'tool_calls' in message:
                tool_results = []
                for tool_call in message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    try:
                        args = json.loads(tool_call['function']['arguments'])
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid arguments for tool {tool_name}")
                        
                    tool_response = self._execute_tool(tool_name, args)
                    
                    if not self._validate_tool_response(tool_response):
                        raise ValueError(f"Invalid response from tool {tool_name}")
                        
                    tool_results.append({
                        'tool_call_id': tool_call['id'],
                        'response': tool_response
                    })
                
                return {
                    'content': message.get('content'),
                    'tool_calls': message['tool_calls'],
                    'tool_results': tool_results
                }
            
            return {'content': message.get('content')}

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return {"content": "Error: Request failed"}
        
        except ValueError as e:
            print(e)
            return {"content": str(e)}
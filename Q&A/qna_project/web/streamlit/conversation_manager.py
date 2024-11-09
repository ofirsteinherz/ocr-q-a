from typing import List, Dict, Any, Optional
import json
from enum import Enum
from gpt_client import GPTClient

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message:
    def __init__(self, role: MessageRole, content: Optional[str], tool_calls=None, tool_call_id=None, name=None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
        self.name = name

class ConversationManager:
    def __init__(self, client: GPTClient):
        self.client = client
        self.history: List[Message] = []
        self.user_data_complete = False
        self.collection_phase = True
        self.confirmed = False

    def add_message(self, message: Message):
        self.history.append(message)

    def process_response(self, response: Dict[str, Any]) -> str:
        """Process the response from the GPT client"""
        try:
            # Handle simple text response
            if 'content' in response and response['content']:
                self.add_message(Message(
                    role=MessageRole.ASSISTANT,
                    content=response['content']
                ))
                return response['content']

            # Handle tool calls
            if 'tool_calls' in response:
                # Add assistant's message with tool calls
                self.add_message(Message(
                    role=MessageRole.ASSISTANT,
                    content=response.get('content'),
                    tool_calls=response['tool_calls']
                ))

                # Process tool results
                tool_responses = []
                for result in response.get('tool_results', []):
                    try:
                        tool_content = json.loads(result['response'])
                        
                        # Format tool response based on the type
                        if 'current_data' in tool_content:
                            # Handle user data updates
                            formatted_data = self._format_user_data(tool_content['current_data'])
                            tool_responses.append(formatted_data)
                        elif 'services' in tool_content:
                            # Handle healthcare services data
                            formatted_services = self._format_services_data(tool_content)
                            tool_responses.append(formatted_services)
                        
                        # Add tool response to history
                        self.add_message(Message(
                            role=MessageRole.TOOL,
                            content=json.dumps(tool_content),
                            tool_call_id=result['tool_call_id'],
                            name=result['tool_call_id']
                        ))
                    except json.JSONDecodeError:
                        continue

                # Get follow-up response from GPT
                follow_up_response = self.client.chat(self.history)
                if follow_up_response and 'content' in follow_up_response:
                    self.add_message(Message(
                        role=MessageRole.ASSISTANT,
                        content=follow_up_response['content']
                    ))
                    return follow_up_response['content']

                # If no follow-up response, return formatted tool responses
                if tool_responses:
                    return "\n\n".join(tool_responses)

            return "I apologize, but I couldn't process that properly. Please try again."
            
        except Exception as e:
            print(f"Error in process_response: {str(e)}")
            return "I encountered an error processing the response. Please try again."

    def _format_user_data(self, user_data: Dict[str, str]) -> str:
        """Format user data for display"""
        formatted_fields = [
            f"• {key.replace('_', ' ').title()}: {value}"
            for key, value in user_data.items()
        ]
        return "Current Information:\n" + "\n".join(formatted_fields)

    def _format_services_data(self, services_data: Dict[str, Any]) -> str:
        """Format services data for display"""
        try:
            if services_data.get('status') != 'success':
                return f"Error: {services_data.get('message', 'Unknown error')}"

            services = services_data.get('services', {})
            formatted_text = f"Healthcare Services for {services_data['hmo'].title()} {services_data['plan'].title()} Plan:\n\n"

            for service_type, details in services.items():
                formatted_text += f"{details['general_info']['title']}:\n"
                for service in details['services']:
                    formatted_text += f"• {service['name']}: {service['details']}\n"
                formatted_text += "\n"

            return formatted_text
        except Exception as e:
            print(f"Error formatting services: {str(e)}")
            return "Error formatting services information"

    def prompt_for_user_information(self) -> str:
        """Initialize the conversation with a structured prompt"""
        initial_prompt = """I'll help you collect your healthcare information. I need:
- First and last name
- ID number (9 digits)
- Gender
- Age
- HMO name (Maccabi/Meuhedet/Clalit)
- HMO number (9 digits)
- Insurance plan (Gold/Silver/Bronze)

Please provide your information and I'll help collect it all. Let's start - what is your first and last name?"""
        
        system_message = Message(
            role=MessageRole.SYSTEM,
            content="""You are a healthcare information collection assistant. Collect all required user information in a conversational way. Use the update_user_data function to store the information as you receive it. After collecting all required fields, show a summary and ask for confirmation."""
        )
        
        self.add_message(system_message)
        self.add_message(Message(role=MessageRole.ASSISTANT, content=initial_prompt))
        return initial_prompt

    def send_message(self, content: str) -> str:
        try:
            # Add user message to history
            self.add_message(Message(role=MessageRole.USER, content=content))
            
            # Handle confirmation and transition
            if self.user_data_complete and content.lower() in ['yes', 'confirm', 'ok']:
                if not self.confirmed:
                    self.confirmed = True
                    return self.transition_to_qa()
            
            # Get response from GPT
            response = self.client.chat(self.history)
            if not response:
                return "I apologize, but I encountered an error. Please try again."

            result = self.process_response(response)
            
            # Check if all information is collected
            if isinstance(result, str) and "summary" in result.lower() and "correct" in result.lower():
                self.user_data_complete = True
            
            return result

        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

    def transition_to_qa(self) -> str:
        """Transition to Q&A phase with new system message"""
        self.collection_phase = False
        
        system_message = Message(
            role=MessageRole.SYSTEM,
            content="""You are now a healthcare services assistant. Use the stored user information to:
1. Answer questions about available services using the get_healthcare_services function
2. Handle information updates using the update_user_data function when needed
3. Provide personalized responses based on the user's HMO and plan

When users ask about services:
- Call get_healthcare_services with their HMO and plan
- Explain the benefits in a clear way
- Mention any service limitations for their plan

If users want to update their information:
- Use update_user_data to modify their details
- Confirm the changes and continue with accurate information"""
        )
        
        transition_message = Message(
            role=MessageRole.ASSISTANT,
            content="""Perfect! I'm now ready to help you with questions about your healthcare services. 
You can:
- Ask about specific services or coverage
- Update your information if needed
- Learn about your benefits

What would you like to know about?"""
        )
        
        self.add_message(system_message)
        self.add_message(transition_message)
        return transition_message.content
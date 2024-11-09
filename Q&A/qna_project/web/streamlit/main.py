import os
import streamlit as st
from dotenv import load_dotenv
import json
from conversation_manager import ConversationManager
from gpt_client import GPTClient
from tools import get_registry
from chat_manager import ChatManager
from typing import Optional

def load_config() -> dict:
    """Load configuration from .env file"""
    load_dotenv()
    
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {
        'AZURE_OPENAI_API_KEY': os.getenv('AZURE_OPENAI_API_KEY'),
        'AZURE_OPENAI_ENDPOINT': os.getenv('AZURE_OPENAI_ENDPOINT')
    }

class HealthcareAssistant:
    def __init__(self):
        try:
            self.config = load_config()
            self.tools_registry = get_registry()
            
            # Initialize GPT client
            self.client = GPTClient(
                api_key=self.config['AZURE_OPENAI_API_KEY'],
                endpoint=self.config['AZURE_OPENAI_ENDPOINT'],
                tools=self.tools_registry
            )
            
            # Initialize conversation manager
            self.conversation = ConversationManager(self.client)
            
            # Initialize chat manager
            self.chat_manager = ChatManager("Healthcare Assistant")
            
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            raise

    def handle_response(self, user_input: str) -> Optional[str]:
        """Handle user input and get response from conversation manager"""
        try:
            if not user_input:
                return None
                
            response = self.conversation.send_message(user_input)
            return response
            
        except Exception as e:
            st.error(f"Error processing response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

def main():
    st.set_page_config(
        page_title="Healthcare Assistant",
        page_icon="🏥",
        layout="wide"
    )

    # Display title only once
    st.title("Healthcare Information Assistant")
    
    try:
        # Initialize session state
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
            
        # Initialize assistant only once
        if 'assistant' not in st.session_state:
            st.session_state.assistant = HealthcareAssistant()
            
            # Add initial message only once
            initial_message = st.session_state.assistant.conversation.prompt_for_user_information()
            st.session_state.assistant.chat_manager.add_message("assistant", initial_message, display=False)
            st.session_state.initialized = True
        
        # Add clear chat button
        if st.sidebar.button("Clear Chat"):
            st.session_state.assistant.chat_manager.clear_chat_history()
            # Re-initialize with initial message
            initial_message = st.session_state.assistant.conversation.prompt_for_user_information()
            st.session_state.assistant.chat_manager.add_message("assistant", initial_message, display=False)
            st.rerun()
        
        # Display chat history once
        st.session_state.assistant.chat_manager.display_chat_history()
        
        # Handle user input
        st.session_state.assistant.chat_manager.handle_user_input(
            callback_fn=st.session_state.assistant.handle_response
        )
        
    except ValueError as e:
        st.error(f"Configuration error: {str(e)}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
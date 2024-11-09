import streamlit as st
from datetime import datetime
import re
import os
from pathlib import Path
import sys
import json
import logging

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from qna_project.config.settings import settings
from qna_project.clients.gpt_client import GPTClient, Message, MessageRole

class UserInfoBot:
    def __init__(self, translations):
        self.translations = translations
        self.client = GPTClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.prompt_template = """
        You are an assistant helping gather user information for a medical system.
        You need to collect the following information one at a time:
        - First and last name
        - ID number (must be 9 digits)
        - Gender (Male/Female/Other)
        - Age (between 0 and 120)
        - HMO card number (must be 9 digits)
        - HMO name (must be one of: Maccabi, Meuchedet, Clalit)
        - Insurance membership plan (must be one of: Gold, Silver, Bronze)

        For each piece of information:
        1. Ask for only one piece of information at a time
        2. Validate the response based on the rules
        3. If invalid, explain why and ask again
        4. If valid, confirm and move to next piece of information
        5. Keep track of what information has been collected
        
        Current collected information: {collected_info}
        Next required information: {next_required}
        """
        self.initialize_state()
        self.setup_logging()
        
    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = settings.OUTPUT_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a file handler
        log_file = log_dir / f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        self.logger.addHandler(file_handler)
        
    def initialize_state(self):
        # Clear session state on page load/refresh
        if 'page_loaded' not in st.session_state:
            st.session_state.clear()
            st.session_state.page_loaded = True
            self.logger.info("New session started")
            
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            
        if 'conversation_state' not in st.session_state:
            st.session_state.conversation_state = {
                'user_info': {},
                'current_field': 'first_name'
            }

    def save_conversation_to_file(self):
        if 'session_id' in st.session_state:
            # Save chat history
            chat_file = settings.OUTPUT_DIR / f"chat_history_{st.session_state.session_id}.json"
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'messages': st.session_state.messages,
                    'user_info': st.session_state.conversation_state['user_info'],
                    'timestamp': datetime.now().isoformat(),
                    'session_id': st.session_state.session_id
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Conversation saved to {chat_file}")

    def validate_response(self, field: str, value: str) -> tuple[bool, str]:
        validations = {
            'id_number': lambda x: bool(re.match(r'^\d{9}$', x)),
            'hmo_number': lambda x: bool(re.match(r'^\d{9}$', x)),
            'age': lambda x: x.isdigit() and 0 <= int(x) <= 120,
            'hmo_name': lambda x: x.lower() in ['maccabi', 'meuchedet', 'clalit'],
            'insurance_plan': lambda x: x.lower() in ['gold', 'silver', 'bronze'],
            'gender': lambda x: x.lower() in ['male', 'female', 'other']
        }
        
        if field in validations:
            is_valid = validations[field](value)
            message = "" if is_valid else f"Invalid {field}. Please try again."
            if not is_valid:
                self.logger.warning(f"Invalid {field} value provided: {value}")
            return is_valid, message
        return True, ""

    def get_gpt_response(self, user_input: str = None) -> str:
        collected_info = "\n".join([f"{k}: {v}" for k, v in st.session_state.conversation_state['user_info'].items()])
        next_required = st.session_state.conversation_state['current_field']
        
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=self.prompt_template.format(
                    collected_info=collected_info or "None",
                    next_required=next_required
                )
            )
        ]
        
        # Add conversation history
        for msg in st.session_state.messages:
            role = MessageRole.ASSISTANT if msg["role"] == "assistant" else MessageRole.USER
            messages.append(Message(role=role, content=msg["content"]))
            
        if user_input:
            messages.append(Message(role=MessageRole.USER, content=user_input))
        
        try:
            response = self.client.chat(messages)
            self.logger.info(f"GPT response received for input: {user_input}")
            return response
        except Exception as e:
            self.logger.error(f"Error getting GPT response: {str(e)}")
            raise

    def process_user_input(self, user_input: str):
        current_field = st.session_state.conversation_state['current_field']
        is_valid, error_message = self.validate_response(current_field, user_input)
        
        if is_valid:
            st.session_state.conversation_state['user_info'][current_field] = user_input
            self.logger.info(f"Field {current_field} updated with value: {user_input}")
            
            # Define the order of fields
            field_order = [
                'first_name', 'last_name', 'id_number', 'gender', 
                'age', 'hmo_number', 'hmo_name', 'insurance_plan'
            ]
            
            # Move to next field
            current_index = field_order.index(current_field)
            if current_index < len(field_order) - 1:
                st.session_state.conversation_state['current_field'] = field_order[current_index + 1]
                self.logger.info(f"Moving to next field: {field_order[current_index + 1]}")
            else:
                # All fields collected
                self.logger.info("All user information collected successfully")
                return True
                
        return False

    def render_chat(self):
        st.header(self.translations['stage1_title'])

        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("Type your response..."):
            self.logger.info(f"User input received: {prompt}")
            
            # Display user message in chat
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Process user input
            try:
                all_done = self.process_user_input(prompt)
                if all_done:
                    self.logger.info("Processing complete, moving to next stage")
                    st.session_state.user_info = st.session_state.conversation_state['user_info']
                    st.session_state.stage = 2
                    return True

                # Get GPT response
                response = self.get_gpt_response(prompt)
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response})

                # Save conversation
                self.save_conversation_to_file()
                
            except Exception as e:
                self.logger.error(f"Error during chat processing: {str(e)}")
                st.error("An error occurred while processing your message. Please try again.")
        
        # Start conversation if no messages
        if not st.session_state.messages:
            self.logger.info("Starting new conversation")
            try:
                initial_response = self.get_gpt_response()
                with st.chat_message("assistant"):
                    st.markdown(initial_response)
                st.session_state.messages.append({"role": "assistant", "content": initial_response})
                self.save_conversation_to_file()
            except Exception as e:
                self.logger.error(f"Error starting conversation: {str(e)}")
                st.error("An error occurred while starting the conversation. Please refresh the page.")
            
        return False

def render_user_info_form(translations):
    bot = UserInfoBot(translations)
    return bot.render_chat()
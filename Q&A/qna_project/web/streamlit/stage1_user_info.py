import streamlit as st
from datetime import datetime
import re
import os
from pathlib import Path
import sys
import json
import logging
from typing import Dict, Set

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from qna_project.config.settings import settings
from qna_project.clients.gpt_client import GPTClient, Message, MessageRole

class UserDataModel:
    """Data model for user information"""
    def __init__(self):
        self.data = {
            'first_name': '',
            'last_name': '',
            'id_number': '',
            'gender': '',
            'age': '',
            'hmo_number': '',
            'hmo_name': '',
            'insurance_plan': ''
        }
        self.completed_fields: Set[str] = set()

    def update_field(self, field: str, value: str) -> None:
        """Update a field and mark it as completed"""
        if field == 'first_name':
            names = value.split(' ', 1)
            self.data['first_name'] = names[0]
            if len(names) > 1:
                self.data['last_name'] = names[1]
                self.completed_fields.add('last_name')
            self.completed_fields.add('first_name')
        else:
            self.data[field] = value
            self.completed_fields.add(field)

    def to_dict(self) -> Dict:
        return {
            'data': self.data,
            'completed_fields': list(self.completed_fields)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserDataModel':
        instance = cls()
        instance.data = data.get('data', {})
        instance.completed_fields = set(data.get('completed_fields', []))
        return instance

class UserInfoBot:
    def __init__(self, translations):
        self.translations = translations
        self.setup_logging()
        
        self.client = GPTClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Define the required fields and their order
        self.required_fields = [
            'first_name', 'last_name', 'id_number', 'gender', 
            'age', 'hmo_number', 'hmo_name', 'insurance_plan'
        ]
        
        self.prompt_template = """
        You are an assistant helping gather user information for a medical system.
        Please respond in {language}.
        
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
        
        Current collected information: 
        {collected_info}
        
        Next required field: {next_required}
        Missing fields: {missing_fields}
        
        Additional language-specific instructions:
        - If language is 'he': Use Hebrew and maintain Right-to-Left (RTL) text direction
        - If language is 'en': Use English and maintain Left-to-Right (LTR) text direction

        After you done getting all fields from the user, return a json wraped with '''json [add here] '''
        """
        self.initialize_state()

    def setup_logging(self):
        """Initialize logging configuration for the bot"""
        log_dir = settings.LOGS_DIR / "site_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"UserInfoBot_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            log_file = log_dir / f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
        
        self.logger.info("Logging initialized")

    def save_conversation_to_file(self):
        """Save current conversation state to a JSON file"""
        if 'session_id' in st.session_state:
            chat_file = settings.OUTPUT_DIR / f"chat_history_{st.session_state.session_id}.json"
            conversation_data = {
                'messages': st.session_state.messages,
                'user_info': st.session_state.conversation_state['user_info'],
                'completed_fields': list(st.session_state.conversation_state['completed_fields']),
                'timestamp': datetime.now().isoformat(),
                'session_id': st.session_state.session_id
            }
            
            chat_file.parent.mkdir(parents=True, exist_ok=True)
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Conversation saved to {chat_file}")

    def initialize_state(self):
        """Initialize or restore session state"""
        if 'page_loaded' not in st.session_state:
            st.session_state.page_loaded = True
            st.session_state.session_id = str(datetime.now().strftime('%Y%m%d_%H%M%S'))
            self.logger.info(f"New session started: {st.session_state.session_id}")
            
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            
        if 'conversation_state' not in st.session_state:
            st.session_state.conversation_state = {
                'user_info': {},
                'current_field': self.required_fields[0],
                'completed_fields': set()
            }
            
        if 'previous_language' not in st.session_state:
            st.session_state.previous_language = st.session_state.language

    def get_missing_fields(self):
        """Return list of fields that haven't been completed yet"""
        completed = set(st.session_state.conversation_state['completed_fields'])
        return [field for field in self.required_fields if field not in completed]

    def get_gpt_response(self, user_input: str = None) -> str:
        """Get response from GPT based on current conversation state"""
        current_language = st.session_state.language.lower()
        
        if st.session_state.previous_language != st.session_state.language:
            self.logger.info(f"Language changed to {current_language}, resetting conversation")
            st.session_state.messages = []
            st.session_state.conversation_state = {
                'user_info': {},
                'current_field': self.required_fields[0],
                'completed_fields': set()
            }
            st.session_state.previous_language = st.session_state.language
        
        collected_info = "\n".join([
            f"{k}: {st.session_state.conversation_state['user_info'][k]}"
            for k in st.session_state.conversation_state['completed_fields']
        ])
        
        next_required = st.session_state.conversation_state['current_field']
        missing_fields = ", ".join(self.get_missing_fields())
        
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=self.prompt_template.format(
                    language=current_language,
                    collected_info=collected_info or "None",
                    next_required=next_required,
                    missing_fields=missing_fields
                )
            )
        ]
        
        for msg in st.session_state.messages:
            role = MessageRole.ASSISTANT if msg["role"] == "assistant" else MessageRole.USER
            messages.append(Message(role=role, content=msg["content"]))
            
        if user_input:
            messages.append(Message(role=MessageRole.USER, content=user_input))
        
        try:
            response = self.client.chat(messages)
            self.logger.info(f"GPT response received for field {next_required}")
            return response
        except Exception as e:
            self.logger.error(f"Error getting GPT response: {str(e)}")
            raise

    def process_user_input(self, prompt: str) -> bool:
        """Process and validate user input, update state accordingly"""
        current_field = st.session_state.conversation_state['current_field']

        st.session_state.conversation_state['user_info'][current_field] = prompt
        st.session_state.conversation_state['completed_fields'].add(current_field)
        self.logger.info(f"Field {current_field} validated and saved: {prompt}")
        
        missing_fields = self.get_missing_fields()
        if not missing_fields:
            self.logger.info("All fields completed, preparing for stage 2")
            st.session_state.user_info = st.session_state.conversation_state['user_info'].copy()
            self.save_conversation_to_file()
            st.session_state.stage = 2  # Set stage to 2
            return True  # Important: Return True when done
        
        st.session_state.conversation_state['current_field'] = missing_fields[0]
        self.logger.info(f"Moving to next field: {missing_fields[0]}")
        return False  # Important: Return False when not done

    def render_chat(self):
        """Render the chat interface and handle user interactions"""
        st.header(self.translations['stage1_title'])
        
        # Display completion progress
        total_fields = len(self.required_fields)
        completed_fields = len(st.session_state.conversation_state['completed_fields'])
        progress = completed_fields / total_fields
        st.progress(progress, text=f"Completed {completed_fields} of {total_fields} fields")

        # Display current user info
        if st.session_state.conversation_state['completed_fields']:
            st.write("Collected Information:")
            for field in st.session_state.conversation_state['completed_fields']:
                st.write(f"{field}: {st.session_state.conversation_state['user_info'][field]}")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Handle user input
        if prompt := st.chat_input("Type your response..."):
            self.logger.info(f"User input received for field {st.session_state.conversation_state['current_field']}")
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                all_done = self.process_user_input(prompt)
                self.logger.info(f"process_user_input returned: {all_done}")  # Debug log
                
                if all_done:
                    self.logger.info(f"All information collected, moving to stage 2. Current stage: {st.session_state.stage}")
                    return True

                response = self.get_gpt_response(prompt)
                
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                self.save_conversation_to_file()
                
            except Exception as e:
                self.logger.error(f"Error processing chat: {str(e)}")
                st.error("An error occurred. Please try again.")
        
        # Start new conversation if needed
        if not st.session_state.messages:
            try:
                initial_response = self.get_gpt_response()
                with st.chat_message("assistant"):
                    st.markdown(initial_response)
                st.session_state.messages.append({"role": "assistant", "content": initial_response})
                self.save_conversation_to_file()
            except Exception as e:
                self.logger.error(f"Error starting conversation: {str(e)}")
                st.error("Error starting conversation. Please refresh the page.")
            
        return False

def render_user_info_form(translations):
    """Main entry point for the user info form"""
    if 'language' not in st.session_state:
        st.session_state.language = 'HE'
    
    bot = UserInfoBot(translations)
    return bot.render_chat()
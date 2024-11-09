import streamlit as st
from datetime import datetime
import re
import os
from pathlib import Path
import sys
import json

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
        
    def initialize_state(self):
        # Clear session state on page load/refresh
        if 'page_loaded' not in st.session_state:
            st.session_state.clear()
            st.session_state.page_loaded = True
            
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            
        if 'conversation_state' not in st.session_state:
            st.session_state.conversation_state = {
                'user_info': {},
                'current_field': 'first_name'
            }

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
            
        return self.client.chat(messages)

    def process_user_input(self, user_input: str):
        current_field = st.session_state.conversation_state['current_field']
        is_valid, error_message = self.validate_response(current_field, user_input)
        
        if is_valid:
            st.session_state.conversation_state['user_info'][current_field] = user_input
            
            # Define the order of fields
            field_order = [
                'first_name', 'last_name', 'id_number', 'gender', 
                'age', 'hmo_number', 'hmo_name', 'insurance_plan'
            ]
            
            # Move to next field
            current_index = field_order.index(current_field)
            if current_index < len(field_order) - 1:
                st.session_state.conversation_state['current_field'] = field_order[current_index + 1]
            else:
                # All fields collected
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
            # Display user message in chat
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Process user input
            all_done = self.process_user_input(prompt)
            if all_done:
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

            # Save conversation if needed
            if 'session_id' in st.session_state:
                conversation_file = settings.OUTPUT_DIR / f"conversation_{st.session_state.session_id}.json"
                with open(conversation_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
        
        # Start conversation if no messages
        if not st.session_state.messages:
            initial_response = self.get_gpt_response()
            with st.chat_message("assistant"):
                st.markdown(initial_response)
            st.session_state.messages.append({"role": "assistant", "content": initial_response})
            
        return False

def render_user_info_form(translations):
    bot = UserInfoBot(translations)
    return bot.render_chat()
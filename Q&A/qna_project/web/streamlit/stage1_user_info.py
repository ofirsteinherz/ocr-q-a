import streamlit as st
from datetime import datetime
import os
import json
import logging
from pathlib import Path
from typing import Dict

from qna_project.config.settings import settings  # Added back for output directory
from qna_project.clients.gpt_client import GPTClient, Message, MessageRole

class UserInfoBot:
    def __init__(self, translations):
        self.translations = translations
        self.setup_logging()
        
        self.client = GPTClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
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

        Important instructions:
        1. Ask for only ONE piece of information at a time
        2. Validate each response based on the rules above
        3. If invalid, explain why and ask again
        4. If valid, move to the next piece of information
        5. After collecting ALL information, respond with the data in this exact format:
           '''json
           {{"first_name": "...", "last_name": "...", "id_number": "...", "gender": "...", 
             "age": "...", "hmo_number": "...", "hmo_name": "...", "insurance_plan": "..."}}
           '''

        Additional language-specific instructions:
        - If language is 'he': Use Hebrew and maintain Right-to-Left (RTL) text direction
        - If language is 'en': Use English and maintain Left-to-Right (LTR) text direction
        """

    def setup_logging(self):
        """Initialize logging configuration"""
        log_dir = settings.LOGS_DIR / "site_logs"  # Using settings
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"UserInfoBot_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            log_file = log_dir / f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)

    def save_conversation_to_file(self):
        """Save current conversation state to a JSON file"""
        if 'session_id' in st.session_state:
            chat_file = settings.OUTPUT_DIR / f"chat_history_{st.session_state.session_id}.json"
            conversation_data = {
                'messages': st.session_state.messages,
                'timestamp': datetime.now().isoformat(),
                'session_id': st.session_state.session_id
            }
            
            chat_file.parent.mkdir(parents=True, exist_ok=True)
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Conversation saved to {chat_file}")

    def initialize_state(self):
        """Initialize basic session state"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'language' not in st.session_state:
            st.session_state.language = 'HE'
            
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(datetime.now().strftime('%Y%m%d_%H%M%S'))

    def extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON data from response if present"""
        # Check for both triple quote and triple backtick formats
        for delimiter in ["'''json", "```json"]:
            if delimiter in response:
                try:
                    # Split by the delimiter and take the part after it
                    json_str = response.split(delimiter)[1]
                    # Remove the closing delimiter (both ''' and ``` cases)
                    json_str = json_str.split("'''")[0].split("```")[0].strip()
                    return json.loads(json_str)
                except:
                    continue
        return None

    def get_gpt_response(self, user_input: str = None) -> str:
        """Get response from GPT"""
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=self.prompt_template.format(language=st.session_state.language.lower())
            )
        ]
        
        # Add conversation history
        for msg in st.session_state.messages:
            role = MessageRole.ASSISTANT if msg["role"] == "assistant" else MessageRole.USER
            messages.append(Message(role=role, content=msg["content"]))
            
        if user_input:
            messages.append(Message(role=MessageRole.USER, content=user_input))
        
        try:
            return self.client.chat(messages)
        except Exception as e:
            self.logger.error(f"Error getting GPT response: {str(e)}")
            raise

    def render_chat(self):
        """Render the chat interface"""
        st.header(self.translations['stage1_title'])
        self.initialize_state()

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Check if we have a complete JSON response
                if message["role"] == "assistant":
                    json_data = self.extract_json_from_response(message["content"])
                    if json_data:
                        st.session_state.user_info = json_data  # Save the extracted data
                        st.session_state.stage = 2
                        return True

        # Handle user input
        if prompt := st.chat_input("Type your response..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                response = self.get_gpt_response(prompt)
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                self.save_conversation_to_file()
                
                # Check if we have a complete JSON response
                json_data = self.extract_json_from_response(response)
                if json_data:
                    st.session_state.user_info = json_data  # Save the extracted data
                    st.session_state.stage = 2
                    return True
                    
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
    bot = UserInfoBot(translations)
    return bot.render_chat()
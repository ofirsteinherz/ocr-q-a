import os
import streamlit as st
import json
from datetime import datetime
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from qna_project.config.settings import settings
from qna_project.clients.gpt_client import GPTClient, Message, MessageRole

class QASession:
    def __init__(self):
        self.client = GPTClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.prompt_template = settings.get_prompt('data_gather')
            
    def save_conversation(self, message: str, role: str):
        timestamp = datetime.now().isoformat()
        conversation_entry = {
            'timestamp': timestamp,
            'session_id': st.session_state.session_id,
            'role': role,
            'message': message
        }
        
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
            
        st.session_state.conversation_history.append(conversation_entry)
        
        # Save to file in the output directory
        conversation_file = settings.OUTPUT_DIR / f"conversation_{st.session_state.session_id}.json"
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.conversation_history, f, ensure_ascii=False, indent=2)

    def get_response(self, user_question: str) -> str:
        context = f"User HMO: {st.session_state.user_info['hmo_name']}\n"
        context += f"Insurance Plan: {st.session_state.user_info['insurance_plan']}\n"
        
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=self.prompt_template
            ),
            Message(
                role=MessageRole.USER,
                content=f"{context}\nQuestion: {user_question}"
            )
        ]
        
        return self.client.chat(messages)

    def render_qa_session(self, translations):
        st.header(translations['stage3_title'])
        
        if 'user_info' not in st.session_state:
            st.error("No user information found. Please go back to stage 1.")
            st.session_state.stage = 1
            return False
        
        user_question = st.text_input("Ask a question:")
        
        if user_question:
            try:
                response = self.get_response(user_question)
                self.save_conversation(user_question, "user")
                self.save_conversation(response, "assistant")
                st.write("Response:", response)
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
        
        if st.button(translations['back']):
            st.session_state.stage = 2
            return False
        
        return None

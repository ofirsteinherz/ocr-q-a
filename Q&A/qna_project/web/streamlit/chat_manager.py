import streamlit as st
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = datetime.now()

class ChatManager:
    def __init__(self, title: str = "Chat Application"):
        """Initialize the chat manager with a title and session state."""
        self.title = title
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize the session state if it doesn't exist."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
    
    def display_chat_history(self) -> None:
        """Display all messages in the chat history."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                st.caption(f"Sent at: {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    def add_message(self, role: str, content: str, display: bool = False) -> None:
        """Add a new message to the chat history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        st.session_state.messages.append(message)
        
        if display:
            with st.chat_message(role):
                st.markdown(content)
                st.caption(f"Sent at: {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_user_input(self, placeholder: str = "Type your message...") -> Optional[str]:
        """Get user input from the chat input field."""
        return st.chat_input(placeholder)
    
    def clear_chat_history(self) -> None:
        """Clear all messages from the chat history."""
        st.session_state.messages = []
    
    def get_chat_history(self) -> List[Dict]:
        """Return the complete chat history."""
        return st.session_state.messages
    
    def handle_user_input(self, callback_fn=None):
        """Handle user input and process it through an optional callback function."""
        if prompt := self.get_user_input():
            # Add user message
            self.add_message("user", prompt, display=True)
            
            # Process response through callback if provided
            if callback_fn:
                response = callback_fn(prompt)
            else:
                response = f"Echo: {prompt}"  # Default echo behavior
            
            # Add assistant response
            self.add_message("assistant", response, display=True)
            
        return prompt
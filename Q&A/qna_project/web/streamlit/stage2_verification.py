import streamlit as st

def render_user_verification(translations):
    st.header(translations['stage2_title'])
    
    # Check if user info exists
    if 'user_info' not in st.session_state:
        st.error("No user information found. Please go back to stage 1.")
        st.session_state.stage = 1
        st.rerun()
        return False
    
    # Display user information in single column
    for key, value in st.session_state.user_info.items():
        if key != 'timestamp':
            st.write(f"**{translations.get(key, key)}:** {value}")
    
    # Single next button
    if st.button(translations['next']):
        st.session_state.stage = 3
        st.rerun()
        return True
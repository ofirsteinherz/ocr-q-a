import streamlit as st

def render_user_verification(translations):
    st.header(translations['stage2_title'])
    
    if 'user_info' not in st.session_state:
        st.error("No user information found. Please go back to stage 1.")
        st.session_state.stage = 1
        return False
    
    col1, col2 = st.columns(2)
    with col1:
        for key, value in st.session_state.user_info.items():
            if key != 'timestamp':
                st.write(f"**{translations.get(key, key)}:** {value}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(translations['back']):
            st.session_state.stage = 1
            return False
    with col2:
        if st.button(translations['next']):
            st.session_state.stage = 3
            return True
    return None

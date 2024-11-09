import streamlit as st
from datetime import datetime

def validate_id_number(id_number: str) -> bool:
    if not id_number.isdigit() or len(id_number) != 9:
        return False
    return True

def render_user_info_form(translations):
    st.header(translations['stage1_title'])
    
    with st.form("user_info_form"):
        first_name = st.text_input(translations['first_name'])
        last_name = st.text_input(translations['last_name'])
        id_number = st.text_input(translations['id_number'])
        gender = st.selectbox(translations['gender'], ['Male', 'Female', 'Other'])
        age = st.number_input(translations['age'], min_value=0, max_value=120)
        hmo_number = st.text_input(translations['hmo_number'])
        hmo_name = st.selectbox(translations['hmo_name'], ['Maccabi', 'Meuchedet', 'Clalit'])
        insurance_plan = st.selectbox(translations['insurance_plan'], ['Gold', 'Silver', 'Bronze'])

        submitted = st.form_submit_button(translations['next'])
        
        if submitted:
            if validate_id_number(id_number):
                user_info = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'id_number': id_number,
                    'gender': gender,
                    'age': age,
                    'hmo_number': hmo_number,
                    'hmo_name': hmo_name,
                    'insurance_plan': insurance_plan,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.user_info = user_info
                st.session_state.stage = 2
                return True
            else:
                st.error("Invalid ID number. Please enter a valid 9-digit number.")
                return False
    return False
import streamlit as st
import uuid
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from qna_project.web.streamlit.stage1_user_info import render_user_info_form
from qna_project.web.streamlit.stage2_verification import render_user_verification
from qna_project.web.streamlit.stage3_qa import QASession

TRANSLATIONS = {
    'HE': {
        'title': 'מערכת שירות לקוחות',
        'stage1_title': 'איסוף פרטי לקוח',
        'stage2_title': 'אימות פרטי לקוח',
        'stage3_title': 'שאלות ותשובות',
        'first_name': 'שם פרטי',
        'last_name': 'שם משפחה',
        'id_number': 'מספר תעודת זהות',
        'gender': 'מגדר',
        'age': 'גיל',
        'hmo_number': 'מספר כרטיס קופת חולים',
        'hmo_name': 'שם קופת חולים',
        'insurance_plan': 'תוכנית ביטוח',
        'next': 'הבא',
        'back': 'חזור',
        'submit': 'שלח',
        'edit': 'ערוך פרטים',
    },
    'EN': {
        'title': 'Customer Service System',
        'stage1_title': 'User Information Collection',
        'stage2_title': 'User Information Verification',
        'stage3_title': 'Q&A Session',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'id_number': 'ID Number',
        'gender': 'Gender',
        'age': 'Age',
        'hmo_number': 'HMO Card Number',
        'hmo_name': 'HMO Name',
        'insurance_plan': 'Insurance Plan',
        'next': 'Next',
        'back': 'Back',
        'submit': 'Submit',
        'edit': 'Edit Details',
    }
}

def initialize_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'stage' not in st.session_state:
        st.session_state.stage = 1
    if 'language' not in st.session_state:
        st.session_state.language = 'HE'

def main():
    initialize_session_state()
    
    st.sidebar.selectbox(
        "Language / שפה",
        ['HE', 'EN'],
        key='language'
    )
    
    translations = TRANSLATIONS[st.session_state.language]
    
    st.title(translations['title'])
    st.write(f"Stage {st.session_state.stage} / 3")
    
    if st.session_state.stage == 1:
        render_user_info_form(translations)
    elif st.session_state.stage == 2:
        render_user_verification(translations)
    elif st.session_state.stage == 3:
        qa_session = QASession()
        qa_session.render_qa_session(translations)

if __name__ == "__main__":
    main()
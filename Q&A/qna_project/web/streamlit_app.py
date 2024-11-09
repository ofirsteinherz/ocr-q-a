import streamlit as st
import requests
from requests.exceptions import ConnectionError
from pathlib import Path
import logging

# Get the project root directory (2 levels up from web/streamlit_app.py)
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOGS_DIR / "streamlit.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_service(url):
    """Check if a service is available"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def wait_for_services():
    """Wait for all services to be available"""
    services = {
        "Data Gathering Service": "http://localhost:5001",
        "Q&A Service": "http://localhost:5002"
    }
    
    for service_name, url in services.items():
        if not check_service(url):
            st.error(f"❌ {service_name} is not available at {url}")
        else:
            st.success(f"✅ {service_name} is running")

def main():
    st.title("Data Analysis and Q&A System")
    logger.info("Starting Streamlit application")
    
    # Check services status
    st.sidebar.title("Services Status")
    wait_for_services()
    
    # Stage selection
    stage = st.sidebar.radio(
        "Select Stage",
        ["1. Data Gathering", "2. Show Data", "3. Q&A"]
    )
    
    if stage == "1. Data Gathering":
        st.header("Data Gathering")
        if st.button("Gather Data"):
            try:
                with st.spinner("Gathering data..."):
                    response = requests.post("http://localhost:5001/gather")
                    if response.status_code == 200:
                        st.success("Data gathered successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.json().get('message', 'Unknown error')}")
            except ConnectionError:
                st.error("Could not connect to the data gathering service. Please make sure it's running.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in data gathering: {str(e)}")
            
    elif stage == "2. Show Data":
        st.header("Data Visualization")
        st.info("Data visualization will be implemented here")
        
    elif stage == "3. Q&A":
        st.header("Question & Answer")
        question = st.text_input("Enter your question:")
        if question and st.button("Ask"):
            try:
                with st.spinner("Getting answer..."):
                    response = requests.post("http://localhost:5002/qa")
                    if response.status_code == 200:
                        st.success("Got response!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.json().get('message', 'Unknown error')}")
            except ConnectionError:
                st.error("Could not connect to the Q&A service. Please make sure it's running.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in Q&A: {str(e)}")

if __name__ == "__main__":
    main()

from flask import Flask, render_template, request, jsonify
from pathlib import Path
import os
import logging

# Get the project root directory (3 levels up from web/qa_service/app.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOGS_DIR / "qa_service.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='templates/static')
app.config['DATA_DIR'] = str(DATA_DIR)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "qa_service"}), 200

@app.route('/qa', methods=['POST'])
def answer_question():
    try:
        logger.info("Received Q&A request")
        # Add your Q&A logic here
        return jsonify({
            "status": "success",
            "message": "Q&A endpoint",
            "project_root": str(PROJECT_ROOT)
        }), 200
    except Exception as e:
        logger.error(f"Error in answer_question: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Q&A service on port 5002")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Logs directory: {LOGS_DIR}")
    logger.info(f"Data directory: {DATA_DIR}")
    app.run(port=5002, host='0.0.0.0', debug=True)

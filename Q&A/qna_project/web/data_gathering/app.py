from flask import Flask, render_template, request, jsonify
from pathlib import Path
import os
import logging

# Get the project root directory (3 levels up from web/data_gathering/app.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
UPLOAD_FOLDER = PROJECT_ROOT / "uploads"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOGS_DIR / "data_gathering.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='templates/static')
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "data_gathering"}), 200

@app.route('/gather', methods=['POST'])
def gather_data():
    try:
        logger.info("Received data gathering request")
        # Add your data gathering logic here
        return jsonify({
            "status": "success",
            "message": "Data gathering endpoint",
            "project_root": str(PROJECT_ROOT)
        }), 200
    except Exception as e:
        logger.error(f"Error in gather_data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting data gathering service on port 5001")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Logs directory: {LOGS_DIR}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    app.run(port=5001, host='0.0.0.0', debug=True)
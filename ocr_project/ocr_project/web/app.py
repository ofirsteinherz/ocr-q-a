# app.py
from flask import Flask, render_template, request, jsonify
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from ocr_project.core.ocr_service import OCRService
import glob
import time

app = Flask(__name__, static_folder='templates/static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Get the project root directory (2 levels up from web/app.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_latest_log():
    """Get the most recent log file and its last line"""
    try:
        # Get all log files matching the pattern
        log_files = glob.glob(str(LOGS_DIR / "extract_form_fields_*.log"))
        if not log_files:
            return None
        
        # Get the most recent log file
        latest_log = max(log_files, key=os.path.getctime)
        
        # Read the file and get relevant information
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return None
                
            # Get the last line
            last_line = lines[-1].strip()
            
            # Parse the log line to determine the current step
            if "Starting form processing" in last_line:
                return {"step": "start", "details": "Initializing process..."}
            elif "Starting PDF splitting process" in last_line:
                return {"step": "split", "details": "Splitting PDF into sections"}
            elif "Processing section" in last_line:
                section = last_line.split("Processing section")[1].split(":")[0].strip()
                return {"step": "analyze", "details": f"Processing section {section}"}
            elif "Sending request to Document Analyzer" in last_line:
                return {"step": "extract", "details": "Extracting text"}
            elif "Sending request to GPT" in last_line:
                return {"step": "process", "details": "Processing with GPT"}
            elif "Post-processing completed successfully" in last_line:
                return {"step": "complete", "details": "Complete!", "status": "complete"}
            elif "error" in last_line.lower():
                return {"step": "error", "details": last_line, "status": "error"}
            
            return {"step": "processing", "details": "Processing..."}
    except Exception as e:
        print(f"Error reading log: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def get_progress():
    progress = get_latest_log()
    if progress:
        # Make sure we're setting status correctly for completion
        if progress.get('step') == 'complete':
            progress['status'] = 'complete'
        return jsonify(progress)
    return jsonify({"step": "waiting", "details": "Waiting to start..."})

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(filepath))
        
        # Process the PDF
        ocr_service = OCRService()
        result = ocr_service.process_pdf(filepath)
        
        # Clean up uploaded file
        filepath.unlink(missing_ok=True)
        
        # If result is a string, parse it to ensure proper JSON
        if isinstance(result, str):
            try:
                import json
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
        
        # Add a status field to indicate completion
        if isinstance(result, dict):
            result['status'] = 'complete'
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    app.run(debug=True)
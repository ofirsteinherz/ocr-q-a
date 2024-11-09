from pathlib import Path
WEB_ROOT = Path(__file__).parent

# web/data_gathering/app.py
from flask import Flask, jsonify
from qna_project.config.settings import settings

app = Flask(__name__)

@app.route('/gather', methods=['POST'])
def gather_data():
    return jsonify({"status": "test", "message": "Data gathering endpoint"}), 200

if __name__ == '__main__':
    app.run(port=5001)
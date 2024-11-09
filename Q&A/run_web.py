import os
import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    import streamlit.web.bootstrap as bootstrap
    bootstrap.run(
        os.path.join(PROJECT_ROOT, "qna_project", "web", "streamlit", "app.py"),
        "",
        [],
        flag_options={},
    )
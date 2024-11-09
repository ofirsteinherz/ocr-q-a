# run_services.py (place this in the root directory)
import subprocess
import sys
import time
import signal
from pathlib import Path
import os

def get_project_root():
    return Path(__file__).parent

def run_service(command, name):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        print(f"Started {name} (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Error starting {name}: {str(e)}")
        return None

def stop_services(processes):
    for name, process in processes.items():
        if process:
            print(f"Stopping {name}...")
            if sys.platform == 'win32':
                process.terminate()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    
def main():
    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # Define service commands
    services = {
        "Data Gathering": [sys.executable, str(project_root / "qna_project" / "web" / "data_gathering" / "app.py")],
        "QA Service": [sys.executable, str(project_root / "qna_project" / "web" / "qa_service" / "app.py")],
        "Streamlit": [sys.executable, "-m", "streamlit", "run", str(project_root / "qna_project" / "web" / "streamlit_app.py")]
    }

    # Start all services
    processes = {}
    try:
        print("Starting services...")
        for name, command in services.items():
            print(f"\nStarting {name}...")
            print(f"Command: {' '.join(command)}")
            processes[name] = run_service(command, name)
            time.sleep(2)  # Give each service time to start

        print("\nAll services started. Press Ctrl+C to stop all services.")
        
        # Keep the script running and monitor the processes
        while all(p and p.poll() is None for p in processes.values()):
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived shutdown signal (Ctrl+C)")
    finally:
        stop_services(processes)
        print("All services stopped")

if __name__ == "__main__":
    main()
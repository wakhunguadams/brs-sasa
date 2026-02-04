#!/usr/bin/env python3
"""
BRS-SASA Startup Script
This script handles the startup of the BRS-SASA application with proper configuration
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
import argparse

def setup_environment():
    """
    Setup the environment for the application
    """
    # Add the project root to the Python path
    project_root = Path(__file__).parent

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Ensure required directories exist
    (project_root / "logs").mkdir(exist_ok=True)
    (project_root / "data").mkdir(exist_ok=True)
    (project_root / "chroma_data").mkdir(exist_ok=True)

    # Check if .env file exists, if not create from example
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists():
        print(f"Warning: .env file not found. Creating from {env_example}")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"Created .env file from example. Please update with your API keys.")
        else:
            print("Error: Neither .env nor .env.example found. Please create a .env file with your configuration.")

def start_api_server():
    """
    Start the FastAPI server
    """
    from core.config import settings
    import uvicorn

    print(f"Starting {settings.APP_NAME} API server on {settings.HOST}:{settings.PORT}")
    print(f"Debug mode: {'ON' if settings.DEBUG else 'OFF'}")
    print(f"LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"Docs available at: http://{settings.HOST}:{settings.PORT}/docs")

    # Don't use reload when running in a thread
    if settings.DEBUG:
        print("Note: Debug mode detected. For development with hot-reload, run API server separately using:")
        print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("Running without reload for threading compatibility...")
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # Disable reload when running in thread
            log_level=settings.LOG_LEVEL.lower(),
            app_dir="."  # Specify the directory where main.py is located
        )
    else:
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # Always disable reload in threading context
            log_level=settings.LOG_LEVEL.lower(),
            app_dir="."  # Specify the directory where main.py is located
        )

def start_ui_server():
    """
    Start the Streamlit UI server
    """
    print("Starting BRS-SASA UI on http://localhost:8501")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "ui_demo.py",
        "--server.address", "localhost",
        "--server.port", "8501",
        "--server.headless", "true"  # Don't open browser automatically
    ])

def main():
    """
    Main entry point for the application
    """
    parser = argparse.ArgumentParser(description='BRS-SASA Startup Script')
    parser.add_argument('--mode', choices=['api', 'ui', 'both'], default='both',
                        help='Start API server, UI server, or both (default: both)')
    args = parser.parse_args()

    setup_environment()

    if args.mode == 'api':
        start_api_server()
    elif args.mode == 'ui':
        start_ui_server()
    else:  # both
        # Start both servers in parallel
        api_thread = threading.Thread(target=start_api_server)
        ui_thread = threading.Thread(target=start_ui_server)

        print("Starting both API and UI servers...")
        api_thread.start()
        ui_thread.start()

        try:
            api_thread.join()
            ui_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down servers...")
            sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
BRS-SASA Complete Startup Script
Starts API server, User UI, and CRM Dashboard
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
import argparse
import time

def setup_environment():
    """Setup the environment for the application"""
    project_root = Path(__file__).parent

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Ensure required directories exist
    (project_root / "logs").mkdir(exist_ok=True)
    (project_root / "data").mkdir(exist_ok=True)
    (project_root / "chroma_data").mkdir(exist_ok=True)

    # Check if .env file exists
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists():
        print(f"Warning: .env file not found. Creating from {env_example}")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"Created .env file from example. Please update with your API keys.")
        else:
            print("Error: Neither .env nor .env.example found. Please create a .env file.")

def start_api_server():
    """Start the FastAPI server"""
    from core.config import settings
    import uvicorn

    print(f"\n{'='*60}")
    print(f"🚀 Starting {settings.APP_NAME} API Server")
    print(f"{'='*60}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"Debug: {'ON' if settings.DEBUG else 'OFF'}")
    print(f"LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"{'='*60}\n")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
        app_dir="."
    )

def start_ui_server():
    """Start the Streamlit User UI"""
    print(f"\n{'='*60}")
    print(f"🎨 Starting BRS-SASA User Interface")
    print(f"{'='*60}")
    print(f"URL: http://localhost:8501")
    print(f"Purpose: Public-facing chat interface")
    print(f"{'='*60}\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "ui_demo.py",
        "--server.address", "localhost",
        "--server.port", "8501",
        "--server.headless", "true"
    ])

def start_crm_dashboard():
    """Start the CRM Dashboard"""
    print(f"\n{'='*60}")
    print(f"📊 Starting BRS-SASA CRM Dashboard")
    print(f"{'='*60}")
    print(f"URL: http://localhost:8502")
    print(f"Purpose: Admin interface for monitoring")
    print(f"{'='*60}\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "crm_dashboard.py",
        "--server.address", "localhost",
        "--server.port", "8502",
        "--server.headless", "true"
    ])

def print_startup_summary():
    """Print summary of all services"""
    time.sleep(3)  # Wait for services to start
    
    print(f"\n{'='*60}")
    print(f"✅ BRS-SASA Services Started Successfully!")
    print(f"{'='*60}")
    print(f"\n📋 Service URLs:")
    print(f"  • API Server:      http://localhost:8000")
    print(f"  • API Docs:        http://localhost:8000/docs")
    print(f"  • User Interface:  http://localhost:8501")
    print(f"  • CRM Dashboard:   http://localhost:8502")
    print(f"\n💡 Usage:")
    print(f"  • Users interact via:     http://localhost:8501")
    print(f"  • Admins monitor via:     http://localhost:8502")
    print(f"  • Developers test via:    http://localhost:8000/docs")
    print(f"\n⚠️  Press Ctrl+C to stop all services")
    print(f"{'='*60}\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='BRS-SASA Complete Startup Script')
    parser.add_argument('--mode', 
                       choices=['api', 'ui', 'crm', 'all'], 
                       default='all',
                       help='Start specific service or all (default: all)')
    args = parser.parse_args()

    setup_environment()

    if args.mode == 'api':
        start_api_server()
    elif args.mode == 'ui':
        start_ui_server()
    elif args.mode == 'crm':
        start_crm_dashboard()
    else:  # all
        # Start all services in parallel
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        ui_thread = threading.Thread(target=start_ui_server, daemon=True)
        crm_thread = threading.Thread(target=start_crm_dashboard, daemon=True)
        summary_thread = threading.Thread(target=print_startup_summary, daemon=True)

        print(f"\n🚀 Starting all BRS-SASA services...\n")
        
        api_thread.start()
        time.sleep(2)  # Let API start first
        
        ui_thread.start()
        crm_thread.start()
        summary_thread.start()

        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print(f"🛑 Shutting down all services...")
            print(f"{'='*60}\n")
            sys.exit(0)

if __name__ == "__main__":
    main()

import os
import sys
import subprocess
from pathlib import Path

# Locate backend directory and virtual environments
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
backend_venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
root_venv_python = root_dir / "venv" / "Scripts" / "python.exe"

# Select python executable
if backend_venv_python.exists():
    py_executable = str(backend_venv_python)
elif root_venv_python.exists():
    py_executable = str(root_venv_python)
else:
    py_executable = sys.executable

if __name__ == "__main__":
    print("=" * 60)
    print("      Starting LegalEase Fullstack Server (Port 4000)      ")
    print("=" * 60)
    print(f" * Python interpreter: {py_executable}")
    print(f" * Backend directory:  {backend_dir}")
    print(f" * Frontend URL:       file:///{root_dir / 'frontend.html'}")
    print(" * API URL:            http://127.0.0.1:4000/api")
    print("=" * 60)
    
    # Run backend/run.py with selected python
    backend_run_script = backend_dir / "run.py"
    subprocess.run([py_executable, str(backend_run_script)], cwd=str(backend_dir))

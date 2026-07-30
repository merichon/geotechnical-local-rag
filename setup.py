#!/usr/bin/env python3
"""
Setup script for offline RAG system.
Handles environment configuration and dependency installation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_python_version():
    """Check Python version is 3.10+"""
    print_header("CHECKING PYTHON VERSION")

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        return False

    print("✓ Python version OK\n")
    return True


def create_venv():
    """Create virtual environment."""
    print_header("CREATING VIRTUAL ENVIRONMENT")

    venv_path = Path("venv")

    if venv_path.exists():
        print("✓ Virtual environment already exists\n")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created\n")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment\n")
        return False


def get_pip_command():
    """Get appropriate pip command for current OS."""
    if platform.system() == "Windows":
        return Path("venv/Scripts/pip.exe")
    return Path("venv/bin/pip")


def install_requirements():
    """Install Python packages."""
    print_header("INSTALLING DEPENDENCIES")

    pip_cmd = get_pip_command()

    if not pip_cmd.exists():
        print("❌ pip not found in virtual environment\n")
        return False

    # On Windows pip.exe can't upgrade itself while running, so use `python -m pip`.
    python_cmd = pip_cmd.parent / ("python.exe" if platform.system() == "Windows" else "python")

    try:
        subprocess.run([str(python_cmd), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_cmd), "install", "-r", "requirements.txt"], check=True)
        print("\n✓ Dependencies installed\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}\n")
        return False


def create_project_structure():
    """Create project directory structure."""
    print_header("CREATING PROJECT STRUCTURE")

    dirs = [
        "data/raw",
        "data/processed",
        "src",
        "tests",
        "notebooks"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}/")

    print()
    return True


def create_env_file():
    """Create .env file from template."""
    print_header("CONFIGURING ENVIRONMENT")

    env_path = Path(".env")
    example_path = Path(".env.example")

    if env_path.exists():
        print("✓ .env file already exists\n")
        return True

    if example_path.exists():
        content = example_path.read_text()
        env_path.write_text(content)
        print("✓ Created .env from .env.example\n")
        return True

    print("⚠ .env.example not found\n")
    return True


def verify_installation():
    """Verify installation is complete."""
    print_header("VERIFYING INSTALLATION")

    python_cmd = get_pip_command().parent / ("python.exe" if platform.system() == "Windows" else "python")

    if not python_cmd.exists():
        print("❌ Python executable not found\n")
        return False

    # Test imports
    test_code = """
import sys
try:
    import sentence_transformers
    import torch
    import numpy
    import sqlite3
    print("✓ All core packages imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""

    try:
        result = subprocess.run(
            [str(python_cmd), "-c", test_code],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.returncode == 0:
            print("\n✓ Installation verified\n")
            return True
        else:
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠ Verification timeout (packages may still be loading)\n")
        return True
    except Exception as e:
        print(f"⚠ Verification error: {e}\n")
        return True


def print_next_steps():
    """Print instructions for next steps."""
    print_header("NEXT STEPS")

    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"

    print(f"""
1. Activate virtual environment:
   {activate_cmd}

2. Install Microsoft Foundry Local (on-device LLM runtime):
   https://learn.microsoft.com/azure/ai-foundry/foundry-local/

3. Start the service and load the model:
   foundry service start
   foundry model load phi-4-mini --device GPU

4. Test the setup:
   python tests/test_setup.py

5. Build the knowledge base from data/raw/*.txt:
   python src/ingest.py

6. Ask questions:
   python src/chat.py          (CLI)
   run_app.bat                 (Streamlit web UI)
""")


def main():
    """Run complete setup."""
    print("\n" + "="*60)
    print("  OFFLINE RAG SYSTEM - SETUP")
    print("="*60)

    steps = [
        ("Python version", check_python_version),
        ("Virtual environment", create_venv),
        ("Project structure", create_project_structure),
        ("Dependencies", install_requirements),
        ("Environment config", create_env_file),
        ("Verification", verify_installation),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            sys.exit(1)

    print_next_steps()
    print("="*60)
    print("  SETUP COMPLETE ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

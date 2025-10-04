#!/usr/bin/env python3
"""Setup script for ETL Dashboard."""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ required, found {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    directories = [
        "data/uploads",
        "data/processed",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    # Create .gitkeep files
    (Path("data/uploads") / ".gitkeep").touch()
    (Path("data/processed") / ".gitkeep").touch()
    
    print("✅ Directories created")
    return True

def setup_environment():
    """Set up environment file."""
    print("⚙️  Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("   Created .env from .env.example")
    
    print("✅ Environment setup completed")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def run_tests():
    """Run basic tests to verify installation."""
    print("🧪 Running basic tests...")
    
    # Test imports
    try:
        import fastapi
        import flask
        import pandas
        import openpyxl
        print("✅ Core dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Run a simple test
    if Path("tests").exists():
        if not run_command(f"{sys.executable} -m pytest tests/test_cleaning.py::TestCleanId::test_basic_cleaning -v", "Running sample test"):
            print("⚠️  Tests failed, but installation may still work")
    
    return True

def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*50)
    print("🎉 ETL Dashboard Setup Complete!")
    print("="*50)
    print("\n📋 Next Steps:")
    print("1. Review and update .env file with your settings")
    print("2. Start the development servers:")
    print("   python run_dev.py")
    print("\n🌐 Access Points:")
    print("   Frontend:  http://localhost:5000")
    print("   Backend:   http://localhost:8000")
    print("   API Docs:  http://localhost:8000/docs")
    print("\n📚 Documentation:")
    print("   README.md - General usage")
    print("   powerbi/   - Power BI integration guides")
    print("\n🧪 Testing:")
    print("   pytest tests/ -v")
    print("\n🐳 Docker Alternative:")
    print("   docker-compose up --build")

def main():
    """Main setup function."""
    print("🚀 ETL Dashboard Setup")
    print("=" * 30)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Installing dependencies", install_dependencies),
        ("Running verification tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n⚠️  Setup completed with {len(failed_steps)} issues:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nYou may need to resolve these issues manually.")
    else:
        print("\n✅ All setup steps completed successfully!")
    
    display_next_steps()

if __name__ == "__main__":
    main()

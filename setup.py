# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil

def check_requirements():
    """Check if required packages are installed"""
    try:
        import discord
        from dotenv import load_dotenv
        print("✅ Required packages are installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e.name}")
        return False

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Required packages installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install required packages.")
        return False

def setup_database():
    """Set up the database"""
    print("Setting up database...")
    try:
        # Import database module to create tables
        import database
        print("✅ Database setup complete.")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup():
    """Run the setup process"""
    print("\n===== DAO Bot Setup =====\n")
    
    # Check if requirements are installed
    if not check_requirements():
        print("\nInstalling required packages...")
        if not install_requirements():
            print("\nPlease install the required packages manually:")
            print("  pip install -r requirements.txt")
            return False
    
    # Set up database
    if not setup_database():
        print("\nDatabase setup failed. Please check the error message above.")
        return False
    
    print("\n===== Setup Complete =====\n")
    print("You can now run the migration script to transfer your data:")
    print("  python migrate.py run")
    print("\nOr start using the database version of the bot:")
    print("  python main_db.py")
    
    return True

if __name__ == "__main__":
    setup()
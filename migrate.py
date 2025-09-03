# -*- coding: utf-8 -*-
import os
import sys
import shutil
import logging
from datetime import datetime
from database import migrate_json_to_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('migration')

def backup_json_files():
    """Create backups of all JSON files before migration"""
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # List of JSON files to backup
    json_files = [
        "economy.json",
        "user_money.json",
        "jobs.json",
        "store.json",
        "sects.json",
        "tournaments.json"
    ]
    
    # Copy files to backup directory
    for file_name in json_files:
        if os.path.exists(file_name):
            try:
                shutil.copy2(file_name, os.path.join(backup_dir, file_name))
                logger.info(f"Backed up {file_name} to {backup_dir}")
            except Exception as e:
                logger.error(f"Failed to backup {file_name}: {e}")
    
    return backup_dir

def run_migration():
    """Run the migration process"""
    logger.info("Starting migration from JSON files to SQLite database")
    
    # Step 1: Create backups
    logger.info("Creating backups of JSON files...")
    backup_dir = backup_json_files()
    logger.info(f"Backups created in directory: {backup_dir}")
    
    # Step 2: Run the migration
    logger.info("Migrating data from JSON files to SQLite database...")
    success = migrate_json_to_db()
    
    if success:
        logger.info("Migration completed successfully!")
        logger.info("Your data has been migrated to the SQLite database.")
        logger.info(f"Backups of your original JSON files are available in the {backup_dir} directory.")
        logger.info("You can now update your bot code to use the database.")
    else:
        logger.error("Migration failed!")
        logger.error("Please check the logs for details and try again.")
        logger.error(f"Your original JSON files are still available in the {backup_dir} directory.")
    
    return success

def print_help():
    """Print help information"""
    print("\nDAO Bot Migration Tool")
    print("======================")
    print("This tool migrates your bot data from JSON files to a SQLite database.")
    print("\nUsage:")
    print("  python migrate.py [command]")
    print("\nCommands:")
    print("  run       Run the migration process")
    print("  help      Show this help message")
    print("\nExample:")
    print("  python migrate.py run")
    print("\nNote: Before running the migration, make sure your bot is not running.")
    print("      The migration process will create backups of your JSON files.")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print_help()
    elif sys.argv[1] == "run":
        run_migration()
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print_help()
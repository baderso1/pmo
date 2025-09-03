# -*- coding: utf-8 -*-
import os
import json
import logging
from typing import Dict, Any, List, Union, Optional, Tuple
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_integration')

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths (for backward compatibility)
DATA_FILE = "economy.json"
INCOME_FILE = "user_money.json"
JOBS_FILE = "jobs.json"
STORE_FILE = "store.json"
SECTS_FILE = "sects.json"
TOURNAMENTS_FILE = "tournaments.json"

# Helper functions to replace the original file operations
def ensure_file(file_path: str, default_content: Any = None) -> None:
    """Ensure a file exists with default content (for backward compatibility)"""
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            if default_content is None:
                json.dump({}, f)
            else:
                json.dump(default_content, f)

def load_json(file_path: str, default: Any = None) -> Dict:
    """Load JSON data from file or database based on file path"""
    if default is None:
        default = {}
    
    # Use database for specific files
    if os.path.basename(file_path) == DATA_FILE:
        # For economy.json, we'll construct the data from the database
        return get_economy_data()
    elif os.path.basename(file_path) == JOBS_FILE:
        # For jobs.json, get jobs from database
        return db.get_jobs()
    elif os.path.basename(file_path) == STORE_FILE:
        # For store.json, get store items from database
        return db.get_store_items()
    elif os.path.basename(file_path) == SECTS_FILE:
        # For sects.json, get sects from database
        return get_sects_data()
    elif os.path.basename(file_path) == TOURNAMENTS_FILE:
        # For tournaments.json, get tournaments from database
        return get_tournaments_data()
    
    # For other files, use the original file-based approach
    try:
        if not os.path.exists(file_path):
            ensure_file(file_path, default)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is empty or invalid JSON, return the default
        if file_path.endswith(JOBS_FILE):
            # Special case for jobs.json
            return default
        return {}

def save_json(file_path: str, data: Dict) -> None:
    """Save JSON data to file or database based on file path"""
    # Use database for specific files
    if os.path.basename(file_path) == DATA_FILE:
        # For economy.json, update the database
        save_economy_data(data)
        return
    elif os.path.basename(file_path) == JOBS_FILE:
        # For jobs.json, update jobs in database
        save_jobs_data(data)
        return
    elif os.path.basename(file_path) == STORE_FILE:
        # For store.json, update store items in database
        save_store_data(data)
        return
    elif os.path.basename(file_path) == SECTS_FILE:
        # For sects.json, update sects in database
        save_sects_data(data)
        return
    elif os.path.basename(file_path) == TOURNAMENTS_FILE:
        # For tournaments.json, update tournaments in database
        save_tournaments_data(data)
        return
    
    # For other files, use the original file-based approach
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Database integration functions
def get_economy_data() -> Dict[str, Dict[str, Any]]:
    """Get economy data from database in the format expected by the bot"""
    result = {}
    
    # Get all users from the database
    try:
        # We'll need to query all users
        # Since we don't have a direct method to get all users, we'll construct this manually
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row['user_id'] for row in cursor.fetchall()]
        
        for user_id in user_ids:
            user_data = db.get_user(user_id)
            inventory = db.get_inventory(user_id)
            
            # Ensure cash and bank are always present and are integers
            cash = user_data.get("cash")
            if cash is None:
                cash = 0
            else:
                try:
                    cash = int(cash)
                except (ValueError, TypeError):
                    cash = 0
                    
            bank = user_data.get("bank")
            if bank is None:
                bank = 0
            else:
                try:
                    bank = int(bank)
                except (ValueError, TypeError):
                    bank = 0
            
            # Format user data as expected by the bot
            user_entry = {
                "cash": cash,
                "bank": bank,
                "balance": 0,  # Will be calculated by the bot
                "last_collect": user_data.get("last_collect"),
                "job": user_data.get("job"),
                "last_cultivate": user_data.get("last_cultivate"),
                "last_job": user_data.get("last_job"),
                "inventory": [item["item_name"] for item in inventory],
                "message_count": user_data.get("message_count", 0)
            }
            
            # Get user metadata
            last_collects = db.get_user_meta(user_id, "last_collects")
            if last_collects:
                user_entry["last_collects"] = last_collects
            
            # Add to result
            result[user_id] = user_entry
        
        return result
    except Exception as e:
        logger.error(f"Error getting economy data: {e}")
        return {}

def save_economy_data(data: Dict[str, Dict[str, Any]]) -> None:
    """Save economy data to database"""
    try:
        for user_id, user_data in data.items():
            # Ensure cash and bank are always present and are integers
            cash = user_data.get("cash")
            if cash is None:
                cash = 0
            else:
                try:
                    cash = int(cash)
                except (ValueError, TypeError):
                    cash = 0
                    
            bank = user_data.get("bank")
            if bank is None:
                bank = 0
            else:
                try:
                    bank = int(bank)
                except (ValueError, TypeError):
                    bank = 0
            
            # Update user data
            db_user_data = {
                "cash": cash,
                "bank": bank,
                "job": user_data.get("job"),
                "last_cultivate": user_data.get("last_cultivate"),
                "last_collect": user_data.get("last_collect"),
                "message_count": user_data.get("message_count", 0)
            }
            db.update_user(user_id, db_user_data)
            
            # Update inventory
            if "inventory" in user_data and isinstance(user_data["inventory"], list):
                # First, get current inventory
                current_inventory = db.get_inventory(user_id)
                current_items = {item["item_name"]: item for item in current_inventory}
                
                # Add new items and remove missing items
                for item_name in user_data["inventory"]:
                    if item_name not in current_items:
                        db.add_inventory_item(user_id, item_name)
                
                for item in current_inventory:
                    if item["item_name"] not in user_data["inventory"]:
                        db.remove_inventory_item(user_id, item["item_name"])
            
            # Update last_collects metadata
            if "last_collects" in user_data:
                db.set_user_meta(user_id, "last_collects", user_data["last_collects"])
    except Exception as e:
        logger.error(f"Error saving economy data: {e}")

def save_jobs_data(data: Dict[str, List[int]]) -> None:
    """Save jobs data to database"""
    try:
        for job_name, pay_range in data.items():
            if isinstance(pay_range, list) and len(pay_range) >= 2:
                db.set_job(job_name, pay_range[0], pay_range[1])
    except Exception as e:
        logger.error(f"Error saving jobs data: {e}")

def get_sects_data() -> Dict[str, Dict[str, Any]]:
    """Get sects data from database in the format expected by the bot"""
    result = {}
    
    try:
        # Get all sects
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT sect_id FROM sects")
        sect_ids = [row['sect_id'] for row in cursor.fetchall()]
        
        for sect_id in sect_ids:
            sect_data = db.get_sect(sect_id)
            members = db.get_sect_members(sect_id)
            
            # Format sect data as expected by the bot
            sect_entry = {
                "name": sect_data.get("name", f"Sect {sect_id}"),
                "leader": sect_data.get("leader_id"),
                "description": sect_data.get("description", ""),
                "level": sect_data.get("level", 1),
                "wealth": sect_data.get("wealth", 0),
                "members": [member["user_id"] for member in members]
            }
            
            # Add to result
            result[sect_id] = sect_entry
        
        return result
    except Exception as e:
        logger.error(f"Error getting sects data: {e}")
        return {}

def save_sects_data(data: Dict[str, Dict[str, Any]]) -> None:
    """Save sects data to database"""
    try:
        # Get existing sects
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT sect_id FROM sects")
        existing_sects = {row['sect_id'] for row in cursor.fetchall()}
        
        for sect_id, sect_data in data.items():
            if sect_id in existing_sects:
                # Update existing sect
                update_data = {
                    "name": sect_data.get("name", f"Sect {sect_id}"),
                    "leader_id": sect_data.get("leader"),
                    "description": sect_data.get("description", ""),
                    "level": sect_data.get("level", 1),
                    "wealth": sect_data.get("wealth", 0)
                }
                db.update_sect(sect_id, update_data)
                
                # Update members
                if "members" in sect_data and isinstance(sect_data["members"], list):
                    # Get current members
                    current_members = db.get_sect_members(sect_id)
                    current_member_ids = {member["user_id"] for member in current_members}
                    
                    # Add new members
                    for member_id in sect_data["members"]:
                        if member_id not in current_member_ids:
                            role = "leader" if member_id == sect_data.get("leader") else "member"
                            db.add_sect_member(sect_id, member_id, role)
                    
                    # Remove missing members
                    for member in current_members:
                        if member["user_id"] not in sect_data["members"]:
                            db.remove_sect_member(sect_id, member["user_id"])
            else:
                # Create new sect
                db.create_sect(
                    sect_id,
                    sect_data.get("name", f"Sect {sect_id}"),
                    sect_data.get("leader", "0"),
                    sect_data.get("description", ""),
                    sect_data.get("level", 1),
                    sect_data.get("wealth", 0)
                )
                
                # Add members
                if "members" in sect_data and isinstance(sect_data["members"], list):
                    for member_id in sect_data["members"]:
                        if member_id != sect_data.get("leader"):  # Leader already added
                            db.add_sect_member(sect_id, member_id)
        
        # Remove deleted sects
        for sect_id in existing_sects:
            if sect_id not in data:
                cursor.execute("DELETE FROM sects WHERE sect_id = ?", (sect_id,))
        
        db.conn.commit()
    except Exception as e:
        logger.error(f"Error saving sects data: {e}")
        db.conn.rollback()

def get_tournaments_data() -> Dict[str, Dict[str, Any]]:
    """Get tournaments data from database in the format expected by the bot"""
    result = {}
    
    try:
        # Get all tournaments
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT tournament_id FROM tournaments")
        tournament_ids = [row['tournament_id'] for row in cursor.fetchall()]
        
        for tournament_id in tournament_ids:
            tournament_data = db.get_tournament(tournament_id)
            participants = db.get_tournament_participants(tournament_id)
            
            # Format tournament data as expected by the bot
            tournament_entry = {
                "title": tournament_data.get("title", f"Tournament {tournament_id}"),
                "host": tournament_data.get("host_id"),
                "description": tournament_data.get("description", ""),
                "status": tournament_data.get("status", "recruiting"),
                "participants": []
            }
            
            # Add winner if exists
            if tournament_data.get("winner_id"):
                tournament_entry["winner"] = tournament_data["winner_id"]
            
            # Add reward data if exists
            reward_data = tournament_data.get("reward_data", {})
            for key in ["add_money", "set_money", "rem_money", "reward_title"]:
                if key in reward_data:
                    tournament_entry[key] = reward_data[key]
            
            # Add participants
            bot_names = {}
            for participant in participants:
                participant_id = participant["participant_id"]
                # Convert to int for bot IDs (negative numbers)
                if participant["is_bot"] and participant["bot_name"]:
                    bot_names[participant_id] = participant["bot_name"]
                    # Convert to int for bots
                    try:
                        participant_id = int(participant_id)
                    except ValueError:
                        pass
                
                tournament_entry["participants"].append(participant_id)
            
            # Add bot names if any
            if bot_names:
                tournament_entry["bot_names"] = bot_names
            
            # Add to result
            result[tournament_id] = tournament_entry
        
        return result
    except Exception as e:
        logger.error(f"Error getting tournaments data: {e}")
        return {}

def save_tournaments_data(data: Dict[str, Dict[str, Any]]) -> None:
    """Save tournaments data to database"""
    try:
        # Get existing tournaments
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT tournament_id FROM tournaments")
        existing_tournaments = {row['tournament_id'] for row in cursor.fetchall()}
        
        for tournament_id, tournament_data in data.items():
            # Extract reward data
            reward_data = {}
            for key in ["add_money", "set_money", "rem_money", "reward_title"]:
                if key in tournament_data:
                    reward_data[key] = tournament_data[key]
            
            if tournament_id in existing_tournaments:
                # Update existing tournament
                update_data = {
                    "title": tournament_data.get("title", f"Tournament {tournament_id}"),
                    "host_id": tournament_data.get("host"),
                    "description": tournament_data.get("description", ""),
                    "status": tournament_data.get("status", "recruiting"),
                    "reward_data": reward_data
                }
                
                # Add winner if exists
                if "winner" in tournament_data:
                    update_data["winner_id"] = tournament_data["winner"]
                
                db.update_tournament(tournament_id, update_data)
                
                # Update participants
                if "participants" in tournament_data and isinstance(tournament_data["participants"], list):
                    # Get current participants
                    current_participants = db.get_tournament_participants(tournament_id)
                    current_participant_ids = {p["participant_id"] for p in current_participants}
                    
                    # Process participants
                    for participant_id in tournament_data["participants"]:
                        # Handle bot participants (negative IDs)
                        is_bot = isinstance(participant_id, int) and participant_id < 0
                        p_id_str = str(participant_id)
                        
                        bot_name = None
                        if is_bot and "bot_names" in tournament_data:
                            bot_name = tournament_data["bot_names"].get(p_id_str)
                        
                        if p_id_str not in current_participant_ids:
                            db.add_tournament_participant(tournament_id, p_id_str, is_bot, bot_name)
                    
                    # Remove missing participants
                    for participant in current_participants:
                        p_id = participant["participant_id"]
                        if p_id not in [str(p) for p in tournament_data["participants"]]:
                            db.remove_tournament_participant(tournament_id, p_id)
            else:
                # Create new tournament
                db.create_tournament(
                    tournament_id,
                    tournament_data.get("host", "0"),
                    tournament_data.get("title", f"Tournament {tournament_id}"),
                    tournament_data.get("description", ""),
                    reward_data
                )
                
                # Update status and winner
                update_data = {"status": tournament_data.get("status", "recruiting")}
                if "winner" in tournament_data:
                    update_data["winner_id"] = tournament_data["winner"]
                db.update_tournament(tournament_id, update_data)
                
                # Add participants
                if "participants" in tournament_data and isinstance(tournament_data["participants"], list):
                    for participant_id in tournament_data["participants"]:
                        is_bot = isinstance(participant_id, int) and participant_id < 0
                        p_id_str = str(participant_id)
                        
                        bot_name = None
                        if is_bot and "bot_names" in tournament_data:
                            bot_name = tournament_data["bot_names"].get(p_id_str)
                        
                        db.add_tournament_participant(tournament_id, p_id_str, is_bot, bot_name)
        
        # Remove deleted tournaments
        for tournament_id in existing_tournaments:
            if tournament_id not in data:
                cursor.execute("DELETE FROM tournaments WHERE tournament_id = ?", (tournament_id,))
        
        db.conn.commit()
    except Exception as e:
        logger.error(f"Error saving tournaments data: {e}")
        db.conn.rollback()

# Economy helper functions
def get_user_meta(user_id: Union[int, str], key: str, default: Any = None) -> Any:
    """Get user metadata from database"""
    result = db.get_user_meta(user_id, key)
    return result if result is not None else default

def set_user_meta(user_id: Union[int, str], key: str, value: Any) -> None:
    """Set user metadata in database"""
    db.set_user_meta(user_id, key, value)

def get_balance(user_id: Union[int, str]) -> Tuple[int, int]:
    """Get user's cash and bank balance"""
    return db.get_balance(user_id)

def add_money(user_id: Union[int, str], amount: int) -> bool:
    """Add money to user's cash balance"""
    return db.add_cash(user_id, amount)

def set_money(user_id: Union[int, str], amount: int) -> bool:
    """Set user's cash balance"""
    return db.set_cash(user_id, amount)

def add_bank(user_id: Union[int, str], amount: int) -> bool:
    """Add money to user's bank balance"""
    return db.add_bank(user_id, amount)

def set_bank(user_id: Union[int, str], amount: int) -> bool:
    """Set user's bank balance"""
    return db.set_bank(user_id, amount)

# Initialize database with default jobs if needed
def init_default_jobs(default_jobs: Dict[str, List[int]]) -> None:
    """Initialize database with default jobs"""
    jobs = db.get_jobs()
    if not jobs:
        for job_name, pay_range in default_jobs.items():
            db.set_job(job_name, pay_range[0], pay_range[1])
        logger.info("Default jobs initialized in database")

# Migration function to be called when switching to database
def migrate_from_json() -> bool:
    """Migrate data from JSON files to database"""
    from database import migrate_json_to_db
    return migrate_json_to_db()

# Function to check if migration is needed
def check_migration_needed() -> bool:
    """Check if migration from JSON to database is needed"""
    # Check if economy.json exists and has data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:  # If there's data in the file
                    # Check if database is empty
                    conn = db.conn
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM users")
                    count = cursor.fetchone()['count']
                    return count == 0
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return False
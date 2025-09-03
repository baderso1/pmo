# -*- coding: utf-8 -*-
import os
import json
import sqlite3
from typing import Dict, Any, Optional, List, Union
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('database')

# Database constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dao_bot.db')

class Database:
    """Database handler for the Discord bot using SQLite"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Users table - stores basic user information
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                cash INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                job TEXT DEFAULT NULL,
                last_cultivate TEXT DEFAULT NULL,
                last_collect TEXT DEFAULT NULL,
                message_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # User metadata table - stores additional user data as JSON
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_meta (
                user_id TEXT,
                meta_key TEXT,
                meta_value TEXT,  -- JSON string
                PRIMARY KEY (user_id, meta_key),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')
            
            # Inventory table - stores user inventory items
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                item_name TEXT,
                quantity INTEGER DEFAULT 1,
                rarity TEXT DEFAULT 'common',
                metadata TEXT DEFAULT '{}',  -- JSON string for additional item data
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')
            
            # Jobs table - stores job definitions
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_name TEXT PRIMARY KEY,
                min_pay INTEGER,
                max_pay INTEGER
            )
            ''')
            
            # User jobs table - stores user job progress
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_jobs (
                user_id TEXT,
                job_name TEXT,
                xp INTEGER DEFAULT 0,
                rank TEXT DEFAULT 'apprentice',
                last_work TEXT DEFAULT NULL,
                PRIMARY KEY (user_id, job_name),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (job_name) REFERENCES jobs(job_name) ON DELETE CASCADE
            )
            ''')
            
            # Sects table - stores sect information
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sects (
                sect_id TEXT PRIMARY KEY,
                name TEXT,
                leader_id TEXT,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level INTEGER DEFAULT 1,
                wealth INTEGER DEFAULT 0,
                max_members INTEGER DEFAULT 10
            )
            ''')
            
            # Sect members table - stores sect membership
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sect_members (
                sect_id TEXT,
                user_id TEXT,
                role TEXT DEFAULT 'member',  -- 'leader', 'elder', 'member'
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sect_id, user_id),
                FOREIGN KEY (sect_id) REFERENCES sects(sect_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')
            
            # Store items table - stores store items
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_items (
                item_name TEXT PRIMARY KEY,
                price INTEGER,
                description TEXT DEFAULT '',
                stock INTEGER DEFAULT -1,  -- -1 means unlimited
                min_rank INTEGER DEFAULT 0,
                rarity TEXT DEFAULT 'common',
                metadata TEXT DEFAULT '{}'  -- JSON string for additional item data
            )
            ''')
            
            # Tournaments table - stores tournament information
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                tournament_id TEXT PRIMARY KEY,
                host_id TEXT,
                title TEXT,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'recruiting',  -- 'recruiting', 'active', 'completed'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                winner_id TEXT DEFAULT NULL,
                reward_data TEXT DEFAULT '{}'  -- JSON string for reward data
            )
            ''')
            
            # Tournament participants table - stores tournament participants
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                tournament_id TEXT,
                participant_id TEXT,  -- can be user_id or bot_id (negative)
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_bot INTEGER DEFAULT 0,  -- 0 for user, 1 for bot
                bot_name TEXT DEFAULT NULL,  -- only for bots
                PRIMARY KEY (tournament_id, participant_id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id) ON DELETE CASCADE
            )
            ''')
            
            # Commit the changes
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()
            raise
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    # User data methods
    def get_user(self, user_id: Union[int, str]) -> Dict[str, Any]:
        """Get user data from the database"""
        user_id = str(user_id)
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = self.cursor.fetchone()
            
            if user:
                return dict(user)
            else:
                # Create new user if not exists
                self.cursor.execute(
                    "INSERT INTO users (user_id, cash, bank) VALUES (?, 0, 0)",
                    (user_id,)
                )
                self.conn.commit()
                return {"user_id": user_id, "cash": 0, "bank": 0, "job": None, 
                        "last_cultivate": None, "last_collect": None, "message_count": 0}
        except sqlite3.Error as e:
            logger.error(f"Error getting user {user_id}: {e}")
            self.conn.rollback()
            return {"user_id": user_id, "cash": 0, "bank": 0, "job": None, 
                    "last_cultivate": None, "last_collect": None, "message_count": 0}
    
    def update_user(self, user_id: Union[int, str], data: Dict[str, Any]) -> bool:
        """Update user data in the database"""
        user_id = str(user_id)
        try:
            # Get existing user or create if not exists
            user = self.get_user(user_id)
            
            # Build the update query dynamically based on provided data
            fields = []
            values = []
            for key, value in data.items():
                if key in user and key != 'user_id':
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return True  # Nothing to update
            
            fields.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
            values.append(user_id)
            
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating user {user_id}: {e}")
            self.conn.rollback()
            return False
    
    def get_user_meta(self, user_id: Union[int, str], meta_key: str) -> Any:
        """Get user metadata from the database"""
        user_id = str(user_id)
        try:
            self.cursor.execute(
                "SELECT meta_value FROM user_meta WHERE user_id = ? AND meta_key = ?",
                (user_id, meta_key)
            )
            result = self.cursor.fetchone()
            
            if result:
                return json.loads(result['meta_value'])
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user meta {user_id}.{meta_key}: {e}")
            return None
    
    def set_user_meta(self, user_id: Union[int, str], meta_key: str, meta_value: Any) -> bool:
        """Set user metadata in the database"""
        user_id = str(user_id)
        try:
            # Ensure user exists
            self.get_user(user_id)
            
            # Convert value to JSON string
            json_value = json.dumps(meta_value)
            
            # Use UPSERT pattern (INSERT OR REPLACE)
            self.cursor.execute(
                "INSERT OR REPLACE INTO user_meta (user_id, meta_key, meta_value) VALUES (?, ?, ?)",
                (user_id, meta_key, json_value)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting user meta {user_id}.{meta_key}: {e}")
            self.conn.rollback()
            return False
    
    # Economy methods
    def get_balance(self, user_id: Union[int, str]) -> tuple[int, int]:
        """Get user's cash and bank balance"""
        user = self.get_user(user_id)
        
        # Ensure cash and bank are always present and are integers
        cash = user.get('cash')
        if cash is None:
            cash = 0
        else:
            try:
                cash = int(cash)
            except (ValueError, TypeError):
                cash = 0
                
        bank = user.get('bank')
        if bank is None:
            bank = 0
        else:
            try:
                bank = int(bank)
            except (ValueError, TypeError):
                bank = 0
                
        return cash, bank
    
    def add_cash(self, user_id: Union[int, str], amount: int) -> bool:
        """Add cash to user's balance"""
        user_id = str(user_id)
        try:
            # Ensure amount is an integer
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                logger.warning(f"Invalid amount {amount} for user {user_id}, using 0")
                amount = 0
                
            user = self.get_user(user_id)
            
            # Ensure cash is an integer
            cash = user.get('cash')
            if cash is None:
                cash = 0
            else:
                try:
                    cash = int(cash)
                except (ValueError, TypeError):
                    cash = 0
                    
            new_cash = max(0, cash + amount)  # Prevent negative cash
            return self.update_user(user_id, {"cash": new_cash})
        except Exception as e:
            logger.error(f"Error adding cash to user {user_id}: {e}")
            return False
    
    def set_cash(self, user_id: Union[int, str], amount: int) -> bool:
        """Set user's cash balance"""
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount {amount} for user {user_id}, using 0")
            amount = 0
            
        amount = max(0, amount)  # Prevent negative cash
        return self.update_user(user_id, {"cash": amount})
    
    def add_bank(self, user_id: Union[int, str], amount: int) -> bool:
        """Add money to user's bank balance"""
        user_id = str(user_id)
        try:
            # Ensure amount is an integer
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                logger.warning(f"Invalid amount {amount} for user {user_id}, using 0")
                amount = 0
                
            user = self.get_user(user_id)
            
            # Ensure bank is an integer
            bank = user.get('bank')
            if bank is None:
                bank = 0
            else:
                try:
                    bank = int(bank)
                except (ValueError, TypeError):
                    bank = 0
                    
            new_bank = max(0, bank + amount)  # Prevent negative bank
            return self.update_user(user_id, {"bank": new_bank})
        except Exception as e:
            logger.error(f"Error adding bank to user {user_id}: {e}")
            return False
    
    def set_bank(self, user_id: Union[int, str], amount: int) -> bool:
        """Set user's bank balance"""
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount {amount} for user {user_id}, using 0")
            amount = 0
            
        amount = max(0, amount)  # Prevent negative bank
        return self.update_user(user_id, {"bank": amount})
    
    # Inventory methods
    def get_inventory(self, user_id: Union[int, str]) -> List[Dict[str, Any]]:
        """Get user's inventory items"""
        user_id = str(user_id)
        try:
            self.cursor.execute(
                "SELECT * FROM inventory WHERE user_id = ?",
                (user_id,)
            )
            items = self.cursor.fetchall()
            return [dict(item) for item in items]
        except sqlite3.Error as e:
            logger.error(f"Error getting inventory for user {user_id}: {e}")
            return []
    
    def add_inventory_item(self, user_id: Union[int, str], item_name: str, 
                          quantity: int = 1, rarity: str = 'common', 
                          metadata: Dict[str, Any] = None) -> bool:
        """Add an item to user's inventory"""
        user_id = str(user_id)
        if metadata is None:
            metadata = {}
        
        try:
            # Ensure user exists
            self.get_user(user_id)
            
            # Check if item already exists
            self.cursor.execute(
                "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ? AND rarity = ?",
                (user_id, item_name, rarity)
            )
            existing_item = self.cursor.fetchone()
            
            if existing_item:
                # Update quantity
                new_quantity = existing_item['quantity'] + quantity
                self.cursor.execute(
                    "UPDATE inventory SET quantity = ? WHERE id = ?",
                    (new_quantity, existing_item['id'])
                )
            else:
                # Insert new item
                self.cursor.execute(
                    "INSERT INTO inventory (user_id, item_name, quantity, rarity, metadata) VALUES (?, ?, ?, ?, ?)",
                    (user_id, item_name, quantity, rarity, json.dumps(metadata))
                )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding inventory item for user {user_id}: {e}")
            self.conn.rollback()
            return False
    
    def remove_inventory_item(self, user_id: Union[int, str], item_name: str, 
                             quantity: int = 1, rarity: str = None) -> bool:
        """Remove an item from user's inventory"""
        user_id = str(user_id)
        try:
            # Build query based on whether rarity is specified
            if rarity:
                query = "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ? AND rarity = ?"
                params = (user_id, item_name, rarity)
            else:
                query = "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ?"
                params = (user_id, item_name)
            
            self.cursor.execute(query, params)
            existing_item = self.cursor.fetchone()
            
            if not existing_item:
                return False  # Item not found
            
            if existing_item['quantity'] <= quantity:
                # Remove the item entirely
                self.cursor.execute("DELETE FROM inventory WHERE id = ?", (existing_item['id'],))
            else:
                # Reduce quantity
                new_quantity = existing_item['quantity'] - quantity
                self.cursor.execute(
                    "UPDATE inventory SET quantity = ? WHERE id = ?",
                    (new_quantity, existing_item['id'])
                )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing inventory item for user {user_id}: {e}")
            self.conn.rollback()
            return False
    
    # Jobs methods
    def get_jobs(self) -> Dict[str, List[int]]:
        """Get all available jobs"""
        try:
            self.cursor.execute("SELECT * FROM jobs")
            jobs = self.cursor.fetchall()
            return {job['job_name']: [job['min_pay'], job['max_pay']] for job in jobs}
        except sqlite3.Error as e:
            logger.error(f"Error getting jobs: {e}")
            return {}
    
    def set_job(self, job_name: str, min_pay: int, max_pay: int) -> bool:
        """Set or update a job"""
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO jobs (job_name, min_pay, max_pay) VALUES (?, ?, ?)",
                (job_name, min_pay, max_pay)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting job {job_name}: {e}")
            self.conn.rollback()
            return False
    
    def get_user_job(self, user_id: Union[int, str], job_name: str) -> Dict[str, Any]:
        """Get user's job data"""
        user_id = str(user_id)
        try:
            self.cursor.execute(
                "SELECT * FROM user_jobs WHERE user_id = ? AND job_name = ?",
                (user_id, job_name)
            )
            job = self.cursor.fetchone()
            
            if job:
                return dict(job)
            return {"user_id": user_id, "job_name": job_name, "xp": 0, "rank": "apprentice", "last_work": None}
        except sqlite3.Error as e:
            logger.error(f"Error getting job for user {user_id}: {e}")
            return {"user_id": user_id, "job_name": job_name, "xp": 0, "rank": "apprentice", "last_work": None}
    
    def update_user_job(self, user_id: Union[int, str], job_name: str, data: Dict[str, Any]) -> bool:
        """Update user's job data"""
        user_id = str(user_id)
        try:
            # Ensure user exists
            self.get_user(user_id)
            
            # Check if job record exists
            self.cursor.execute(
                "SELECT 1 FROM user_jobs WHERE user_id = ? AND job_name = ?",
                (user_id, job_name)
            )
            exists = self.cursor.fetchone()
            
            if exists:
                # Update existing record
                fields = []
                values = []
                for key, value in data.items():
                    if key not in ['user_id', 'job_name']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return True  # Nothing to update
                
                query = f"UPDATE user_jobs SET {', '.join(fields)} WHERE user_id = ? AND job_name = ?"
                values.extend([user_id, job_name])
                
                self.cursor.execute(query, values)
            else:
                # Create new record
                data.setdefault('xp', 0)
                data.setdefault('rank', 'apprentice')
                
                fields = ['user_id', 'job_name'] + list(data.keys())
                placeholders = ['?'] * len(fields)
                values = [user_id, job_name] + list(data.values())
                
                query = f"INSERT INTO user_jobs ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                self.cursor.execute(query, values)
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating job for user {user_id}: {e}")
            self.conn.rollback()
            return False
    
    # Sect methods
    def get_sect(self, sect_id: str) -> Dict[str, Any]:
        """Get sect data"""
        try:
            self.cursor.execute("SELECT * FROM sects WHERE sect_id = ?", (sect_id,))
            sect = self.cursor.fetchone()
            
            if sect:
                return dict(sect)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting sect {sect_id}: {e}")
            return None
    
    def create_sect(self, sect_id: str, name: str, leader_id: Union[int, str], 
                   description: str = '', level: int = 1, wealth: int = 0) -> bool:
        """Create a new sect"""
        leader_id = str(leader_id)
        try:
            # Ensure leader exists
            self.get_user(leader_id)
            
            self.cursor.execute(
                "INSERT INTO sects (sect_id, name, leader_id, description, level, wealth) VALUES (?, ?, ?, ?, ?, ?)",
                (sect_id, name, leader_id, description, level, wealth)
            )
            
            # Add leader as member with 'leader' role
            self.cursor.execute(
                "INSERT INTO sect_members (sect_id, user_id, role) VALUES (?, ?, 'leader')",
                (sect_id, leader_id)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating sect {name}: {e}")
            self.conn.rollback()
            return False
    
    def update_sect(self, sect_id: str, data: Dict[str, Any]) -> bool:
        """Update sect data"""
        try:
            # Check if sect exists
            if not self.get_sect(sect_id):
                return False
            
            # Build the update query
            fields = []
            values = []
            for key, value in data.items():
                if key != 'sect_id':
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return True  # Nothing to update
            
            query = f"UPDATE sects SET {', '.join(fields)} WHERE sect_id = ?"
            values.append(sect_id)
            
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating sect {sect_id}: {e}")
            self.conn.rollback()
            return False
    
    def get_sect_members(self, sect_id: str) -> List[Dict[str, Any]]:
        """Get all members of a sect"""
        try:
            self.cursor.execute(
                """SELECT sm.*, u.cash, u.bank 
                   FROM sect_members sm 
                   JOIN users u ON sm.user_id = u.user_id 
                   WHERE sm.sect_id = ?""",
                (sect_id,)
            )
            members = self.cursor.fetchall()
            return [dict(member) for member in members]
        except sqlite3.Error as e:
            logger.error(f"Error getting members for sect {sect_id}: {e}")
            return []
    
    def add_sect_member(self, sect_id: str, user_id: Union[int, str], role: str = 'member') -> bool:
        """Add a user to a sect"""
        user_id = str(user_id)
        try:
            # Ensure user exists
            self.get_user(user_id)
            
            # Check if sect exists
            if not self.get_sect(sect_id):
                return False
            
            # Add member
            self.cursor.execute(
                "INSERT OR REPLACE INTO sect_members (sect_id, user_id, role) VALUES (?, ?, ?)",
                (sect_id, user_id, role)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding member {user_id} to sect {sect_id}: {e}")
            self.conn.rollback()
            return False
    
    def remove_sect_member(self, sect_id: str, user_id: Union[int, str]) -> bool:
        """Remove a user from a sect"""
        user_id = str(user_id)
        try:
            self.cursor.execute(
                "DELETE FROM sect_members WHERE sect_id = ? AND user_id = ?",
                (sect_id, user_id)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing member {user_id} from sect {sect_id}: {e}")
            self.conn.rollback()
            return False
    
    # Store methods
    def get_store_items(self) -> Dict[str, Dict[str, Any]]:
        """Get all store items"""
        try:
            self.cursor.execute("SELECT * FROM store_items")
            items = self.cursor.fetchall()
            return {item['item_name']: dict(item) for item in items}
        except sqlite3.Error as e:
            logger.error(f"Error getting store items: {e}")
            return {}
    
    def get_store_item(self, item_name: str) -> Dict[str, Any]:
        """Get a specific store item"""
        try:
            self.cursor.execute("SELECT * FROM store_items WHERE item_name = ?", (item_name,))
            item = self.cursor.fetchone()
            
            if item:
                result = dict(item)
                # Parse metadata JSON
                if 'metadata' in result:
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        result['metadata'] = {}
                return result
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting store item {item_name}: {e}")
            return None
    
    def set_store_item(self, item_name: str, price: int, description: str = '', 
                      stock: int = -1, min_rank: int = 0, rarity: str = 'common', 
                      metadata: Dict[str, Any] = None) -> bool:
        """Set or update a store item"""
        if metadata is None:
            metadata = {}
        
        try:
            self.cursor.execute(
                """INSERT OR REPLACE INTO store_items 
                   (item_name, price, description, stock, min_rank, rarity, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item_name, price, description, stock, min_rank, rarity, json.dumps(metadata))
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting store item {item_name}: {e}")
            self.conn.rollback()
            return False
    
    def update_store_item_stock(self, item_name: str, change: int) -> bool:
        """Update a store item's stock"""
        try:
            item = self.get_store_item(item_name)
            if not item:
                return False
            
            # Only update if stock is not unlimited (-1)
            if item['stock'] != -1:
                new_stock = max(0, item['stock'] + change)
                self.cursor.execute(
                    "UPDATE store_items SET stock = ? WHERE item_name = ?",
                    (new_stock, item_name)
                )
                self.conn.commit()
            
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating stock for item {item_name}: {e}")
            self.conn.rollback()
            return False
    
    # Tournament methods
    def get_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament data"""
        try:
            self.cursor.execute("SELECT * FROM tournaments WHERE tournament_id = ?", (tournament_id,))
            tournament = self.cursor.fetchone()
            
            if tournament:
                result = dict(tournament)
                # Parse reward_data JSON
                if 'reward_data' in result:
                    try:
                        result['reward_data'] = json.loads(result['reward_data'])
                    except json.JSONDecodeError:
                        result['reward_data'] = {}
                return result
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting tournament {tournament_id}: {e}")
            return None
    
    def create_tournament(self, tournament_id: str, host_id: Union[int, str], 
                         title: str, description: str = '', 
                         reward_data: Dict[str, Any] = None) -> bool:
        """Create a new tournament"""
        host_id = str(host_id)
        if reward_data is None:
            reward_data = {}
        
        try:
            # Ensure host exists
            self.get_user(host_id)
            
            self.cursor.execute(
                """INSERT INTO tournaments 
                   (tournament_id, host_id, title, description, status, reward_data) 
                   VALUES (?, ?, ?, ?, 'recruiting', ?)""",
                (tournament_id, host_id, title, description, json.dumps(reward_data))
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating tournament {title}: {e}")
            self.conn.rollback()
            return False
    
    def update_tournament(self, tournament_id: str, data: Dict[str, Any]) -> bool:
        """Update tournament data"""
        try:
            # Check if tournament exists
            if not self.get_tournament(tournament_id):
                return False
            
            # Handle special case for reward_data
            if 'reward_data' in data and isinstance(data['reward_data'], dict):
                data['reward_data'] = json.dumps(data['reward_data'])
            
            # Build the update query
            fields = []
            values = []
            for key, value in data.items():
                if key != 'tournament_id':
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return True  # Nothing to update
            
            query = f"UPDATE tournaments SET {', '.join(fields)} WHERE tournament_id = ?"
            values.append(tournament_id)
            
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating tournament {tournament_id}: {e}")
            self.conn.rollback()
            return False
    
    def get_tournament_participants(self, tournament_id: str) -> List[Dict[str, Any]]:
        """Get all participants of a tournament"""
        try:
            self.cursor.execute(
                "SELECT * FROM tournament_participants WHERE tournament_id = ?",
                (tournament_id,)
            )
            participants = self.cursor.fetchall()
            return [dict(participant) for participant in participants]
        except sqlite3.Error as e:
            logger.error(f"Error getting participants for tournament {tournament_id}: {e}")
            return []
    
    def add_tournament_participant(self, tournament_id: str, participant_id: Union[int, str], 
                                 is_bot: bool = False, bot_name: str = None) -> bool:
        """Add a participant to a tournament"""
        participant_id = str(participant_id)
        try:
            # Check if tournament exists
            if not self.get_tournament(tournament_id):
                return False
            
            # If not a bot, ensure user exists
            if not is_bot:
                self.get_user(participant_id)
            
            self.cursor.execute(
                """INSERT OR REPLACE INTO tournament_participants 
                   (tournament_id, participant_id, is_bot, bot_name) 
                   VALUES (?, ?, ?, ?)""",
                (tournament_id, participant_id, 1 if is_bot else 0, bot_name)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding participant {participant_id} to tournament {tournament_id}: {e}")
            self.conn.rollback()
            return False
    
    def remove_tournament_participant(self, tournament_id: str, participant_id: Union[int, str]) -> bool:
        """Remove a participant from a tournament"""
        participant_id = str(participant_id)
        try:
            self.cursor.execute(
                "DELETE FROM tournament_participants WHERE tournament_id = ? AND participant_id = ?",
                (tournament_id, participant_id)
            )
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing participant {participant_id} from tournament {tournament_id}: {e}")
            self.conn.rollback()
            return False

# Create a global database instance
db = Database()

# Migration helpers
def migrate_json_to_db():
    """Migrate data from JSON files to the SQLite database"""
    from pathlib import Path
    import os
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # Helper to load JSON files
    def load_json_file(path):
        path = Path(path)
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    # Migrate economy data
    def migrate_economy():
        logger.info("Migrating economy data...")
        economy_path = os.path.join(DATA_DIR, "economy.json")
        economy_data = load_json_file(economy_path)
        
        for user_id, data in economy_data.items():
            # Create or update user
            user_data = {
                "cash": data.get("cash", 0),
                "bank": data.get("bank", 0),
                "job": data.get("job"),
                "last_cultivate": data.get("last_cultivate"),
                "last_collect": data.get("last_collect"),
                "message_count": data.get("message_count", 0)
            }
            db.update_user(user_id, user_data)
            
            # Migrate inventory
            if "inventory" in data and isinstance(data["inventory"], list):
                for item in data["inventory"]:
                    if isinstance(item, str):
                        db.add_inventory_item(user_id, item)
            
            # Migrate jobs data
            if "jobs" in data and isinstance(data["jobs"], dict):
                for job_name, job_data in data["jobs"].items():
                    if isinstance(job_data, dict):
                        job_update = {
                            "xp": job_data.get("xp", 0),
                            "rank": job_data.get("rank", "apprentice"),
                            "last_work": job_data.get("last_work")
                        }
                        db.update_user_job(user_id, job_name, job_update)
    
    # Migrate jobs definitions
    def migrate_jobs():
        logger.info("Migrating jobs definitions...")
        jobs_path = os.path.join(DATA_DIR, "jobs.json")
        jobs_data = load_json_file(jobs_path)
        
        for job_name, pay_range in jobs_data.items():
            if isinstance(pay_range, list) and len(pay_range) >= 2:
                db.set_job(job_name, pay_range[0], pay_range[1])
    
    # Migrate store items
    def migrate_store():
        logger.info("Migrating store items...")
        store_path = os.path.join(DATA_DIR, "store.json")
        store_data = load_json_file(store_path)
        
        for item_name, item_data in store_data.items():
            if isinstance(item_data, dict):
                metadata = {}
                for key, value in item_data.items():
                    if key not in ["price", "description", "stock", "min_rank", "rarity"]:
                        metadata[key] = value
                
                db.set_store_item(
                    item_name,
                    item_data.get("price", 0),
                    item_data.get("description", ""),
                    item_data.get("stock", -1),
                    item_data.get("min_rank", 0),
                    item_data.get("rarity", "common"),
                    metadata
                )
    
    # Migrate sects
    def migrate_sects():
        logger.info("Migrating sects data...")
        sects_path = os.path.join(DATA_DIR, "sects.json")
        sects_data = load_json_file(sects_path)
        
        for sect_id, sect_data in sects_data.items():
            if isinstance(sect_data, dict):
                # Create sect
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
    
    # Migrate tournaments
    def migrate_tournaments():
        logger.info("Migrating tournaments data...")
        tournaments_path = os.path.join(DATA_DIR, "tournaments.json")
        tournaments_data = load_json_file(tournaments_path)
        
        for tournament_id, tournament_data in tournaments_data.items():
            if isinstance(tournament_data, dict):
                # Extract reward data
                reward_data = {}
                for key in ["add_money", "set_money", "rem_money", "reward_title"]:
                    if key in tournament_data:
                        reward_data[key] = tournament_data[key]
                
                # Create tournament
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
                        bot_name = None
                        if is_bot and "bot_names" in tournament_data:
                            bot_name = tournament_data["bot_names"].get(str(participant_id))
                        db.add_tournament_participant(tournament_id, participant_id, is_bot, bot_name)
    
    # Run migrations
    try:
        migrate_economy()
        migrate_jobs()
        migrate_store()
        migrate_sects()
        migrate_tournaments()
        logger.info("Migration completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    # Test the database
    print("Testing database connection...")
    print(f"Database path: {db.db_path}")
    print("Database connected successfully!")
    
    # Run migration if needed
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        print("Starting migration...")
        success = migrate_json_to_db()
        print(f"Migration {'completed successfully' if success else 'failed'}!")
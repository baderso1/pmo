# -*- coding: utf-8 -*-
import os
import json
import random
import logging
import asyncio
import subprocess
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict, Tuple
import time

# Import database integration
import database
from db_integration import (
    # File operations
    ensure_file, load_json, save_json,
    # User metadata
    get_user_meta, set_user_meta,
    # Economy functions
    get_balance, add_money, set_money, add_bank, set_bank,
    # Database initialization
    init_default_jobs, check_migration_needed, migrate_from_json
)

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STARTUP_CHANNEL_ID = os.getenv("STARTUP_CHANNEL_ID")  # optional channel ID to announce
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")  # bot owner ID for admin commands

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found in environment (.env).")

# Files & constants (use stable data directory anchored to this file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _abs_data_path(path: str) -> str:
    # Map any relative filename into the data directory
    return path if os.path.isabs(path) else os.path.join(DATA_DIR, path)

# File paths (for backward compatibility)
DATA_FILE = "economy.json"
MONEY_FILE = "user_money.json"
INCOME_FILE = "income_roles.json"
STORE_FILE = "store.json"
JOBS_FILE = "jobs.json"
AUCTIONS_FILE = "auctions.json"
LOOT_ROLES_FILE = "loot_roles.json"
SECTS_FILE = "sects.json"
CASES_FILE = "cases.json"
CASE_ITEMS_FILE = "case_items.json"
TOURNAMENTS_FILE = "tournaments.json"

# Convert relative paths to absolute paths for file operations
DATA_FILE_PATH = _abs_data_path(DATA_FILE)
MONEY_FILE_PATH = _abs_data_path(MONEY_FILE)
INCOME_FILE_PATH = _abs_data_path(INCOME_FILE)
STORE_FILE_PATH = _abs_data_path(STORE_FILE)
JOBS_FILE_PATH = _abs_data_path(JOBS_FILE)
AUCTIONS_FILE_PATH = _abs_data_path(AUCTIONS_FILE)
LOOT_ROLES_FILE_PATH = _abs_data_path(LOOT_ROLES_FILE)
SECTS_FILE_PATH = _abs_data_path(SECTS_FILE)
CASES_FILE_PATH = _abs_data_path(CASES_FILE)
CASE_ITEMS_FILE_PATH = _abs_data_path(CASE_ITEMS_FILE)
TOURNAMENTS_FILE_PATH = _abs_data_path(TOURNAMENTS_FILE)

MONEY_ICON = "<:SpiritStonesPurple:1353660935465599086>"

# Default jobs
DEFAULT_JOBS = {
    "Farmer": [200, 400],
    "Blacksmith": [300, 500],
    "Alchemist": [400, 600],
    "Merchant": [600, 800]
}

# Initialize database with default jobs
init_default_jobs(DEFAULT_JOBS)

# Check if migration is needed
if check_migration_needed():
    print("\n===== MIGRATION NOTICE =====\n")
    print("It appears you have JSON data files but your database is empty.")
    print("You may want to run the migration script to transfer your data:")
    print("  python migrate.py run")
    print("\nThis will preserve all your bot data when transferring to a new host or updating.")
    print("===========================\n")

# Case system constants
CASE_MARKET_COOLDOWN = 10  # seconds
CASE_EMOJI = "🎁"
CASE_COLOR = 0x9b59b6  # Purple
CASE_COOLDOWNS = {}  # User ID -> {case_key -> timestamp}

# Job System Constants
JOB_RANKS = {
    "apprentice": {"xp_required": 0, "multiplier": 1.0, "message_requirement": 0},
    "beginner": {"xp_required": 100, "multiplier": 1.2, "message_requirement": 50},
    "adept": {"xp_required": 300, "multiplier": 1.5, "message_requirement": 150},
    "greater": {"xp_required": 600, "multiplier": 2.0, "message_requirement": 300},
    "master": {"xp_required": 1000, "multiplier": 3.0, "message_requirement": 500}
}

# Job progression multipliers for message requirements
JOB_PROGRESSION_MULTIPLIERS = [2, 3, 4, 5, 6, 7, 8, 9, 10]

# Job-specific crafting items and their base rarities
JOB_CRAFTING_ITEMS = {
    "Blacksmith": {
        "apprentice": {
            "items": ["Rusty Sword", "Basic Spear", "Simple Dagger"],
            "base_rarity": "common",
            "quality_chance": 0.05
        },
        "beginner": {
            "items": ["Iron Sword", "Steel Spear", "Sharp Dagger", "Battle Axe"],
            "base_rarity": "uncommon",
            "quality_chance": 0.10
        },
        "adept": {
            "items": ["Steel Greatsword", "Silver Spear", "Enchanted Dagger", "War Axe", "Battle Hammer"],
            "base_rarity": "rare",
            "quality_chance": 0.20
        },
        "greater": {
            "items": ["Mythril Sword", "Dragonbone Spear", "Shadow Dagger", "Thunder Axe", "Earth Hammer", "Lightning Blade"],
            "base_rarity": "legendary",
            "quality_chance": 0.35
        },
        "master": {
            "items": ["Celestial Blade", "Phoenix Spear", "Void Dagger", "Storm Axe", "Mountain Hammer", "Star Sword", "Moon Blade"],
            "base_rarity": "mythic",
            "quality_chance": 0.50
        }
    },
    "Alchemist": {
        "apprentice": {
            "items": ["Minor Healing Potion", "Weak Antidote", "Simple Elixir"],
            "base_rarity": "common",
            "quality_chance": 0.05
        },
        "beginner": {
            "items": ["Healing Potion", "Antidote", "Elixir of Strength", "Potion of Speed"],
            "base_rarity": "uncommon",
            "quality_chance": 0.10
        },
        "adept": {
            "items": ["Greater Healing Potion", "Powerful Antidote", "Elixir of Might", "Potion of Swiftness", "Elixir of Wisdom"],
            "base_rarity": "rare",
            "quality_chance": 0.20
        },
        "greater": {
            "items": ["Superior Healing Potion", "Universal Antidote", "Elixir of Power", "Potion of Haste", "Elixir of Intelligence", "Potion of Invisibility"],
            "base_rarity": "legendary",
            "quality_chance": 0.35
        },
        "master": {
            "items": ["Divine Healing Potion", "Panacea", "Elixir of Godly Might", "Potion of Time Manipulation", "Elixir of Omniscience", "Potion of Etherealness", "Elixir of Immortality"],
            "base_rarity": "mythic",
            "quality_chance": 0.50
        }
    },
    "Farmer": {
        "apprentice": {
            "items": ["Wheat", "Carrot", "Potato"],
            "base_rarity": "common",
            "quality_chance": 0.05
        },
        "beginner": {
            "items": ["Corn", "Tomato", "Lettuce", "Apple"],
            "base_rarity": "uncommon",
            "quality_chance": 0.10
        },
        "adept": {
            "items": ["Rice", "Strawberry", "Pumpkin", "Watermelon", "Grapes"],
            "base_rarity": "rare",
            "quality_chance": 0.20
        },
        "greater": {
            "items": ["Golden Apple", "Spirit Fruit", "Dragon Fruit", "Star Fruit", "Moon Melon", "Sun Pepper"],
            "base_rarity": "legendary",
            "quality_chance": 0.35
        },
        "master": {
            "items": ["Immortal Peach", "Divine Rice", "Celestial Fruit", "Cosmic Berry", "Ethereal Wheat", "Void Vegetable", "Astral Herb"],
            "base_rarity": "mythic",
            "quality_chance": 0.50
        }
    },
    "Merchant": {
        "apprentice": {
            "items": ["Common Goods", "Basic Supplies", "Simple Trinket"],
            "base_rarity": "common",
            "quality_chance": 0.05
        },
        "beginner": {
            "items": ["Trade Goods", "Quality Supplies", "Decorative Trinket", "Foreign Spice"],
            "base_rarity": "uncommon",
            "quality_chance": 0.10
        },
        "adept": {
            "items": ["Luxury Goods", "Premium Supplies", "Valuable Trinket", "Exotic Spice", "Rare Textile"],
            "base_rarity": "rare",
            "quality_chance": 0.20
        },
        "greater": {
            "items": ["Exotic Goods", "Royal Supplies", "Ancient Trinket", "Legendary Spice", "Imperial Textile", "Precious Gem"],
            "base_rarity": "legendary",
            "quality_chance": 0.35
        },
        "master": {
            "items": ["Divine Goods", "Celestial Supplies", "Mythical Trinket", "Cosmic Spice", "Ethereal Textile", "Perfect Gem", "Astral Relic"],
            "base_rarity": "mythic",
            "quality_chance": 0.50
        }
    }
}

# Create files if missing (for backward compatibility)
ensure_file(DATA_FILE_PATH, {})
ensure_file(INCOME_FILE_PATH, {})
ensure_file(STORE_FILE_PATH, {})
ensure_file(JOBS_FILE_PATH, DEFAULT_JOBS)
ensure_file(AUCTIONS_FILE_PATH, {})
ensure_file(LOOT_ROLES_FILE_PATH, {})
ensure_file(CASES_FILE_PATH, {})
ensure_file(CASE_ITEMS_FILE_PATH, {})
ensure_file(TOURNAMENTS_FILE_PATH, {})

# ---- Preconfigured special roles (Axes) ----
# Update these IDs to your guild's roles if they differ.
AXIS_HEALTH_ROLE_ID = 1360668572614918325  # Axis of Health
AXIS_WEALTH_ROLE_ID = 1360269383687082246  # Axis of Wealth
AXIS_LONGEVITY_ROLE_ID = 1355119735154540552  # Axis of Longevity
AXIS_LOVE_VIRTUE_ROLE_ID = 1360617657732173984  # Axis of Love and Virtue

# Optional realm override roles (priority order). If a member has any of these, use the role's
# name as their displayed Realm instead of the level-based realm. Update IDs to match your guild.
REALM_ROLE_IDS_PRIORITY: List[int] = [
    1360612064149901400,
    1360612008344424584,
    1360611957643804856,
]

# The rest of your main.py file follows here...
# You'll need to copy the remaining code from your original main.py file
# and replace any direct calls to load_json, save_json, get_user_meta, set_user_meta,
# add_money, set_money, add_bank, set_bank with the imported functions from db_integration.py

# For example, replace:
# def get_balances(user_id):
#     data = load_json(DATA_FILE)
#     user_data = data.get(str(user_id), {})
#     return user_data.get("cash", 0), user_data.get("bank", 0)

# With:
# def get_balances(user_id):
#     return get_balance(user_id)

# And so on for other functions that interact with the database.
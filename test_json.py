#!/usr/bin/env python3
"""Test script for JSON system"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
from main import (
    save_user_inventory, 
    load_user_inventory,
    save_user_equipment,
    load_user_equipment,
    save_user_stats,
    load_user_stats,
    ensure_json_files
)

def test_json_system():
    """Test the JSON system"""
    print("🧪 Testing JSON system...")
    
    # Ensure files exist
    ensure_json_files()
    print("✅ JSON files ensured")
    
    # Test user ID
    test_user_id = 12345
    
    # Test data
    test_inventory = [{"name": "Test Sword", "rarity": "common"}]
    test_equipment = {"weapon": None, "armor": None, "artifacts": []}
    test_stats = {"cash": 100, "bank": 50}
    
    print("Saving test data...")
    try:
        save_user_inventory(test_user_id, test_inventory)
        print("✅ Inventory saved")
        
        save_user_equipment(test_user_id, test_equipment)
        print("✅ Equipment saved")
        
        save_user_stats(test_user_id, test_stats)
        print("✅ Stats saved")
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False
    
    print("Loading test data...")
    try:
        loaded_inventory = load_user_inventory(test_user_id)
        loaded_equipment = load_user_equipment(test_user_id)
        loaded_stats = load_user_stats(test_user_id)
        
        print(f"✅ Inventory loaded: {loaded_inventory}")
        print(f"✅ Equipment loaded: {loaded_equipment}")
        print(f"✅ Stats loaded: {loaded_stats}")
        
        # Verify data matches
        if (loaded_inventory == test_inventory and 
            loaded_equipment == test_equipment and 
            loaded_stats["cash"] == 100 and 
            loaded_stats["bank"] == 50):
            print("✅ All data matches!")
            return True
        else:
            print("❌ Data mismatch!")
            return False
            
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return False

if __name__ == "__main__":
    success = test_json_system()
    if success:
        print("🎉 JSON system test PASSED!")
        sys.exit(0)
    else:
        print("💥 JSON system test FAILED!")
        sys.exit(1)

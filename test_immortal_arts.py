#!/usr/bin/env python3
"""Test script for immortal arts system"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
from main import get_user_meta, set_user_meta

def test_immortal_arts():
    """Test the immortal arts system"""
    print("🧪 Testing Immortal Arts system...")
    
    # Test user ID
    test_user_id = 12345
    
    # Test 1: Get initial data
    print("1. Getting initial user data...")
    initial_meta = get_user_meta(test_user_id)
    initial_rerolls = initial_meta.get("immortal_arts", {}).get("rerolls", 0)
    print(f"   Initial rerolls: {initial_rerolls}")
    
    # Test 2: Add rerolls
    print("2. Adding 5 rerolls...")
    current_meta = get_user_meta(test_user_id)
    if "immortal_arts" not in current_meta:
        current_meta["immortal_arts"] = {"rerolls": 0, "slots": [None, None, None], "unlocked_slots": 1}
    
    current_rerolls = current_meta["immortal_arts"].get("rerolls", 0)
    current_meta["immortal_arts"]["rerolls"] = current_rerolls + 5
    
    # Save the changes
    set_user_meta(test_user_id, current_meta)
    print(f"   Added 5 rerolls, new total: {current_meta['immortal_arts']['rerolls']}")
    
    # Test 3: Verify data was saved
    print("3. Verifying data was saved...")
    verify_meta = get_user_meta(test_user_id)
    verify_rerolls = verify_meta.get("immortal_arts", {}).get("rerolls", 0)
    print(f"   Verified rerolls: {verify_rerolls}")
    
    # Check if it worked
    if verify_rerolls == initial_rerolls + 5:
        print("✅ Immortal Arts system is working!")
        return True
    else:
        print(f"❌ Failed! Expected {initial_rerolls + 5}, got {verify_rerolls}")
        return False

if __name__ == "__main__":
    success = test_immortal_arts()
    if success:
        print("🎉 Immortal Arts test PASSED!")
        sys.exit(0)
    else:
        print("💥 Immortal Arts test FAILED!")
        sys.exit(1)


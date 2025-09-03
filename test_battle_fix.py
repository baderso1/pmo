#!/usr/bin/env python3
"""
Test script to verify battle command rewards
"""

import sys
import os

# Add the current directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Discord context for testing
class MockContext:
    def __init__(self, user_id):
        self.author = MockUser(user_id)
        self.guild = MockGuild()
    
    async def send(self, embed):
        print(f"Would send embed: {embed.title}")
        print(f"Description: {embed.description}")
        for field in embed.fields:
            print(f"Field: {field.name} = {field.value}")

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockGuild:
    def get_member(self, user_id):
        return MockMember()

class MockMember:
    def __init__(self):
        self.roles = []

def test_battle_loot_generation():
    """Test the battle loot generation function"""
    print("Testing battle loot generation...")
    
    # Import the function
    from main import generate_battle_loot
    
    # Test with different bot tiers
    bot_tiers = ["novice", "apprentice", "disciple", "core", "elder", "master"]
    
    for tier in bot_tiers:
        print(f"\nTesting {tier} tier:")
        for i in range(5):
            result = generate_battle_loot(None, None, tier)
            if result:
                item_name, rarity, sell_price = result
                print(f"  {i+1}: {item_name} ({rarity}) - {sell_price:,} stones")
            else:
                print(f"  {i+1}: No loot")
    
    print("\nBattle loot generation test completed!")

def test_battle_command_structure():
    """Test that the battle command structure is correct"""
    print("\nTesting battle command structure...")
    
    # Import the battle command function
    from main import battle
    
    # Check if the function exists and has the right signature
    if hasattr(battle, '__name__'):
        print(f"✓ Battle command function exists: {battle.__name__}")
    else:
        print("✗ Battle command function not found")
        return
    
    # Check if it's a hybrid command
    if hasattr(battle, 'hybrid_command'):
        print("✓ Battle command is a hybrid command")
    else:
        print("✗ Battle command is not a hybrid command")
    
    print("Battle command structure test completed!")

if __name__ == "__main__":
    print("Testing Battle Command Fixes...")
    print("=" * 40)
    
    try:
        test_battle_loot_generation()
        test_battle_command_structure()
        print("\n" + "=" * 40)
        print("All tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

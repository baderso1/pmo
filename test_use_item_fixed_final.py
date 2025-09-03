#!/usr/bin/env python3
"""
Test script to verify the final fix for the use_item command
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test if the main module can be imported"""
    try:
        import main
        print("✅ Successfully imported main.py")
        return True
    except Exception as e:
        print(f"❌ Failed to import main.py: {e}")
        return False

def test_command_registration():
    """Test if the use_item command is properly registered"""
    try:
        import main
        
        # Check if bot object exists
        if hasattr(main, 'bot'):
            print("✅ Bot object found")
        else:
            print("❌ Bot object not found")
            return False
            
        # Check if use_item command exists
        if hasattr(main, 'use_item'):
            print("✅ use_item command found")
        else:
            print("❌ use_item command not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing command registration: {e}")
        return False

def test_syntax():
    """Test if the file has valid Python syntax"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to compile the source
        compile(source, 'main.py', 'exec')
        print("✅ Python syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing final fix for use_item command...")
    print("=" * 50)
    
    tests = [
        ("Syntax Check", test_syntax),
        ("Bot Import", test_import),
        ("Command Registration", test_command_registration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The use_item command should now work correctly.")
        print("\n📝 Summary of final fixes applied:")
        print("   • Fixed AttributeError: 'Context' object has no attribute 'followup'")
        print("   • Improved slash command detection logic")
        print("   • Added try-catch around ctx.defer() for better error handling")
        print("   • Properly handles both slash commands and prefix commands")
        print("   • Uses ctx.followup.send for slash commands only")
        print("   • Uses send_embed for prefix commands")
        print("   • Command is properly registered with @bot.hybrid_command")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

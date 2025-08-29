#!/usr/bin/env python3
"""
Basic test script to verify Heyu modules work correctly.
This doesn't require pytest and can run standalone.
"""

import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from heyu.protocol import X10Protocol, X10Address, HouseCode, UnitCode, X10Command
        print("✓ Protocol module imported")
        
        from heyu.config import HeyuConfig
        print("✓ Config module imported")
        
        from heyu.serial import CM11AInterface
        print("✓ Serial module imported") 
        
        from heyu.commands import X10Commands
        print("✓ Commands module imported")
        
        from heyu.cli import main
        print("✓ CLI module imported")
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    
    return True

def test_protocol():
    """Test basic protocol functionality."""
    print("\nTesting protocol...")
    
    try:
        from heyu.protocol import X10Address, X10Protocol, HouseCode, UnitCode, X10Command
        
        # Test address parsing
        addr = X10Address.from_string('A1')
        assert addr.house_code == HouseCode.A
        assert addr.unit_code == UnitCode.UNIT_1
        assert str(addr) == 'A1'
        print("✓ Address parsing works")
        
        # Test protocol encoding
        protocol = X10Protocol()
        command_bytes = protocol.encode_address_command(addr, X10Command.ON)
        assert len(command_bytes) == 3
        print("✓ Command encoding works")
        
        # Test address validation
        assert protocol.validate_address('A1') == True
        assert protocol.validate_address('Q1') == False
        print("✓ Address validation works")
        
    except Exception as e:
        print(f"✗ Protocol test failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration functionality."""
    print("\nTesting config...")
    
    try:
        from heyu.config import HeyuConfig
        
        config = HeyuConfig()
        assert config.tty == "/dev/ttyUSB0"
        print("✓ Config initialization works")
        
        # Test alias resolution
        config.add_alias('test_device', 'A1')
        assert config.resolve_address('test_device') == 'A1'
        assert config.resolve_address('B2') == 'B2'  # No alias
        print("✓ Alias resolution works")
        
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False
    
    return True

def test_commands():
    """Test command controller (without actual hardware)."""
    print("\nTesting commands...")
    
    try:
        from heyu.config import HeyuConfig
        from heyu.commands import X10Commands
        
        config = HeyuConfig()
        commands = X10Commands(config)
        
        # Test status (should work without hardware)
        status = commands.status()
        assert 'serial_port' in status
        assert 'supported_commands' in status
        print("✓ Command controller status works")
        
    except Exception as e:
        print(f"✗ Commands test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🏠 Heyu Basic Test Suite")
    print("=" * 30)
    
    tests = [
        test_imports,
        test_protocol, 
        test_config,
        test_commands
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 30)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Basic functionality is working.")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
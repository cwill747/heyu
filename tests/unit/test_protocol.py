"""Unit tests for X10 protocol module."""

import pytest
from heyu.protocol import X10Protocol, HouseCode, UnitCode, X10Command, X10Address
from heyu.protocol.exceptions import InvalidAddressError, EncodingError

class TestHouseCode:
    """Test HouseCode enum."""
    
    def test_from_string_valid(self):
        """Test valid house code strings."""
        assert HouseCode.from_string('A') == HouseCode.A
        assert HouseCode.from_string('a') == HouseCode.A
        assert HouseCode.from_string('P') == HouseCode.P
    
    def test_from_string_invalid(self):
        """Test invalid house code strings."""
        with pytest.raises(InvalidAddressError):
            HouseCode.from_string('Q')
        with pytest.raises(InvalidAddressError):
            HouseCode.from_string('1')

class TestUnitCode:
    """Test UnitCode enum."""
    
    def test_from_int_valid(self):
        """Test valid unit numbers."""
        assert UnitCode.from_int(1) == UnitCode.UNIT_1
        assert UnitCode.from_int(16) == UnitCode.UNIT_16
    
    def test_from_int_invalid(self):
        """Test invalid unit numbers."""
        with pytest.raises(InvalidAddressError):
            UnitCode.from_int(0)
        with pytest.raises(InvalidAddressError):
            UnitCode.from_int(17)
    
    def test_to_int(self):
        """Test conversion back to integer."""
        assert UnitCode.UNIT_1.to_int() == 1
        assert UnitCode.UNIT_16.to_int() == 16

class TestX10Address:
    """Test X10Address class."""
    
    def test_from_string_valid(self):
        """Test valid address strings."""
        addr = X10Address.from_string('A1')
        assert addr.house_code == HouseCode.A
        assert addr.unit_code == UnitCode.UNIT_1
        
        addr = X10Address.from_string('P16')
        assert addr.house_code == HouseCode.P
        assert addr.unit_code == UnitCode.UNIT_16
    
    def test_from_string_invalid(self):
        """Test invalid address strings."""
        with pytest.raises(InvalidAddressError):
            X10Address.from_string('Q1')
        with pytest.raises(InvalidAddressError):
            X10Address.from_string('A17')
        with pytest.raises(InvalidAddressError):
            X10Address.from_string('A')
    
    def test_str_representation(self):
        """Test string representation."""
        addr = X10Address.from_string('A1')
        assert str(addr) == 'A1'
        
        addr = X10Address.from_string('P16')  
        assert str(addr) == 'P16'

class TestX10Protocol:
    """Test X10Protocol class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = X10Protocol()
    
    def test_encode_address_command_basic(self):
        """Test encoding basic commands."""
        addr = X10Address.from_string('A1')
        
        # Test ON command
        data = self.protocol.encode_address_command(addr, X10Command.ON)
        assert len(data) == 3
        assert data[0] == 0x04  # Header
        
        # Test OFF command  
        data = self.protocol.encode_address_command(addr, X10Command.OFF)
        assert len(data) == 3
        assert data[0] == 0x04  # Header
    
    def test_encode_address_command_dim_bright(self):
        """Test encoding DIM/BRIGHT commands."""
        addr = X10Address.from_string('A1')
        
        # Test DIM command with data
        data = self.protocol.encode_address_command(addr, X10Command.DIM, 15)
        assert len(data) == 4
        assert data[0] == 0x06  # Header for dim command
        assert data[3] == 15    # Data byte
        
        # Test invalid data range
        with pytest.raises(EncodingError):
            self.protocol.encode_address_command(addr, X10Command.DIM, 32)
    
    def test_encode_house_command(self):
        """Test encoding house-level commands."""
        data = self.protocol.encode_house_command(HouseCode.A, X10Command.ALL_LIGHTS_ON)
        assert len(data) == 2
        assert data[0] == 0x02  # House command header
    
    def test_validate_address(self):
        """Test address validation."""
        assert self.protocol.validate_address('A1') == True
        assert self.protocol.validate_address('P16') == True
        assert self.protocol.validate_address('Q1') == False
        assert self.protocol.validate_address('A17') == False
    
    def test_get_supported_commands(self):
        """Test getting supported commands."""
        commands = self.protocol.get_supported_commands()
        assert 'on' in commands
        assert 'off' in commands
        assert 'dim' in commands
        assert 'bright' in commands
    
    def test_calculate_checksum(self):
        """Test checksum calculation."""
        data = bytes([0x04, 0x66, 0x62])
        checksum = X10Protocol.calculate_checksum(data)
        assert checksum == (0x04 + 0x66 + 0x62) & 0xFF
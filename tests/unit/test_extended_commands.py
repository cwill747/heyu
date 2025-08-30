"""Unit tests for extended X10 commands."""

import pytest
from heyu.protocol import X10Protocol, X10Address, ExtendedCommand, HouseCode, UnitCode
from heyu.protocol.exceptions import EncodingError
from heyu.commands import X10Commands, CommandError
from heyu.config import HeyuConfig
from heyu.serial import CM11AInterface

class MockSerialInterface:
    """Mock serial interface for testing."""
    
    def __init__(self):
        self.written_data = []
        self.connected = True
        
    def write(self, data: bytes) -> int:
        self.written_data.append(data)
        return len(data)
    
    def read(self, size: int = 1) -> bytes:
        # Mock successful response
        return bytes([0x55])
    
    def in_waiting(self) -> int:
        return 0
    
    def close(self) -> None:
        pass

class TestExtendedCommands:
    """Test extended X10 command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = X10Protocol()
        self.config = HeyuConfig()
        self.mock_serial = MockSerialInterface()
        self.mock_interface = CM11AInterface("/dev/ttyUSB0", mock_serial=self.mock_serial)
        self.commands = X10Commands(self.config, self.mock_interface)
    
    def test_extended_preset_encoding(self):
        """Test extended preset command encoding."""
        addr = X10Address.from_string('A1')
        data = self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_PRESET, 15)
        
        assert len(data) == 5
        assert data[0] == 0x06  # Extended header
        assert data[3] == 0x31  # Extended preset command code
        assert data[4] == 15    # Dim level
    
    def test_extended_full_on_encoding(self):
        """Test extended full on command encoding.""" 
        addr = X10Address.from_string('B5')
        data = self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_FULL_ON)
        
        assert len(data) == 5
        assert data[0] == 0x06  # Extended header
        assert data[3] == 0xFE  # Extended full on command code
        assert data[4] == 0     # No additional data
    
    def test_extended_full_off_encoding(self):
        """Test extended full off command encoding."""
        addr = X10Address.from_string('C12')
        data = self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_FULL_OFF)
        
        assert len(data) == 5
        assert data[0] == 0x06  # Extended header
        assert data[3] == 0xFD  # Extended full off command code
        assert data[4] == 0     # No additional data
        
    def test_extended_status_encoding(self):
        """Test extended status request encoding."""
        addr = X10Address.from_string('D3')
        data = self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_STATUS)
        
        assert len(data) == 5
        assert data[0] == 0x06  # Extended header
        assert data[3] == 0x37  # Extended status command code
        assert data[4] == 0     # No additional data
    
    def test_extended_preset_invalid_level(self):
        """Test extended preset with invalid level."""
        addr = X10Address.from_string('A1')
        
        with pytest.raises(EncodingError):
            self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_PRESET, 32)
        
        with pytest.raises(EncodingError):
            self.protocol.encode_extended_command(addr, ExtendedCommand.EXTENDED_PRESET, -1)
    
    def test_xpreset_command(self):
        """Test xpreset high-level command.""" 
        result = self.commands.xpreset("A1", 20)
        assert result == True
        
        # Check that data was written to mock interface
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_xpreset_percentage_conversion(self):
        """Test xpreset with percentage conversion."""
        result = self.commands.xpreset("A1", 75)  # 75% should convert to ~23
        assert result == True
        
        # Check that data was written to mock interface
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_xon_command(self):
        """Test xon high-level command."""
        result = self.commands.xon("B2")
        assert result == True
        
        # Check that data was written
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_xoff_command(self):
        """Test xoff high-level command."""
        result = self.commands.xoff("C3")
        assert result == True
        
        # Check that data was written
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_xstatus_command(self):
        """Test xstatus high-level command."""
        result = self.commands.xstatus("D4")
        assert result == True
        
        # Check that data was written
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_xdim_command(self):
        """Test xdim command (alias for xpreset)."""
        result = self.commands.xdim("A1", 10)
        assert result == True
        
        # Check that data was written
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_extended_command_with_alias(self):
        """Test extended command with device alias."""
        self.config.add_alias("living_room", "A1")
        
        result = self.commands.xpreset("living_room", 15)
        assert result == True
        
        # Check that data was written
        assert len(self.mock_interface._serial.written_data) > 0
    
    def test_extended_command_invalid_address(self):
        """Test extended command with invalid address."""
        with pytest.raises(CommandError):
            self.commands.xpreset("Q1", 15)  # Invalid house code
        
        with pytest.raises(CommandError): 
            self.commands.xon("A17")  # Invalid unit code
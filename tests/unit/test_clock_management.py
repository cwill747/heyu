"""Unit tests for clock management commands."""

import pytest
from datetime import datetime, timezone
from heyu.commands import X10Commands
from heyu.config import HeyuConfig
from heyu.serial import CM11AInterface

class MockSerialInterface:
    """Mock serial interface for testing."""
    
    def __init__(self):
        self.written_data = []
        self.response_data = bytes([0x55])  # Default ACK response
        self.connected = True
        
    def write(self, data: bytes) -> int:
        self.written_data.append(data)
        return len(data)
    
    def read(self, size: int = 1) -> bytes:
        return self.response_data[:size]
    
    def in_waiting(self) -> int:
        return len(self.response_data)
    
    def close(self) -> None:
        pass

class TestClockManagement:
    """Test clock management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = HeyuConfig()
        self.mock_serial = MockSerialInterface()
        self.mock_interface = CM11AInterface("/dev/ttyUSB0", mock_serial=self.mock_serial)
        self.commands = X10Commands(self.config, self.mock_interface)
    
    def test_encode_clock_data(self):
        """Test clock data encoding."""
        # Test with a known date/time
        test_time = datetime(2024, 6, 15, 14, 30, 45)  # June 15, 2024, 14:30:45
        
        clock_data = self.commands._encode_clock_data(test_time)
        
        assert len(clock_data) == 7
        assert clock_data[0] == 0x9B  # Timer download code
        assert clock_data[1] == 45    # Seconds
        assert clock_data[2] == 30    # Minutes (30 + (14%2)*60 = 30)
        assert clock_data[3] == 7     # Hours/2 (14/2 = 7)
        
        # Day of year for June 15 should be around 167 (depending on leap year)
        expected_day = test_time.timetuple().tm_yday
        assert clock_data[4] == expected_day % 256
        
        # Byte 5 contains day of year radix and day of week mask
        day_mask = 1 << test_time.weekday() if test_time.weekday() < 6 else 1
        expected_byte5 = ((expected_day // 256) << 7) | day_mask
        assert clock_data[5] == expected_byte5
        
        # Byte 6 is housecode (A=0x6) shifted left 4 bits
        assert clock_data[6] == 0x60
    
    def test_setclock_command(self):
        """Test setclock high-level command."""
        result = self.commands.setclock()
        assert result == True
        
        # Check that clock data was written to mock interface
        assert len(self.mock_interface._serial.written_data) > 0
        
        # Verify the first byte of the written data is the clock command
        written = self.mock_interface._serial.written_data[0]
        assert written[0] == 0x9B  # Timer download code
    
    def test_readclock_command(self):
        """Test readclock high-level command."""
        # Set up mock response data for status request
        self.mock_serial.response_data = bytes([0x55] + [0x00] * 13)  # Mock 14-byte status
        
        result = self.commands.readclock()
        
        assert isinstance(result, dict)
        assert 'system_time' in result
        assert 'cm11a_time' in result
        assert 'status' in result
        assert 'raw_response' in result
        
        # Check that status request was sent
        assert len(self.mock_interface._serial.written_data) > 0
        written = self.mock_interface._serial.written_data[0]
        assert written[0] == 0x8B  # Status request command
    
    def test_clock_encoding_edge_cases(self):
        """Test clock encoding with edge cases."""
        # Test midnight
        midnight = datetime(2024, 1, 1, 0, 0, 0)
        data = self.commands._encode_clock_data(midnight)
        assert data[1] == 0    # Seconds
        assert data[2] == 0    # Minutes
        assert data[3] == 0    # Hours/2
        
        # Test near end of year
        end_of_year = datetime(2024, 12, 31, 23, 59, 59)
        data = self.commands._encode_clock_data(end_of_year)
        assert data[1] == 59   # Seconds
        assert data[2] == 59   # Minutes (59 + (23%2)*60 = 119)
        assert data[3] == 11   # Hours/2 (23/2 = 11)
    
    def test_clock_data_format(self):
        """Test that clock data follows CM11A format exactly."""
        test_time = datetime(2024, 3, 15, 12, 0, 0)  # Noon on March 15
        clock_data = self.commands._encode_clock_data(test_time)
        
        # Verify each byte follows the expected format
        assert clock_data[0] == 0x9B                    # Command code
        assert 0 <= clock_data[1] <= 59                 # Seconds
        assert 0 <= clock_data[2] <= 119                # Extended minutes
        assert 0 <= clock_data[3] <= 11                 # Hour/2
        assert 0 <= clock_data[4] <= 255                # Day of year low
        assert 0 <= clock_data[5] <= 255                # Day of year high + day mask
        assert (clock_data[6] & 0xF0) == 0x60          # Housecode A in upper nibble
    
    def test_weekday_encoding(self):
        """Test that weekday is properly encoded in day mask."""
        # Test different days of week
        for day_offset in range(7):
            base_date = datetime(2024, 6, 17)  # Monday, June 17, 2024
            test_date = datetime(2024, 6, 17 + day_offset, 12, 0, 0)
            
            clock_data = self.commands._encode_clock_data(test_date)
            
            # Verify day mask is set correctly
            day_mask = clock_data[5] & 0x7F  # Lower 7 bits
            weekday = test_date.weekday()
            
            if weekday < 6:  # Monday-Saturday
                expected_mask = 1 << weekday
            else:  # Sunday
                expected_mask = 1
                
            assert day_mask == expected_mask
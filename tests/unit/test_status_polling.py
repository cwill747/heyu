"""Unit tests for status polling and acknowledgment handling."""

import pytest
from datetime import datetime
from heyu.commands import X10Commands
from heyu.config import HeyuConfig
from heyu.serial import CM11AInterface
from heyu.protocol import CM11AStatus, CM11AStatusParser


class MockSerialInterface:
    """Mock serial interface for testing status polling."""
    
    def __init__(self):
        self.written_data = []
        self.response_queue = []  # Queue of responses to return
        self.response_data = bytes([0x55])  # Default ACK response
        self.connected = True
        self.status_response = None
        self.poll_response = None
        self.read_call_count = 0
        
    def write(self, data: bytes) -> int:
        self.written_data.append(data)
        return len(data)
    
    def read(self, size: int = 1) -> bytes:
        """Return data from queue or default response."""
        if self.response_queue:
            response = self.response_queue.pop(0)
            return response[:size]
        return self.response_data[:size]
    
    def in_waiting(self) -> int:
        return len(self.response_data) if not self.response_queue else len(self.response_queue[0])
    
    def close(self) -> None:
        pass
    
    def set_status_response(self, status_data: bytes):
        """Set the 14-byte status response data."""
        self.status_response = status_data
        self.response_data = status_data
    
    def set_poll_response(self, poll_data: bytes):
        """Set poll response data."""
        self.poll_response = poll_data
    
    def queue_response(self, data: bytes):
        """Queue a response to be returned by read()."""
        self.response_queue.append(data)


class TestCM11AStatusParser:
    """Test CM11A status response parsing."""
    
    def test_parse_valid_status(self):
        """Test parsing a valid 14-byte status response."""
        # Sample status data (based on original Heyu format)
        status_data = bytes([
            0x10, 0x00,  # Battery usage: 16 minutes
            0x2D,        # Seconds: 45
            0x1E,        # Minutes: 30
            0x07,        # Hours/2: 7 (14 hours)
            0xA7,        # Day of year: 167 (June 16)
            0x08,        # Day of week mask: bit 3 (Wednesday)
            0x61,        # Firmware rev 1, House code A (0x6)
            0x01, 0x00,  # Last addressed: unit 1
            0x02, 0x00,  # Monitored status: unit 2
            0x00, 0x00   # Dimmed status: none
        ])
        
        status = CM11AStatusParser.parse_status(status_data)
        
        assert status.battery_usage_minutes == 16
        assert status.firmware_revision == 1
        assert status.seconds == 45
        assert status.minutes == 30
        assert status.hours == 14
        assert status.day_of_year == 167
        assert status.day_of_week_mask == 8
        assert status.house_code == 'A'
        assert status.last_addressed_devices == 1
        assert status.monitored_device_status == 2
        assert status.dimmed_device_status == 0
        assert status.raw_data == status_data
    
    def test_parse_invalid_length(self):
        """Test parsing with invalid data length."""
        with pytest.raises(ValueError, match="Status data must be 14 bytes"):
            CM11AStatusParser.parse_status(bytes([1, 2, 3]))
    
    def test_format_battery_status(self):
        """Test battery status formatting."""
        # Normal battery usage
        assert CM11AStatusParser.format_battery_status(90) == "1:30 (hh:mm)"
        
        # High battery usage (over 40 hours)
        assert "REPLACE SOON" in CM11AStatusParser.format_battery_status(2500)
        
        # Unknown battery usage
        assert CM11AStatusParser.format_battery_status(0xFFFF) == "Unknown (cold restart)"
    
    def test_format_device_bitmap(self):
        """Test device bitmap formatting."""
        # Unit 1 on
        assert CM11AStatusParser.format_device_bitmap(1) == "0000000000000001"
        
        # Units 1 and 16 on
        assert CM11AStatusParser.format_device_bitmap(0x8001) == "1000000000000001"
        
        # No units
        assert CM11AStatusParser.format_device_bitmap(0) == "0000000000000000"


class TestCM11AInterfacePolling:
    """Test CM11A interface polling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = HeyuConfig()
        self.mock_serial = MockSerialInterface()
        self.mock_interface = CM11AInterface("/dev/ttyUSB0", mock_serial=self.mock_serial)
        self.mock_interface._is_connected = True  # Mock connection state
    
    def test_get_status_success(self):
        """Test successful status request."""
        # Mock 14-byte status response
        status_data = bytes([0x10, 0x00, 0x2D, 0x1E, 0x07, 0xA7, 0x08, 0x61,
                            0x01, 0x00, 0x02, 0x00, 0x00, 0x00])
        self.mock_serial.response_data = status_data
        
        result = self.mock_interface.get_status()
        
        assert result == status_data
        assert len(self.mock_interface._serial.written_data) > 0
        assert self.mock_interface._serial.written_data[0] == bytes([0x8B])  # Status request
    
    def test_check_for_poll_with_data(self):
        """Test poll checking when data is available."""
        # Mock poll request and subsequent data
        self.mock_serial.response_data = bytes([0x5A])  # Poll request
        self.mock_serial.poll_response = bytes([0x04, 0x06, 0x66, 0x02, 0x62])  # Mock X10 data
        
        # Simulate the full poll sequence
        poll_data = self.mock_interface.check_for_poll()
        
        # Should have written poll acknowledgment
        written_data = [data for data in self.mock_interface._serial.written_data]
        assert bytes([0xC3]) in written_data  # Poll acknowledgment
    
    def test_check_for_poll_no_data(self):
        """Test poll checking when no poll is available."""
        self.mock_serial.response_data = bytes()  # No data
        
        result = self.mock_interface.check_for_poll()
        
        assert result is None


class TestX10CommandsStatusPolling:
    """Test X10Commands status polling integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = HeyuConfig()
        self.mock_serial = MockSerialInterface()
        self.mock_interface = CM11AInterface("/dev/ttyUSB0", mock_serial=self.mock_serial)
        self.mock_interface._is_connected = True  # Mock connection state
        self.commands = X10Commands(self.config, self.mock_interface)
    
    def test_enhanced_readclock(self):
        """Test enhanced readclock with status parsing."""
        # Mock status response
        status_data = bytes([0x10, 0x00, 0x2D, 0x1E, 0x07, 0xA7, 0x08, 0x61,
                            0x01, 0x00, 0x02, 0x00, 0x00, 0x00])
        self.mock_serial.response_data = status_data
        
        result = self.commands.readclock()
        
        assert 'system_time' in result
        assert 'cm11a_time' in result
        assert 'status' in result
        assert 'battery_status' in result
        assert 'firmware_revision' in result
        assert 'house_code' in result
        
        assert result['firmware_revision'] == 1
        assert result['house_code'] == 'A'
    
    def test_enhanced_status(self):
        """Test enhanced status command with CM11A data."""
        # Mock status response
        status_data = bytes([0x10, 0x00, 0x2D, 0x1E, 0x07, 0xA7, 0x08, 0x61,
                            0x01, 0x00, 0x02, 0x00, 0x00, 0x00])
        self.mock_serial.response_data = status_data
        
        result = self.commands.status()
        
        assert result['serial_port'] == '/dev/ttyUSB0'
        assert 'supported_commands' in result
        assert 'cm11a_connected' in result
        
        if result['cm11a_connected']:
            assert 'battery_usage' in result
            assert 'firmware_revision' in result
            assert 'house_code' in result
    
    def test_poll_status_with_buffered_data(self):
        """Test poll_status when buffered data is available."""
        # Mock status and poll responses
        status_data = bytes([0x10, 0x00, 0x2D, 0x1E, 0x07, 0xA7, 0x08, 0x61,
                            0x01, 0x00, 0x02, 0x00, 0x00, 0x00])
        self.mock_serial.status_response = status_data
        self.mock_serial.response_data = status_data
        
        result = self.commands.poll_status(show_details=True)
        
        assert 'timestamp' in result
        assert 'buffered_data' in result
        assert 'status' in result
        
        if result['status']:
            assert 'battery_usage' in result['status']
            assert 'firmware_revision' in result['status']
    
    def test_monitor_powerline_no_activity(self):
        """Test powerline monitoring with no activity."""
        # Mock empty responses
        self.mock_serial.response_data = bytes()
        
        # Monitor for a very short time
        activities = self.commands.monitor_powerline(duration=1)
        
        assert isinstance(activities, list)
        assert len(activities) == 0
    
    def test_monitor_powerline_with_activity(self):
        """Test powerline monitoring with simulated activity."""
        # This would require more complex mocking to simulate timing
        # For now, just test the structure
        self.mock_serial.response_data = bytes()
        
        activities = self.commands.monitor_powerline(duration=1)
        
        assert isinstance(activities, list)
        # With no actual activity, should be empty
        assert len(activities) == 0


class TestStatusPollingEdgeCases:
    """Test edge cases in status polling."""
    
    def test_malformed_status_data(self):
        """Test handling of malformed status data."""
        # Test various malformed data scenarios
        with pytest.raises(ValueError):
            CM11AStatusParser.parse_status(bytes([1, 2, 3]))  # Too short
        
        with pytest.raises(ValueError):
            CM11AStatusParser.parse_status(bytes(range(20)))  # Too long
    
    def test_unknown_house_codes(self):
        """Test handling of unknown house codes in status."""
        # Status with invalid house code (using unmapped value)
        status_data = bytes([0x10, 0x00, 0x2D, 0x1E, 0x07, 0xA7, 0x08, 0x11,  # Invalid house code
                            0x01, 0x00, 0x02, 0x00, 0x00, 0x00])
        
        status = CM11AStatusParser.parse_status(status_data)
        assert status.house_code.startswith('?')  # Unknown house code
    
    def test_clock_decoding_edge_cases(self):
        """Test edge cases in CM11A clock decoding."""
        # Status with edge case time values
        status_data = bytes([0xFF, 0xFF, 59, 119, 11, 255, 255, 0x61,  # Max values with high bit set
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        status = CM11AStatusParser.parse_status(status_data)
        
        # Should handle extreme values gracefully
        assert status.seconds == 59
        assert status.minutes == 59  # 119 % 60
        assert status.hours == 23    # (11 * 2) + (119 // 60)
        assert status.day_of_year == 511  # 255 + ((255 & 0x80) >> 7) * 256 = 255 + 256
"""
CM11A Status Response Parsing

Handles parsing of the 14-byte status response from CM11A interface.
Based on original Heyu status.c implementation.
"""

from typing import Dict, Any, NamedTuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class CM11AStatus:
    """Parsed CM11A status information."""
    
    # Battery and hardware info
    battery_usage_minutes: int
    firmware_revision: int
    
    # Clock information
    seconds: int
    minutes: int
    hours: int
    day_of_year: int
    day_of_week_mask: int
    
    # Device monitoring
    house_code: str
    last_addressed_devices: int
    monitored_device_status: int
    dimmed_device_status: int
    
    # Raw data for debugging
    raw_data: bytes


class CM11AStatusParser:
    """Parser for CM11A 14-byte status response."""
    
    # House code mapping (same as protocol)
    HOUSE_CODE_MAP = {
        0x6: 'A', 0xE: 'B', 0x2: 'C', 0xA: 'D',
        0x1: 'E', 0x9: 'F', 0x5: 'G', 0xD: 'H',
        0x7: 'I', 0xF: 'J', 0x3: 'K', 0xB: 'L',
        0x0: 'M', 0x8: 'N', 0x4: 'O', 0xC: 'P'
    }
    
    @classmethod
    def parse_status(cls, status_data: bytes) -> CM11AStatus:
        """
        Parse 14-byte CM11A status response.
        
        Status format (from original Heyu):
        Byte 0-1: Battery usage timer (16-bit, minutes)
        Byte 2:   Seconds (0-59)
        Byte 3:   Minutes with hour overflow (0-119)
        Byte 4:   Hours/2 (0-11)
        Byte 5:   Day of year (low byte)
        Byte 6:   Day of year high bit + day of week mask
        Byte 7:   Firmware revision (low nibble) + house code (high nibble)
        Byte 8-9: Last addressed device bitmap (16-bit)
        Byte 10-11: Monitored device status (16-bit)
        Byte 12-13: Dimmed device status (16-bit)
        
        Args:
            status_data: 14-byte status response from CM11A
            
        Returns:
            Parsed CM11AStatus object
            
        Raises:
            ValueError: If status_data is not 14 bytes
        """
        if len(status_data) != 14:
            raise ValueError(f"Status data must be 14 bytes, got {len(status_data)}")
        
        # Battery usage (bytes 0-1, little endian)
        battery_minutes = status_data[0] | (status_data[1] << 8)
        
        # Clock information
        seconds = status_data[2] & 0xFF
        raw_minutes = status_data[3] & 0xFF
        minutes = raw_minutes % 60
        hours = ((status_data[4] & 0xFF) * 2) + (raw_minutes // 60)
        
        # Day of year calculation
        day_of_year = status_data[5] + (((status_data[6] & 0x80) >> 7) * 256)
        day_of_week_mask = status_data[6] & 0x7F
        
        # Hardware info
        firmware_revision = status_data[7] & 0x0F
        house_code_val = (status_data[7] & 0xF0) >> 4
        house_code = cls.HOUSE_CODE_MAP.get(house_code_val, f"?{house_code_val}")
        
        # Device status bitmaps (16-bit little endian)
        last_addressed = status_data[8] | (status_data[9] << 8)
        monitored_status = status_data[10] | (status_data[11] << 8)
        dimmed_status = status_data[12] | (status_data[13] << 8)
        
        return CM11AStatus(
            battery_usage_minutes=battery_minutes,
            firmware_revision=firmware_revision,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            day_of_year=day_of_year,
            day_of_week_mask=day_of_week_mask,
            house_code=house_code,
            last_addressed_devices=last_addressed,
            monitored_device_status=monitored_status,
            dimmed_device_status=dimmed_status,
            raw_data=status_data
        )
    
    @classmethod
    def format_battery_status(cls, battery_minutes: int) -> str:
        """
        Format battery usage for display.
        
        Args:
            battery_minutes: Battery usage in minutes
            
        Returns:
            Formatted battery status string
        """
        if battery_minutes == 0xFFFF:
            return "Unknown (cold restart)"
        
        hours = battery_minutes // 60
        minutes = battery_minutes % 60
        
        if battery_minutes > 2400:  # 40 hours
            return f"{hours}:{minutes:02d} (hh:mm) - REPLACE SOON"
        else:
            return f"{hours}:{minutes:02d} (hh:mm)"
    
    @classmethod
    def format_device_bitmap(cls, bitmap: int) -> str:
        """
        Format device bitmap for display.
        
        Args:
            bitmap: 16-bit device bitmap
            
        Returns:
            Binary string representation (units 16-1)
        """
        binary_str = ""
        for i in range(15, -1, -1):  # Units 16 down to 1
            binary_str += "1" if (bitmap & (1 << i)) else "0"
        return binary_str
    
    @classmethod
    def decode_cm11a_time(cls, status: CM11AStatus) -> datetime:
        """
        Decode CM11A time to datetime object.
        
        Note: This is a simplified version. The original Heyu has complex
        logic to handle leap years and timezone conversions.
        
        Args:
            status: Parsed CM11A status
            
        Returns:
            Approximate datetime representation
        """
        try:
            # Assume current year (simplified)
            current_year = datetime.now().year
            
            # Create datetime from day of year
            base_date = datetime(current_year, 1, 1)
            target_date = base_date.replace(
                month=1, day=1
            ) + timedelta(days=status.day_of_year - 1)
            
            # Add time components
            cm11a_time = target_date.replace(
                hour=status.hours,
                minute=status.minutes,
                second=status.seconds
            )
            
            return cm11a_time
            
        except (ValueError, OverflowError):
            # Return epoch if date is invalid
            return datetime.fromtimestamp(0)
    
    @classmethod
    def get_day_names_from_mask(cls, day_mask: int) -> list[str]:
        """
        Get day names from day of week mask.
        
        Args:
            day_mask: 7-bit day mask
            
        Returns:
            List of day names
        """
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 
                'Thursday', 'Friday', 'Saturday']
        
        active_days = []
        for i in range(7):
            if day_mask & (1 << i):
                active_days.append(days[i])
        
        return active_days


# Add missing import
from datetime import timedelta
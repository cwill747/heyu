"""High-level command controller for X10 devices."""

import logging
import time
import struct
from datetime import datetime
from typing import Optional, Dict, Any

from ..serial import CM11AInterface
from ..protocol import X10Protocol, X10Address, X10Command, HouseCode, ExtendedCommand
from ..config import HeyuConfig
from .exceptions import CommandError, DeviceNotFoundError, CommandExecutionError

logger = logging.getLogger(__name__)

class X10Commands:
    """High-level X10 device command controller."""
    
    def __init__(self, config: HeyuConfig, interface: Optional[CM11AInterface] = None):
        """
        Initialize command controller.
        
        Args:
            config: Heyu configuration
            interface: Optional CM11A interface (for testing)
        """
        self.config = config
        self.protocol = X10Protocol()
        self._interface = interface
    
    def _get_interface(self) -> CM11AInterface:
        """Get or create CM11A interface."""
        if self._interface is None:
            self._interface = CM11AInterface(self.config.tty)
        return self._interface
    
    def turn_on(self, address: str) -> bool:
        """
        Turn on an X10 device.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self._execute_command(address, X10Command.ON)
    
    def turn_off(self, address: str) -> bool:
        """
        Turn off an X10 device.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self._execute_command(address, X10Command.OFF)
    
    def dim(self, address: str, level: int) -> bool:
        """
        Dim an X10 device.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            level: Dim level (0-31, or percentage 0-100)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        # Convert percentage to X10 dim level if needed
        if level > 31:
            level = int(level * 31 / 100)
        
        return self._execute_command(address, X10Command.DIM, level)
    
    def brighten(self, address: str, level: int) -> bool:
        """
        Brighten an X10 device.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)  
            level: Bright level (0-31, or percentage 0-100)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        # Convert percentage to X10 bright level if needed
        if level > 31:
            level = int(level * 31 / 100)
        
        return self._execute_command(address, X10Command.BRIGHT, level)
    
    def all_lights_on(self, house_code: str) -> bool:
        """
        Turn on all lights for a house code.
        
        Args:
            house_code: House code (A-P)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        try:
            hc = HouseCode.from_string(house_code)
            command_bytes = self.protocol.encode_house_command(hc, X10Command.ALL_LIGHTS_ON)
            
            interface = self._get_interface()
            with interface:
                interface.send_command(command_bytes)
            
            logger.info(f"All lights on for house code {house_code}")
            return True
            
        except Exception as e:
            raise CommandExecutionError(f"Failed to execute all lights on: {e}")
    
    def all_lights_off(self, house_code: str) -> bool:
        """
        Turn off all lights for a house code.
        
        Args:
            house_code: House code (A-P)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        try:
            hc = HouseCode.from_string(house_code)
            command_bytes = self.protocol.encode_house_command(hc, X10Command.ALL_LIGHTS_OFF)
            
            interface = self._get_interface()
            with interface:
                interface.send_command(command_bytes)
            
            logger.info(f"All lights off for house code {house_code}")
            return True
            
        except Exception as e:
            raise CommandExecutionError(f"Failed to execute all lights off: {e}")
    
    def _execute_command(self, address: str, command: X10Command, data: int = 0) -> bool:
        """
        Execute a command on a device.
        
        Args:
            address: Device address or alias
            command: X10 command
            data: Optional command data
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        try:
            # Resolve alias to address
            resolved_address = self.config.resolve_address(address)
            
            # Parse X10 address
            x10_address = X10Address.from_string(resolved_address)
            
            # Encode command
            command_bytes = self.protocol.encode_address_command(x10_address, command, data)
            
            # Send command via interface
            interface = self._get_interface()
            with interface:
                response = interface.send_command(command_bytes)
            
            logger.info(f"Command {command.name} sent to {resolved_address} (alias: {address})")
            return True
            
        except Exception as e:
            error_msg = f"Failed to execute {command.name} on {address}: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(error_msg)
    
    def xpreset(self, address: str, level: int) -> bool:
        """
        Set extended preset dim level for an X10 device.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            level: Preset level (0-31, or percentage 0-100)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        # Convert percentage to X10 dim level if needed
        if level > 31:
            level = int(level * 31 / 100)
        
        return self._execute_extended_command(address, ExtendedCommand.EXTENDED_PRESET, level)
    
    def xdim(self, address: str, level: int) -> bool:
        """
        Extended dim command (alias for xpreset).
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            level: Dim level (0-31, or percentage 0-100)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self.xpreset(address, level)
    
    def xon(self, address: str) -> bool:
        """
        Extended full on command for advanced X10 devices.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self._execute_extended_command(address, ExtendedCommand.EXTENDED_FULL_ON)
    
    def xoff(self, address: str) -> bool:
        """
        Extended full off command for advanced X10 devices.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self._execute_extended_command(address, ExtendedCommand.EXTENDED_FULL_OFF)
    
    def xstatus(self, address: str) -> bool:
        """
        Extended status request for advanced X10 devices.
        
        Args:
            address: Device address (e.g., 'A1' or alias name)
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        return self._execute_extended_command(address, ExtendedCommand.EXTENDED_STATUS)
    
    def _execute_extended_command(self, address: str, extended_command: ExtendedCommand, 
                                data: int = 0) -> bool:
        """
        Execute an extended command on a device.
        
        Args:
            address: Device address or alias
            extended_command: Extended X10 command
            data: Optional command data
            
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        try:
            # Resolve alias to address
            resolved_address = self.config.resolve_address(address)
            
            # Parse X10 address
            x10_address = X10Address.from_string(resolved_address)
            
            # Encode extended command
            command_bytes = self.protocol.encode_extended_command(x10_address, extended_command, data)
            
            # Send command via interface
            interface = self._get_interface()
            with interface:
                response = interface.send_command(command_bytes)
            
            logger.info(f"Extended command {extended_command.name} sent to {resolved_address} (alias: {address})")
            return True
            
        except Exception as e:
            error_msg = f"Failed to execute {extended_command.name} on {address}: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(error_msg)
    
    def setclock(self) -> bool:
        """
        Set CM11A clock to current system time.
        
        The CM11A has an internal clock that needs to be synchronized
        with the system clock for proper timer and macro operation.
        
        Returns:
            True if successful
            
        Raises:
            CommandError: If command fails
        """
        try:
            # Get current system time
            now = datetime.now()
            
            # Convert to CM11A clock format  
            # Based on original Heyu setclock.c implementation
            clock_data = self._encode_clock_data(now)
            
            # Send clock set command to CM11A
            interface = self._get_interface()
            with interface:
                response = interface.send_command(clock_data)
            
            logger.info(f"CM11A clock set to {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to set CM11A clock: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(error_msg)
    
    def readclock(self) -> Dict[str, Any]:
        """
        Read current time from CM11A and compare with system time.
        
        Returns:
            Dictionary containing CM11A time, system time, and comparison
            
        Raises:
            CommandError: If command fails
        """
        try:
            # Send status request to get clock info
            # The CM11A status includes current time information
            interface = self._get_interface()
            
            # Status request command (0x8B)
            status_cmd = bytes([0x8B])
            
            with interface:
                response = interface.send_command(status_cmd)
                # Read status response (typically 14 bytes)
                status_data = interface.read_response(14)
            
            # Decode the clock information from status response
            # Note: This is a simplified version - full implementation would 
            # need to properly decode the CM11A status format
            system_time = datetime.now()
            
            result = {
                'system_time': system_time.strftime('%Y-%m-%d %H:%M:%S'),
                'cm11a_time': 'Clock reading not fully implemented',
                'status': 'Basic status request sent',
                'raw_response': status_data.hex() if status_data else 'No response'
            }
            
            logger.info(f"Clock status retrieved: {result['status']}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to read CM11A clock: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(error_msg)
    
    def _encode_clock_data(self, dt: datetime) -> bytes:
        """
        Encode datetime into CM11A clock format.
        
        Based on original Heyu setclock implementation:
        - Byte 0: 0x9B (timer download code)
        - Byte 1: seconds (0-59)
        - Byte 2: minutes + (hour%2)*60 (0-119) 
        - Byte 3: hour/2 (0-11)
        - Byte 4: day of year % 256
        - Byte 5: (day of year / 256) << 7 | day of week mask
        - Byte 6: housecode << 4 | clear flag
        
        Args:
            dt: Datetime to encode
            
        Returns:
            7-byte clock data for CM11A
        """
        # Calculate day of year (1-366)
        day_of_year = dt.timetuple().tm_yday
        
        # Day of week mask (bit position for day: 0=Sun, 1=Mon, etc.)
        day_mask = 1 << dt.weekday() if dt.weekday() < 6 else 1  # Monday=0 in weekday()
        
        # Default housecode A (0x6)
        housecode = 0x6
        
        clock_data = [
            0x9B,                                           # Timer download code
            dt.second,                                      # Seconds (0-59)
            dt.minute + ((dt.hour % 2) * 60),              # Minutes 0-119
            dt.hour // 2,                                   # Hour/2 (0-11) 
            day_of_year % 256,                             # Day of year mantissa
            ((day_of_year // 256) << 7) | day_mask,       # Day of year radix + day mask
            (housecode << 4) | 0                           # Housecode + clear flag
        ]
        
        return bytes(clock_data)
    
    def status(self) -> dict:
        """
        Get system status information.
        
        Returns:
            Dictionary with status information
        """
        interface = self._get_interface()
        
        return {
            'serial_port': self.config.tty,
            'connected': interface.is_connected() if hasattr(interface, 'is_connected') else False,
            'aliases_count': len(self.config.aliases),
            'supported_commands': self.protocol.get_supported_commands()
        }
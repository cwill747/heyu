"""High-level command controller for X10 devices."""

import logging
from typing import Optional

from ..serial import CM11AInterface
from ..protocol import X10Protocol, X10Address, X10Command, HouseCode
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
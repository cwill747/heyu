"""
X10 Protocol Implementation

This module handles the X10 home automation protocol encoding and decoding.
It converts high-level commands (like "turn on A1") into the low-level
byte sequences required by the CM11A interface.
"""

import logging
from enum import Enum, IntEnum
from typing import List, Tuple, Union
from dataclasses import dataclass

from .exceptions import ProtocolError, InvalidAddressError, InvalidCommandError, EncodingError

logger = logging.getLogger(__name__)

class HouseCode(Enum):
    """X10 House codes A-P with their corresponding binary values."""
    A = 0x06
    B = 0x0E 
    C = 0x02
    D = 0x0A
    E = 0x01
    F = 0x09
    G = 0x05
    H = 0x0D
    I = 0x07
    J = 0x0F
    K = 0x03
    L = 0x0B
    M = 0x00
    N = 0x08
    O = 0x04
    P = 0x0C
    
    @classmethod
    def from_string(cls, code: str) -> 'HouseCode':
        """Convert string to HouseCode."""
        code = code.upper()
        if code not in cls.__members__:
            raise InvalidAddressError(f"Invalid house code: {code}. Must be A-P.")
        return cls[code]

class UnitCode(IntEnum):
    """X10 Unit codes 1-16 with their corresponding binary values."""
    UNIT_1 = 0x06
    UNIT_2 = 0x0E
    UNIT_3 = 0x02
    UNIT_4 = 0x0A
    UNIT_5 = 0x01
    UNIT_6 = 0x09
    UNIT_7 = 0x05
    UNIT_8 = 0x0D
    UNIT_9 = 0x07
    UNIT_10 = 0x0F
    UNIT_11 = 0x03
    UNIT_12 = 0x0B
    UNIT_13 = 0x00
    UNIT_14 = 0x08
    UNIT_15 = 0x04
    UNIT_16 = 0x0C
    
    @classmethod
    def from_int(cls, unit: int) -> 'UnitCode':
        """Convert integer (1-16) to UnitCode."""
        if not 1 <= unit <= 16:
            raise InvalidAddressError(f"Invalid unit code: {unit}. Must be 1-16.")
        return cls[f"UNIT_{unit}"]
    
    def to_int(self) -> int:
        """Convert UnitCode back to integer (1-16)."""
        return int(self.name.split('_')[1])

class X10Command(IntEnum):
    """X10 function codes."""
    ALL_UNITS_OFF = 0x00
    ALL_LIGHTS_ON = 0x01
    ON = 0x02
    OFF = 0x03
    DIM = 0x04
    BRIGHT = 0x05
    ALL_LIGHTS_OFF = 0x06
    EXTENDED_CODE = 0x07
    HAIL_REQUEST = 0x08
    HAIL_ACKNOWLEDGE = 0x09
    PRESET_DIM_1 = 0x0A
    PRESET_DIM_2 = 0x0B
    EXTENDED_DATA = 0x0C
    STATUS_ON = 0x0D
    STATUS_OFF = 0x0E
    STATUS_REQUEST = 0x0F

@dataclass
class X10Address:
    """Represents an X10 address (house code + unit code)."""
    house_code: HouseCode
    unit_code: UnitCode
    
    @classmethod
    def from_string(cls, address: str) -> 'X10Address':
        """
        Parse X10 address from string format like 'A1', 'B16', etc.
        
        Args:
            address: String address (e.g., 'A1', 'K16')
            
        Returns:
            X10Address object
            
        Raises:
            InvalidAddressError: If address format is invalid
        """
        address = address.upper().strip()
        
        if len(address) < 2:
            raise InvalidAddressError(f"Invalid address format: {address}")
        
        house_char = address[0]
        unit_str = address[1:]
        
        try:
            house_code = HouseCode.from_string(house_char)
        except InvalidAddressError:
            raise InvalidAddressError(f"Invalid house code in address: {address}")
        
        try:
            unit_num = int(unit_str)
            unit_code = UnitCode.from_int(unit_num)
        except ValueError:
            raise InvalidAddressError(f"Invalid unit number in address: {address}")
        except InvalidAddressError:
            raise InvalidAddressError(f"Invalid unit code in address: {address}")
        
        return cls(house_code, unit_code)
    
    def __str__(self) -> str:
        """String representation like 'A1'."""
        return f"{self.house_code.name}{self.unit_code.to_int()}"

class X10Protocol:
    """
    X10 Protocol handler for encoding/decoding commands.
    
    This class converts high-level X10 commands into the byte sequences
    required by the CM11A interface and vice versa.
    """
    
    def __init__(self):
        """Initialize X10 protocol handler."""
        pass
    
    def encode_address_command(self, address: X10Address, command: X10Command, 
                             data: int = 0) -> bytes:
        """
        Encode an X10 address + command into CM11A format.
        
        The CM11A expects commands in this format:
        - Header byte (0x04 for address + function)
        - Address byte (house code + unit code)
        - Function byte (house code + function code)
        - Optional data byte for DIM/BRIGHT commands
        
        Args:
            address: X10 address
            command: X10 command
            data: Optional data byte (for DIM/BRIGHT commands, 0-31)
            
        Returns:
            Encoded bytes for CM11A
            
        Raises:
            EncodingError: If encoding fails
        """
        try:
            if command in (X10Command.DIM, X10Command.BRIGHT):
                # DIM/BRIGHT commands need data byte
                if not 0 <= data <= 31:
                    raise EncodingError(f"DIM/BRIGHT data must be 0-31, got {data}")
                
                # Encode as: header, address, function, data
                header = 0x06  # 4 bytes + dim data
                address_byte = (address.house_code.value << 4) | address.unit_code.value
                function_byte = (address.house_code.value << 4) | command.value
                data_byte = data
                
                return bytes([header, address_byte, function_byte, data_byte])
            else:
                # Regular commands
                header = 0x04  # 2 bytes  
                address_byte = (address.house_code.value << 4) | address.unit_code.value
                function_byte = (address.house_code.value << 4) | command.value
                
                return bytes([header, address_byte, function_byte])
                
        except Exception as e:
            raise EncodingError(f"Failed to encode command: {e}")
    
    def encode_house_command(self, house_code: HouseCode, command: X10Command) -> bytes:
        """
        Encode a house-level command (like ALL_LIGHTS_ON).
        
        Args:
            house_code: House code
            command: House-level command
            
        Returns:
            Encoded bytes for CM11A
            
        Raises:
            EncodingError: If encoding fails
        """
        try:
            header = 0x02  # House command
            function_byte = (house_code.value << 4) | command.value
            return bytes([header, function_byte])
        except Exception as e:
            raise EncodingError(f"Failed to encode house command: {e}")
    
    def decode_response(self, data: bytes) -> dict:
        """
        Decode a response from CM11A.
        
        Args:
            data: Response bytes from CM11A
            
        Returns:
            Dictionary with decoded information
            
        Raises:
            ProtocolError: If decoding fails
        """
        if not data:
            raise ProtocolError("Empty response data")
        
        # For now, just return basic status
        # This would be expanded based on CM11A response formats
        return {
            'raw_data': data.hex(),
            'length': len(data),
            'status': 'received'
        }
    
    def validate_address(self, address_str: str) -> bool:
        """
        Validate an X10 address string.
        
        Args:
            address_str: Address string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            X10Address.from_string(address_str)
            return True
        except InvalidAddressError:
            return False
    
    def get_supported_commands(self) -> List[str]:
        """
        Get list of supported X10 commands.
        
        Returns:
            List of command names
        """
        return [cmd.name.lower() for cmd in X10Command]
    
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum for X10 data.
        
        Args:
            data: Data bytes
            
        Returns:
            Checksum value (0-255)
        """
        return sum(data) & 0xFF
    
    def __repr__(self) -> str:
        """String representation."""
        return "X10Protocol()"
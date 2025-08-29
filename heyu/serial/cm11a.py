"""
CM11A Interface Module

Handles low-level serial communication with the X10 CM11A computer interface.
This module provides a clean, testable interface for sending and receiving
X10 commands through the serial port.
"""

import time
import logging
from typing import Optional, List, Protocol
from abc import ABC, abstractmethod

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

from .exceptions import SerialError, CM11AError, TimeoutError, ChecksumError

logger = logging.getLogger(__name__)

class SerialInterface(Protocol):
    """Protocol for serial port interface - allows for easy mocking."""
    
    def write(self, data: bytes) -> int:
        """Write data to serial port."""
        ...
    
    def read(self, size: int = 1) -> bytes:
        """Read data from serial port.""" 
        ...
    
    def in_waiting(self) -> int:
        """Get number of bytes in input buffer."""
        ...
    
    def close(self) -> None:
        """Close serial port."""
        ...

class CM11AInterface:
    """
    Interface for communicating with X10 CM11A computer interface.
    
    The CM11A uses a specific protocol for communication:
    - Commands are sent as byte sequences
    - Responses include checksums for validation
    - Timeouts are used to detect communication failures
    """
    
    DEFAULT_TIMEOUT = 10.0  # seconds
    CHECKSUM_REQUEST = 0x55
    READY_FLAG = 0x55
    
    def __init__(self, port: str, timeout: float = DEFAULT_TIMEOUT, mock_serial: Optional[SerialInterface] = None):
        """
        Initialize CM11A interface.
        
        Args:
            port: Serial port path (e.g., "/dev/ttyUSB0")
            timeout: Communication timeout in seconds
            mock_serial: Mock serial interface for testing
        """
        self.port = port
        self.timeout = timeout
        self._serial: Optional[SerialInterface] = mock_serial
        self._is_connected = False
        
        if serial is None and mock_serial is None:
            raise SerialError("pyserial not available and no mock provided")
    
    def connect(self) -> None:
        """
        Connect to the CM11A interface.
        
        Raises:
            SerialError: If connection fails
            CM11AError: If CM11A doesn't respond properly
        """
        if self._serial is not None:
            # Already have a serial interface (likely mock)
            self._is_connected = True
            return
            
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=4800,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=self.timeout,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Test connection by requesting interface status
            self._test_connection()
            self._is_connected = True
            logger.info(f"Connected to CM11A on {self.port}")
            
        except serial.SerialException as e:
            raise SerialError(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from CM11A interface."""
        if self._serial:
            self._serial.close()
            self._serial = None
        self._is_connected = False
        logger.info("Disconnected from CM11A")
    
    def is_connected(self) -> bool:
        """Check if connected to CM11A."""
        return self._is_connected
    
    def _test_connection(self) -> None:
        """
        Test connection by sending a status request.
        
        Raises:
            CM11AError: If CM11A doesn't respond properly
        """
        if not self._serial:
            raise SerialError("Not connected")
        
        # Send status request (0x8B)
        try:
            self._serial.write(bytes([0x8B]))
            
            # Wait for response
            response = self._read_with_timeout(1)
            if not response:
                raise CM11AError("No response to status request")
                
            logger.debug(f"CM11A status response: 0x{response[0]:02X}")
            
        except Exception as e:
            raise CM11AError(f"Connection test failed: {e}")
    
    def send_command(self, command: bytes) -> bytes:
        """
        Send a command to CM11A and return response.
        
        Args:
            command: Command bytes to send
            
        Returns:
            Response bytes from CM11A
            
        Raises:
            SerialError: If not connected or communication fails
            ChecksumError: If checksum validation fails
            TimeoutError: If timeout occurs
        """
        if not self._is_connected or not self._serial:
            raise SerialError("Not connected to CM11A")
        
        logger.debug(f"Sending command: {command.hex()}")
        
        try:
            # Send command
            self._serial.write(command)
            
            # Wait for checksum request
            checksum_req = self._read_with_timeout(1)
            if not checksum_req or checksum_req[0] != self.CHECKSUM_REQUEST:
                raise CM11AError(f"Expected checksum request, got: {checksum_req.hex() if checksum_req else 'nothing'}")
            
            # Calculate and send checksum
            checksum = sum(command) & 0xFF
            self._serial.write(bytes([checksum]))
            
            # Wait for ready flag
            ready = self._read_with_timeout(1)
            if not ready or ready[0] != self.READY_FLAG:
                raise CM11AError(f"Expected ready flag, got: {ready.hex() if ready else 'nothing'}")
            
            logger.debug("Command sent successfully")
            return ready
            
        except Exception as e:
            if isinstance(e, (SerialError, CM11AError, TimeoutError)):
                raise
            raise SerialError(f"Command send failed: {e}")
    
    def read_response(self, expected_length: int = 1) -> bytes:
        """
        Read response from CM11A.
        
        Args:
            expected_length: Number of bytes expected
            
        Returns:
            Response bytes
            
        Raises:
            TimeoutError: If timeout occurs
            SerialError: If read fails
        """
        if not self._is_connected or not self._serial:
            raise SerialError("Not connected to CM11A")
        
        return self._read_with_timeout(expected_length)
    
    def _read_with_timeout(self, num_bytes: int) -> bytes:
        """
        Read bytes with timeout handling.
        
        Args:
            num_bytes: Number of bytes to read
            
        Returns:
            Bytes read
            
        Raises:
            TimeoutError: If timeout occurs
        """
        if not self._serial:
            raise SerialError("Not connected")
        
        start_time = time.time()
        data = b""
        
        while len(data) < num_bytes:
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Timeout reading {num_bytes} bytes (got {len(data)})")
            
            try:
                chunk = self._serial.read(num_bytes - len(data))
                if chunk:
                    data += chunk
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                raise SerialError(f"Read failed: {e}")
        
        logger.debug(f"Read {len(data)} bytes: {data.hex()}")
        return data
    
    @staticmethod
    def list_serial_ports() -> List[str]:
        """
        List available serial ports.
        
        Returns:
            List of serial port paths
        """
        if serial is None:
            return []
        
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        
        return sorted(ports)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._is_connected else "disconnected"
        return f"CM11AInterface(port='{self.port}', status='{status}')"
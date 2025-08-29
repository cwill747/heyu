"""Exception classes for serial communication."""

class SerialError(Exception):
    """Base exception for serial communication errors."""
    pass

class CM11AError(SerialError):
    """Exception for CM11A specific errors."""
    pass

class TimeoutError(SerialError):
    """Exception for communication timeouts.""" 
    pass

class ChecksumError(SerialError):
    """Exception for checksum validation failures."""
    pass
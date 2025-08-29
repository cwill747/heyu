"""Exception classes for X10 protocol handling."""

class ProtocolError(Exception):
    """Base exception for X10 protocol errors."""
    pass

class InvalidAddressError(ProtocolError):
    """Exception for invalid X10 addresses.""" 
    pass

class InvalidCommandError(ProtocolError):
    """Exception for invalid X10 commands."""
    pass

class EncodingError(ProtocolError):
    """Exception for X10 encoding errors."""
    pass
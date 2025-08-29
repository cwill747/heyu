"""Exception classes for command handling."""

class CommandError(Exception):
    """Base exception for command errors."""
    pass

class DeviceNotFoundError(CommandError):
    """Exception when device is not found."""
    pass

class CommandExecutionError(CommandError):
    """Exception when command execution fails."""
    pass
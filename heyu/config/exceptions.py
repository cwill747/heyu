"""Configuration exception classes."""

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass

class ConfigFileNotFound(ConfigError):
    """Exception when configuration file is not found."""
    pass

class ConfigParseError(ConfigError):
    """Exception when configuration file cannot be parsed."""
    pass
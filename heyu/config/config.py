"""Configuration management for Heyu."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .exceptions import ConfigError, ConfigFileNotFound, ConfigParseError

@dataclass
class HeyuConfig:
    """Heyu configuration management."""
    
    # Serial port configuration
    tty: str = "/dev/ttyUSB0"
    
    # Device aliases
    aliases: Dict[str, str] = field(default_factory=dict)
    
    # Directories
    config_dir: Optional[Path] = None
    spool_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize default paths after object creation."""
        if self.config_dir is None:
            self.config_dir = Path.home() / ".heyu"
        if self.spool_dir is None:
            self.spool_dir = Path("/var/tmp/heyu")
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'HeyuConfig':
        """Load configuration from file."""
        config = cls()
        
        if config_path is None:
            config_path = config.config_dir / "x10config"
        
        if not config_path.exists():
            # Create default config
            config.create_default_config(config_path)
            return config
        
        try:
            config._parse_config_file(config_path)
        except Exception as e:
            raise ConfigParseError(f"Failed to parse {config_path}: {e}")
        
        return config
    
    def _parse_config_file(self, config_path: Path) -> None:
        """Parse configuration file."""
        lines = config_path.read_text().splitlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
            
            directive = parts[0].upper()
            
            if directive == 'TTY':
                self.tty = parts[1]
            elif directive == 'ALIAS':
                if len(parts) >= 3:
                    alias_name = parts[1]
                    address = parts[2]
                    self.aliases[alias_name] = address
    
    def create_default_config(self, config_path: Path) -> None:
        """Create default configuration file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_content = """# Heyu Configuration File
# Generated automatically

# TTY - Serial port for CM11A interface
TTY /dev/ttyUSB0

# Device aliases
ALIAS living_room A1
ALIAS bedroom A2
ALIAS kitchen A3
ALIAS porch_light B1
ALIAS garage_door B2
"""
        
        config_path.write_text(default_content)
    
    def resolve_address(self, address: str) -> str:
        """Resolve alias to actual address."""
        return self.aliases.get(address, address)
    
    def add_alias(self, alias: str, address: str) -> None:
        """Add device alias."""
        self.aliases[alias] = address
    
    def remove_alias(self, alias: str) -> None:
        """Remove device alias."""
        if alias in self.aliases:
            del self.aliases[alias]
    
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = self.config_dir / "x10config"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "# Heyu Configuration File",
            "",
            f"# TTY - Serial port for CM11A interface", 
            f"TTY {self.tty}",
            "",
            "# Device aliases"
        ]
        
        for alias, address in sorted(self.aliases.items()):
            lines.append(f"ALIAS {alias} {address}")
        
        lines.append("")  # Final newline
        
        config_path.write_text('\n'.join(lines))
    
    def __repr__(self) -> str:
        """String representation."""
        return f"HeyuConfig(tty='{self.tty}', aliases={len(self.aliases)})"
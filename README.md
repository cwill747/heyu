# Heyu - Python Implementation

A modern Python port of the original Heyu X10 home automation controller.

## Overview

Heyu is a command-line program for controlling X10 home automation devices through a CM11A computer interface. This Python implementation maintains compatibility with the original Heyu command structure while providing modern, testable, and modular code.

## Features

- **Modular Architecture**: Separate modules for serial communication, protocol handling, configuration, and commands
- **Full Test Coverage**: Comprehensive unit and integration tests
- **Modern Python**: Uses type hints, dataclasses, and modern Python best practices  
- **CLI Compatibility**: Maintains the same command structure as original Heyu
- **Easy Installation**: Simple pip/uv installation with minimal dependencies

## Quick Start

### Installation

Using uv (recommended):
```bash
git clone <repo>
cd heyu
nix develop  # Enter development environment
uv sync      # Install dependencies
```

### Basic Usage

```bash
# Show system information
uv run heyu info

# Turn devices on/off
uv run heyu on A1
uv run heyu off A1

# Dim/brighten devices  
uv run heyu dim A1 50
uv run heyu bright A1 75

# House-level commands
uv run heyu alllightson A
uv run heyu alllightsoff A
```

### Configuration

Configuration file: `~/.heyu/x10config`

```
# Serial port for CM11A interface
TTY /dev/ttyUSB0

# Device aliases
ALIAS living_room A1
ALIAS bedroom A2
ALIAS kitchen A3
```

## Development

This project uses:
- **uv** for dependency management
- **pytest** for testing
- **black** for code formatting
- **mypy** for type checking
- **nix** for development environment

```bash
# Run tests
uv run pytest

# Format code
uv run black .

# Type check
uv run mypy heyu/
```

## Architecture

- `heyu/serial/` - CM11A serial communication
- `heyu/protocol/` - X10 protocol encoding/decoding  
- `heyu/config/` - Configuration file handling
- `heyu/commands/` - High-level device commands
- `heyu/cli/` - Command-line interface

## License

GPL-3.0+, same as the original Heyu program.

## Credits

Original Heyu by Daniel B. Suthers and Charles W. Sullivan.
Python port maintains the same functionality and command structure.
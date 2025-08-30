# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python port of the original Heyu X10 home automation controller (written in C). The Python version implements ~15-20% of the original functionality, focusing on basic X10 device control with a modern, testable, modular architecture. The project serves as a foundation for systematic expansion to match the full feature set of the original.

## Development Environment Setup

This project uses **Nix flakes** for reproducible development environments:

```bash
# Enter development environment (provides uv, Python 3.11, and all tools)
nix develop

# Install dependencies  
uv sync

# Run the application
uv run heyu info
```

The Nix environment provides UV, Python 3.11, pytest, black, mypy, and other development tools pre-configured.

## Core Commands

### Essential Development Commands
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_protocol.py -v

# Run single test method
uv run pytest tests/unit/test_protocol.py::TestX10Protocol::test_encode_address_command_basic -v

# Basic functionality test (standalone, no pytest required)
uv run python test_basic.py

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy heyu/

# Run the CLI
uv run heyu --help
uv run heyu info
uv run heyu on A1    # Will fail without CM11A hardware
```

### Package Management
```bash
# Sync dependencies from lock file
uv sync

# Add new dependency
uv add <package>

# Add development dependency  
uv add --dev <package>

# Update dependencies
uv lock --upgrade
```

## Architecture Overview

The codebase follows a **layered modular architecture** with clear separation of concerns:

### Core Architecture Layers

1. **CLI Layer** (`heyu/cli/`)
   - Click-based command-line interface
   - Entry point: `heyu/cli/main.py` 
   - Maintains CLI compatibility with original C version
   - Orchestrates calls to lower layers

2. **Commands Layer** (`heyu/commands/`)
   - High-level device control logic (`controller.py`)
   - Bridges CLI requests to protocol/serial layers
   - Main class: `X10Commands` - handles device operations
   - Error handling and logging for user operations

3. **Protocol Layer** (`heyu/protocol/`)
   - X10 protocol encoding/decoding (`x10.py`)
   - Address parsing (house codes A-P, units 1-16)
   - Command encoding for CM11A interface
   - Key classes: `X10Protocol`, `X10Address`, `HouseCode`, `UnitCode`

4. **Serial Layer** (`heyu/serial/`)
   - CM11A hardware interface (`cm11a.py`)
   - Serial communication with checksums and timeouts
   - Mock-friendly design for testing
   - Main class: `CM11AInterface` - handles low-level communication

5. **Configuration Layer** (`heyu/config/`)
   - Configuration file parsing (`config.py`)
   - Device alias management
   - Settings: serial port, device aliases, directories
   - Main class: `HeyuConfig`

### Data Flow
```
CLI command → X10Commands → X10Protocol → CM11AInterface → Serial Port
                ↕              ↕              ↕
            HeyuConfig    Address/Command   Hardware
                         Encoding/Decode   Communication
```

### Key Design Patterns

- **Dependency Injection**: All layers accept interfaces/mocks for testing
- **Protocol Pattern**: Serial interface is abstracted for easy mocking
- **Command Pattern**: Commands are encoded as data structures before transmission  
- **Factory Pattern**: Address and command objects created via class methods
- **Context Manager**: CM11A interface supports `with` statements for resource management

## Testing Strategy

### Test Structure
- `tests/unit/` - Fast unit tests for individual components
- `tests/integration/` - Integration tests with mocked hardware  
- `test_basic.py` - Standalone smoke tests for rapid validation

### Test Execution Patterns
```bash
# Full test suite with coverage report
uv run pytest

# Fast smoke test (no pytest dependency)
uv run python test_basic.py

# Test specific layer
uv run pytest tests/unit/test_protocol.py

# Test with verbose output
uv run pytest tests/unit/test_protocol.py -v -s
```

### Mocking Approach
- Serial communication is mocked via `SerialInterface` protocol
- Hardware-specific tests use `mock_serial` parameter in `CM11AInterface`
- Commands can be tested without actual CM11A hardware

## Key Implementation Details

### X10 Protocol Specifics
- House codes A-P map to specific 4-bit values (not sequential)
- Unit codes 1-16 also map to specific 4-bit values (not sequential)
- CM11A expects specific byte sequences with checksums
- Commands require address byte followed by function byte

### Serial Communication
- CM11A uses 4800 baud, 8N1 serial configuration
- Implements checksum validation and timeout handling
- Status polling and acknowledgment patterns for reliability

### Configuration Management  
- Config file: `~/.heyu/x10config` (compatible with original)
- Supports device aliases (e.g., `living_room` → `A1`)
- Automatic creation of default configuration

### Error Handling Philosophy
- Graceful degradation when hardware unavailable
- Comprehensive error messages for user guidance  
- Logging integration for debugging support

## Extending Functionality

### Current Limitations (See TODO.md)
The Python port implements only basic X10 functionality. The original C version has 80+ additional commands, daemon architecture, RF sensor support, scheduling system, and more. 

### Adding New Commands
1. Add command definition to `heyu/protocol/x10.py` (`X10Command` enum)
2. Implement encoding logic in `X10Protocol.encode_*` methods  
3. Add high-level method to `X10Commands` class
4. Add CLI command to `heyu/cli/main.py`
5. Write comprehensive tests

### Adding Hardware Support
1. Create new interface class following `CM11AInterface` pattern
2. Implement protocol-specific communication in new module
3. Update `X10Commands` to support multiple interfaces
4. Add configuration options and CLI parameters

### Module Integration Patterns
- Each module has `__init__.py` with explicit `__all__` exports
- Exceptions are defined in separate `exceptions.py` files  
- Type hints are mandatory for all public interfaces
- Dataclasses preferred for structured data

## Original Heyu Context

This repository contains both the **original C source code** (root level .c/.h files) and the **new Python implementation** (heyu/ directory). The C code serves as reference for understanding the full X10 protocol implementation and identifies missing functionality in the Python port.

Key reference files:
- `cmd.c` - Complete command definitions and implementations
- `x10.h` - X10 protocol constants and structures  
- `process.h` - Daemon architecture and state management
- `TODO.md` - Comprehensive gap analysis and development roadmap

The Python port prioritizes modern software engineering practices (testability, modularity, type safety) while maintaining CLI compatibility for basic X10 operations.
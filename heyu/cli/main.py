#!/usr/bin/env python3
"""
Main CLI entry point for Heyu.

This provides a command-line interface that mimics the original Heyu
functionality while using the new modular Python architecture.
"""

import sys
import logging
from typing import Optional
from pathlib import Path

import click

from .. import __version__
from ..config import HeyuConfig, ConfigError
from ..commands import X10Commands, CommandError
from ..serial import SerialError
from ..protocol.exceptions import InvalidAddressError

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(name)s: %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)

@click.group(invoke_without_command=True)
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-c', '--config', type=click.Path(), help='Configuration file path')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: Optional[str]):
    """Heyu - X10 Home Automation Control (Python Implementation)"""
    
    # Set up logging level
    if verbose:
        logging.getLogger('heyu').setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.INFO)
    
    # Load configuration
    try:
        config_path = Path(config) if config else None
        heyu_config = HeyuConfig.load_from_file(config_path)
    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Initialize commands controller
    commands = X10Commands(heyu_config)
    
    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config'] = heyu_config
    ctx.obj['commands'] = commands
    ctx.obj['verbose'] = verbose
    
    # If no subcommand, show version and basic usage
    if ctx.invoked_subcommand is None:
        click.echo(f"Heyu version {__version__} (Python implementation)")
        click.echo("Usage: heyu [OPTIONS] COMMAND [ARGS]...")
        click.echo("Try 'heyu --help' for more information.")

@cli.command()
@click.pass_context
def info(ctx: click.Context):
    """Display system information."""
    config = ctx.obj['config']
    commands = ctx.obj['commands']
    
    click.echo(f"Heyu version {__version__} (Python implementation)")
    click.echo(f"Configuration directory: {config.config_dir}")
    click.echo(f"Spool directory: {config.spool_dir}")
    click.echo(f"Serial port: {config.tty}")
    
    # Check serial port existence
    if Path(config.tty).exists():
        click.echo(f"Serial port {config.tty}: OK")
    else:
        click.echo(f"Serial port {config.tty}: NOT FOUND", err=True)
    
    # Show aliases
    if config.aliases:
        click.echo(f"\nDevice aliases ({len(config.aliases)}):")
        for alias, address in sorted(config.aliases.items()):
            click.echo(f"  {alias:15} -> {address}")
    else:
        click.echo("\nNo device aliases configured.")

@cli.command()
@click.argument('address')
@click.pass_context  
def on(ctx: click.Context, address: str):
    """Turn device ON."""
    commands = ctx.obj['commands']
    
    try:
        if commands.turn_on(address):
            click.echo(f"Turned on {address}")
        else:
            click.echo(f"Failed to turn on {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.pass_context
def off(ctx: click.Context, address: str):
    """Turn device OFF."""
    commands = ctx.obj['commands']
    
    try:
        if commands.turn_off(address):
            click.echo(f"Turned off {address}")
        else:
            click.echo(f"Failed to turn off {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.argument('level', type=int)
@click.pass_context
def dim(ctx: click.Context, address: str, level: int):
    """Dim device to specified level (0-31 or 0-100%)."""
    commands = ctx.obj['commands']
    
    try:
        if commands.dim(address, level):
            click.echo(f"Dimmed {address} to level {level}")
        else:
            click.echo(f"Failed to dim {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.argument('level', type=int)  
@click.pass_context
def bright(ctx: click.Context, address: str, level: int):
    """Brighten device to specified level (0-31 or 0-100%)."""
    commands = ctx.obj['commands']
    
    try:
        if commands.brighten(address, level):
            click.echo(f"Brightened {address} to level {level}")
        else:
            click.echo(f"Failed to brighten {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('house_code')
@click.pass_context
def alllightson(ctx: click.Context, house_code: str):
    """Turn on all lights for house code."""
    commands = ctx.obj['commands']
    
    try:
        if commands.all_lights_on(house_code):
            click.echo(f"All lights on for house {house_code}")
        else:
            click.echo(f"Failed to turn on all lights for house {house_code}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('house_code')
@click.pass_context
def alllightsoff(ctx: click.Context, house_code: str):
    """Turn off all lights for house code."""
    commands = ctx.obj['commands']
    
    try:
        if commands.all_lights_off(house_code):
            click.echo(f"All lights off for house {house_code}")
        else:
            click.echo(f"Failed to turn off all lights for house {house_code}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """Show system status."""
    commands = ctx.obj['commands']
    
    try:
        status_info = commands.status()
        
        click.echo("System Status:")
        click.echo(f"  Serial port: {status_info['serial_port']}")
        click.echo(f"  Connected: {status_info['connected']}")
        click.echo(f"  Aliases: {status_info['aliases_count']}")
        click.echo(f"  Supported commands: {len(status_info['supported_commands'])}")
        
        if ctx.obj['verbose']:
            click.echo(f"  Commands: {', '.join(status_info['supported_commands'])}")
            
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)

@cli.command()
def help_extended():
    """Show extended help information."""
    help_text = f"""
Heyu {__version__} - X10 Home Automation Control (Python Implementation)

This is a Python port of the original Heyu program, maintaining compatibility
with the command structure while providing modern, testable code.

BASIC COMMANDS:
  info                    Display system information  
  status                  Show system status
  on <address>           Turn device on
  off <address>          Turn device off  
  dim <address> <level>  Dim device (level: 0-31 or 0-100%)
  bright <address> <level>  Brighten device (level: 0-31 or 0-100%)
  alllightson <house>    Turn on all lights for house code
  alllightsoff <house>   Turn off all lights for house code

ADDRESS FORMAT:
  House code (A-P) + Unit number (1-16)  
  Examples: A1, B5, K12
  
  You can also use alias names defined in the configuration file.

CONFIGURATION:
  Configuration file: ~/.heyu/x10config
  
  Example configuration:
    TTY /dev/ttyUSB0
    ALIAS living_room A1
    ALIAS bedroom A2

EXAMPLES:
  heyu info                    # Show system information
  heyu on A1                   # Turn on device A1
  heyu off living_room         # Turn off aliased device  
  heyu dim A1 50               # Dim A1 to 50%
  heyu alllightson A           # Turn on all A house lights

For more information, see the original Heyu documentation.
"""
    click.echo(help_text)

# Extended X10 Commands
@cli.command()
@click.argument('address')
@click.argument('level', type=int)
@click.pass_context
def xpreset(ctx: click.Context, address: str, level: int):
    """Extended preset dim command (0-31 or 0-100%)."""
    commands = ctx.obj['commands']
    
    try:
        if commands.xpreset(address, level):
            click.echo(f"Extended preset {address} to level {level}")
        else:
            click.echo(f"Failed to set extended preset {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')  
@click.argument('level', type=int)
@click.pass_context
def xdim(ctx: click.Context, address: str, level: int):
    """Extended dim command (0-31 or 0-100%)."""
    commands = ctx.obj['commands']
    
    try:
        if commands.xdim(address, level):
            click.echo(f"Extended dim {address} to level {level}")
        else:
            click.echo(f"Failed to extended dim {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.pass_context  
def xon(ctx: click.Context, address: str):
    """Extended full ON command."""
    commands = ctx.obj['commands']
    
    try:
        if commands.xon(address):
            click.echo(f"Extended ON {address}")
        else:
            click.echo(f"Failed to turn on {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.pass_context
def xoff(ctx: click.Context, address: str):
    """Extended full OFF command."""
    commands = ctx.obj['commands']
    
    try:
        if commands.xoff(address):
            click.echo(f"Extended OFF {address}")
        else:
            click.echo(f"Failed to turn off {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('address')
@click.pass_context
def xstatus(ctx: click.Context, address: str):
    """Extended status request."""
    commands = ctx.obj['commands']
    
    try:
        if commands.xstatus(address):
            click.echo(f"Extended status request sent to {address}")
        else:
            click.echo(f"Failed to request status from {address}", err=True)
            sys.exit(1)
    except (CommandError, SerialError, InvalidAddressError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

# Clock Management Commands
@cli.command()
@click.pass_context
def setclock(ctx: click.Context):
    """Set CM11A clock to current system time."""
    commands = ctx.obj['commands']
    
    try:
        if commands.setclock():
            click.echo("CM11A clock set to current system time")
        else:
            click.echo("Failed to set CM11A clock", err=True)
            sys.exit(1)
    except (CommandError, SerialError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def readclock(ctx: click.Context):
    """Display CM11A and system clocks."""
    commands = ctx.obj['commands']
    
    try:
        result = commands.readclock()
        click.echo("Clock Information:")
        click.echo(f"  System Time: {result['system_time']}")
        click.echo(f"  CM11A Time:  {result['cm11a_time']}")
        click.echo(f"  Status:      {result['status']}")
        
        if 'battery_status' in result:
            click.echo(f"  Battery:     {result['battery_status']}")
        if 'firmware_revision' in result:
            click.echo(f"  Firmware:    Rev {result['firmware_revision']}")
        if 'house_code' in result:
            click.echo(f"  House Code:  {result['house_code']}")
        
        if ctx.obj['verbose'] and 'raw_response' in result:
            click.echo(f"  Raw Response: {result['raw_response']}")
            
    except (CommandError, SerialError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--details', is_flag=True, help='Show detailed device status')
@click.pass_context
def poll(ctx: click.Context, details: bool):
    """Poll CM11A for status and buffered data."""
    commands = ctx.obj['commands']
    
    try:
        result = commands.poll_status(show_details=details)
        click.echo(f"Poll Results ({result['timestamp']}):")
        
        if result['buffered_data']:
            click.echo(f"  Buffered Data: {result['buffered_data']['raw']} ({result['buffered_data']['length']} bytes)")
        else:
            click.echo("  No buffered data")
        
        if result['status']:
            status = result['status']
            click.echo("  CM11A Status:")
            click.echo(f"    Battery:     {status['battery_usage']}")
            click.echo(f"    Firmware:    Rev {status['firmware_revision']}")
            click.echo(f"    House Code:  {status['house_code']}")
            click.echo(f"    Clock:       {status['clock']} (Day {status['day_of_year']})")
            
            if details:
                click.echo(f"    Last Addressed: {status['last_addressed_devices']}")
                click.echo(f"    Monitored:      {status['monitored_device_status']}")
                click.echo(f"    Dimmed:         {status['dimmed_device_status']}")
                
        else:
            click.echo("  No status available")
            
    except (CommandError, SerialError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--duration', '-d', type=int, default=60, help='Monitor duration in seconds')
@click.pass_context
def monitor(ctx: click.Context, duration: int):
    """Monitor X10 powerline activity."""
    commands = ctx.obj['commands']
    
    try:
        click.echo(f"Monitoring X10 powerline for {duration} seconds...")
        click.echo("Press Ctrl+C to stop early")
        
        activities = commands.monitor_powerline(duration)
        
        if activities:
            click.echo(f"\nDetected {len(activities)} X10 activities:")
            for activity in activities:
                click.echo(f"  {activity['time_str']} - {activity['raw_data']} ({activity['data_length']} bytes)")
                if 'house_function' in activity:
                    click.echo(f"    House/Function: {activity['house_function']}, Address: {activity['address_data']}")
        else:
            click.echo("\nNo X10 activity detected")
            
    except KeyboardInterrupt:
        click.echo("\nMonitoring interrupted by user")
    except (CommandError, SerialError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

# Add some common aliases
cli.add_command(help_extended, name='help')

def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
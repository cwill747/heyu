# Heyu Python Port - TODO List

This document tracks missing functionality and planned features for the Python port of Heyu, based on analysis of the original C codebase.

## 🎯 **Current Status**
- **Implemented**: ~15-20% of original Heyu functionality
- **Focus**: Basic X10 device control with modern, testable architecture
- **Foundation**: Solid modular design ready for feature expansion

---

## 🔍 **Major Missing Components**

### 1. **Daemon Architecture** 🔴 HIGH PRIORITY
- [ ] **State Engine daemon** (`heyu_engine`) - persistent background process
  - Tracks device states across commands
  - Manages timers and schedules
  - Handles RF sensor data processing
- [ ] **Relay daemon** - monitors CM11A and spools data to files  
  - Continuous CM11A monitoring
  - Inter-process communication via spool files
  - Power-fail detection and recovery
- [ ] **Process communication system**
  - Spool file management
  - Lock file coordination
  - Signal handling between processes

### 2. **Multiple Hardware Interface Support** 🟡 MEDIUM PRIORITY
- [ ] **CM17A "Firecracker" RF interface** (cm17a.c equivalent)
  - RF transmission capability
  - DTR/RTS serial line control
- [ ] **CM10A interface support** (cm10a.c equivalent)
  - Legacy X10 interface support
- [ ] **RFXCOM RF receivers** (rfxcom.c equivalent)
  - 433MHz RF receiver support
  - Multiple RFXCOM device types
- [ ] **RFXLAN network RF receivers**
  - Network-based RF receivers
  - TCP/IP communication

### 3. **RF Sensor/Device Support** 🟡 MEDIUM PRIORITY  
- [ ] **Oregon Scientific weather sensors** (oregon.c equivalent)
  - Temperature, humidity, wind sensors
  - Weather station integration
- [ ] **RFXSensors and RFXMeters**
  - Utility meter reading
  - Security sensors
- [ ] **Digimax thermostats** (digimax.c equivalent)
  - Remote thermostat control
  - Temperature scheduling
- [ ] **KaKu/HomeEasy devices**
  - European X10 alternatives
  - Different RF protocols

### 4. **Extended X10 Commands** 🟠 HIGH PRIORITY
- [ ] **Extended function codes**
  - `xon`, `xoff` - Extended full on/off (LM14A)
  - `xpreset`, `xdim` - Extended preset dim with ramp
  - `xstatus` - Extended status requests
  - `xconfig` - Extended auto status mode
  - `xpowerup` - Extended module power-up
- [ ] **Group commands**
  - `xgrpadd`, `xga` - Add to group
  - `xgrpaddlvl`, `xgal` - Add to group at level
  - `xgrprem`, `xgr` - Remove from group
  - `xgrpexec`, `xgx` - Execute group commands
  - `xgrpstatus`, `xgs` - Group status requests
- [ ] **Status and acknowledgment handling**
  - `status_req`, `statusreq` - Status requests
  - `status_on`, `statuson` - Status on responses
  - `status_off`, `statusoff` - Status off responses  
  - `hail`, `hail_req` - Hail requests
  - `hail_ack`, `hailack` - Hail acknowledgments
- [ ] **Preset commands**
  - `preset`, `preset_dim` - Old-style presets
  - `mpreset`, `macro_preset` - Macro-compatible presets
  - `preset_level`, `presetlevel` - Preset without address

### 5. **Scheduling and Timing System** 🟠 HIGH PRIORITY
- [ ] **CM11A timer/macro upload**
  - Upload schedules to CM11A memory
  - Macro definition and storage
  - Timer event programming
- [ ] **Real-time clock management**
  - `setclock` - Set CM11A clock from system
  - `readclock` - Read CM11A clock
  - `date` - Display/set interface date
  - Clock synchronization
- [ ] **Sunrise/sunset calculations** (sun.c equivalent)
  - Astronomical calculations
  - Location-based timing
  - Dawn/dusk scheduling integration
- [ ] **Schedule file parsing**
  - x10.sched file format support
  - Timer and macro definitions
  - Conditional scheduling
- [ ] **Timing commands**
  - `pause` - Pause execution (locked)
  - `delay` - Delay minutes (unlocked) 
  - `rdelay` - Random delay
  - `sleep` - Sleep seconds
  - `pausetick` - Pause until clock tick

### 6. **State Management System** 🟠 HIGH PRIORITY
- [ ] **Device state tracking**
  - Persistent device state storage
  - State file management (x10state)
  - On/off/dim level tracking
- [ ] **Flag and counter variables**
  - 32 common flags (expandable to 1024)
  - 32 counters (expandable to 1024)  
  - 32 user countdown timers (expandable to 1024)
  - Flag/counter manipulation commands
- [ ] **Scene management**
  - Scene definitions and storage
  - Scene execution commands
  - Scene state persistence
- [ ] **Virtual data handling**
  - `vdata`, `vdatam` - Virtual data commands
  - Internal state communication
  - Engine virtual data processing

### 7. **Advanced Features** 🟡 MEDIUM PRIORITY
- [ ] **Macro system**
  - Macro definition and execution
  - Macro upload to CM11A
  - Conditional macro execution
- [ ] **Script integration**
  - Launch external scripts/programs
  - Script execution on events
  - Environment variable passing
- [ ] **Monitoring and logging**
  - `monitor` - Live X10 traffic monitoring
  - Comprehensive logging system
  - Syslog integration
- [ ] **Power-fail recovery**
  - Power failure detection
  - Automatic recovery procedures
  - Battery backup status
- [ ] **Configuration management**
  - `utility` - Configuration utilities
  - `newbattery` - Battery replacement handling
  - `purge`, `clear` - Memory management
  - Enhanced configuration validation

---

## 📋 **Missing Commands Inventory**

### **State Engine Commands** 🔴 HIGH PRIORITY
```bash
# Core daemon control
engine          # Start state engine daemon
enginestate     # Check if engine is running
restart         # Restart engine with new config
stop            # Stop all daemons
monitor         # Live monitoring mode
```

### **Extended X10 Commands** 🟠 HIGH PRIORITY  
```bash
# Extended device control
xon <addr>              # Extended full on
xoff <addr>             # Extended full off  
xpreset <addr> <level>  # Extended preset dim
xdim <addr> <level>     # Extended dim with ramp
xstatus <addr>          # Extended status request
xconfig <addr> <mode>   # Extended auto status mode

# Group control
xgrpadd <addr> <group>     # Add device to group
xgrprem <addr> <group>     # Remove from group
xgrpexec <group> <cmd>     # Execute group command
xgrpstatus <group>         # Group status request
```

### **Status and Communication** 🟡 MEDIUM PRIORITY
```bash
# Status handling  
status_req <addr>     # Request device status
hail [housecode]      # Send hail request
hail_ack [housecode]  # Send hail acknowledgment

# Preset controls
preset <addr> <level>      # Old-style preset
preset_level <level>       # Preset without address
```

### **Timing and Scheduling** 🟠 HIGH PRIORITY
```bash
# Clock management
setclock         # Set CM11A clock from system
readclock        # Read CM11A clock  
date             # Display/set interface date

# Upload and memory
upload <schedule>    # Upload timers/macros
erase               # Erase CM11A memory
reset               # Reset CM11A interface

# Execution control
pause <seconds>     # Pause execution
delay <minutes>     # Delay execution
rdelay <min> <max>  # Random delay
sleep <seconds>     # Sleep (unlocked)
```

### **State and Variables** 🟠 HIGH PRIORITY
```bash
# Flag management
setflag <flag>         # Set software flag
clrflag <flag>         # Clear software flag
initflag <flags>       # Initialize flag bank

# Counter management  
setcounter <num> <val> # Set counter value
inccounter <num>       # Increment counter
deccounter <num>       # Decrement counter

# Virtual data
vdata <type> <data>    # Send virtual data
vdatam <type> <data>   # Send virtual memory data
```

### **Hardware and Low-level** 🟡 MEDIUM PRIORITY
```bash
# Direct hardware control
address <addr>           # Send address only
function <house> <func>  # Send function only
sendbytes <hex_data>     # Send arbitrary bytes
sendtext <house> <text>  # Send text message

# System management
newbattery          # Handle battery replacement
purge               # Purge delayed macros  
clear               # Clear status flags
utility <command>   # Configuration utilities
```

### **RF and Sensor Commands** 🟡 MEDIUM PRIORITY
```bash
# RCS/Temperature
rcs_req <addr>      # RCS-compatible status query
temp_req <addr>     # Temperature request

# RF sensor queries (require state engine)
oregon_temp <addr>      # Oregon temperature
oregon_humidity <addr>  # Oregon humidity  
rfx_temp <addr>        # RFXSensor temperature
dmx_temp <addr>        # Digimax temperature
```

---

## 🚀 **Implementation Phases**

### **Phase 1: Core Extensions** (Next Priority)
- [ ] Extended X10 commands (xpreset, xdim, xstatus)
- [ ] Clock management (setclock, readclock) 
- [ ] Basic state tracking
- [ ] Status polling and acknowledgments

### **Phase 2: Scheduling Foundation** 
- [ ] Timer upload to CM11A
- [ ] Schedule file parsing
- [ ] Sunrise/sunset calculations
- [ ] Basic macro support

### **Phase 3: State Engine**
- [ ] Background daemon architecture
- [ ] Inter-process communication
- [ ] Persistent state management
- [ ] Flag and counter systems

### **Phase 4: RF and Advanced Features**
- [ ] CM17A RF interface support
- [ ] Oregon sensor integration
- [ ] RFXCOM receiver support
- [ ] Advanced monitoring and logging

---

## 📊 **Development Guidelines**

### **Architectural Principles**
- Maintain modular, testable design
- Add comprehensive unit tests for each feature
- Preserve CLI compatibility with original Heyu
- Use modern Python patterns (async/await for daemons)
- Implement proper logging and error handling

### **Testing Strategy**
- Mock hardware interfaces for testing
- Integration tests with simulated CM11A responses
- Compatibility tests against original command set
- Performance testing for daemon operations

### **Documentation Requirements**
- Update CLI help for each new command
- Maintain compatibility matrix with original
- Document configuration file changes
- Provide migration guides from original Heyu

---

## 🏁 **Success Metrics**

- **Feature Completeness**: Target 80%+ of original functionality
- **Command Compatibility**: 100% compatible command syntax
- **Performance**: Daemon response times < 100ms
- **Reliability**: 99.9% uptime for background daemons
- **Testing**: 90%+ code coverage across all modules

---

*Last Updated: $(date)*
*Status: Foundation complete, ready for systematic feature expansion*
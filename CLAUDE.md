# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web-based GPIO control interface for NVIDIA Jetson Orin development boards. The application provides a Flask backend with REST APIs for GPIO operations and a vanilla JavaScript frontend with real-time pin visualization and control.

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment  
poetry shell

# Run the application
python app.py
```

### Running the Application
- **Development server**: `python app.py` (runs on http://0.0.0.0:5000)
- **With elevated permissions**: `sudo poetry run python app.py` (required for GPIO access)
- The application runs in debug mode by default - disable for production deployment

### GPIO Testing
The Jetson Orin Nano requires specific model environment setup:
```bash
# Test GPIO functionality
JETSON_MODEL_NAME=JETSON_ORIN_NANO python3 -c "import Jetson.GPIO as GPIO; print('GPIO test successful')"
```

## Architecture Overview

### Backend Structure (`app.py`)
- **GPIOController class**: Central hardware abstraction managing all GPIO operations
  - `all_pins` dictionary: Complete 40-pin header mapping (physical pin → type, description, GPIO number)
  - `gpio_pins` dictionary: Filtered controllable pins only
  - Pin state management with direction tracking and verification
- **Flask REST API**: RESTful endpoints for pin operations (`/api/pins`, `/api/pin/<pin>/setup|write|read`)
- **Hardware Integration**: Direct Jetson.GPIO library integration with BOARD pin numbering mode

### Frontend Structure
- **Single Page Application**: `templates/index.html` with dynamic content loading
- **GPIOController class** (`static/js/app.js`): JavaScript mirror of backend controller
  - Auto-refresh functionality (5-second intervals)
  - User selection tracking for pending changes
  - Real-time DOM updates for pin states
- **Visual Components**: 
  - Physical 40-pin header diagram with color-coded pin types
  - Individual pin control cards with setup/read/write operations
  - Activity logging with timestamped entries

### Pin Mapping System
The application uses physical pin numbering (BOARD mode) with accurate Jetson Orin GPIO mappings:
- **Controllable pins**: GPIO pins with valid GPIO numbers (e.g., Pin 7 → GPIO 492)
- **System pins**: Power (3.3V, 5V), Ground, I2C, SPI, UART pins
- **Reserved pins**: Pins used by system services or not exposed as GPIO

### State Management
- **Backend**: Pin states and directions stored in controller instance dictionaries
- **Frontend**: Local state with server synchronization, pending change tracking
- **No persistence**: Configurations are lost on application restart

## Key Implementation Details

### GPIO Operations Flow
1. **Setup**: Configure pin direction (INPUT/OUTPUT) via `/api/pin/<pin>/setup`
2. **Write**: Set OUTPUT pins to HIGH/LOW via `/api/pin/<pin>/write` 
3. **Read**: Get current pin state via `/api/pin/<pin>/read`
4. **Validation**: All operations validate pin numbers against hardware map

### Error Handling
- **Hardware errors**: GPIO exceptions caught and returned as JSON error responses
- **Validation**: Pin number and direction validation before hardware access
- **Frontend**: Error display in status bar and activity log
- **Logging**: Comprehensive logging with emoji indicators for operation types

### Security Considerations  
- **No authentication**: GPIO access is unrestricted
- **Debug mode**: Enabled by default, should be disabled for production
- **CSRF protection**: Not implemented
- **Rate limiting**: Not implemented

## Hardware-Specific Notes

### Jetson Orin Nano Compatibility
- Requires `JETSON_MODEL_NAME='JETSON_ORIN_NANO'` environment variable
- Uses Jetson.GPIO library (not RPi.GPIO) for hardware access
- Pin mapping based on official JetsonHacks documentation

### GPIO Safety
- Pin direction must be set before write operations
- Write operations include read-back verification  
- GPIO cleanup called on application teardown
- No hardware current limiting or short circuit protection

## Development Workflow

### Making Changes
- **Backend modifications**: Edit `app.py`, restart application to see changes
- **Frontend changes**: Modify files in `static/` directory, refresh browser
- **Pin mappings**: Update `all_pins` dictionary in `GPIOController.__init__`

### Testing Changes
- Use individual pin controls in web interface
- Monitor activity log for operation success/failure  
- Check browser developer console for JavaScript errors
- Verify GPIO operations with multimeter/oscilloscope

### API Development
All endpoints return JSON with consistent structure:
```json
{
  "success": boolean,
  "message": string, 
  "pin_info": {...},
  "gpio_mode": "BOARD",
  "physical_pin": number
}
```
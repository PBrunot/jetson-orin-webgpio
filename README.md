# Jetson Orin Web GPIO Controller

A web-based GPIO control interface for the NVIDIA Jetson Orin Nano Developer Kit. This application provides a user-friendly web interface to configure, read, and write GPIO pins on the Jetson Orin Nano's 40-pin header.

## Features

- **Visual GPIO Pin Layout**: Interactive representation of the Jetson Orin Nano 40-pin GPIO header
- **Pin Configuration**: Set pins as INPUT or OUTPUT
- **Real-time Control**: Read pin states and write HIGH/LOW values
- **Live Status Updates**: Monitor pin states and system status in real-time
- **Activity Logging**: Track all GPIO operations with timestamps
- **Responsive Design**: Works on desktop and mobile devices

## Requirements

- NVIDIA Jetson Orin Nano Developer Kit
- Python 3.9+
- Proper GPIO permissions (may require sudo)

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install jetson-orin-webgpio
```

### Option 2: Install from Source

1. Clone the repository:
```bash
git clone https://github.com/PBrunot/jetson-orin-webgpio.git
cd jetson-orin-webgpio
```

2. Install using pip:
```bash
pip install .
```

Or for development:
```bash
pip install -e .
```

## Usage

### Running the Application

#### Option 1: Using Console Command (PyPI Install)

```bash
jetson-gpio-web
```

#### Option 2: Using Python Module

```bash
python -m jetson_orin_webgpio.app
```

#### Option 3: From Source Directory

```bash
python jetson_orin_webgpio/app.py
```

### Accessing the Web Interface

Open your web browser and navigate to:
```
http://localhost:5000
```

Or access from another device on the network:
```
http://[jetson-ip-address]:5000
```

### Using the Interface

1. **Pin Setup**: Select a pin and choose INPUT or OUTPUT direction, then click "Setup"
2. **Reading Pins**: Click "Read" to get the current state of any pin
3. **Writing Pins**: For OUTPUT pins, click "HIGH" or "LOW" to set the pin state
4. **Monitoring**: Use the "Refresh" button to update all pin states
5. **Logging**: Monitor the activity log for detailed operation history

## Jetson Orin Nano 40-Pin Header Mapping

Complete pin mapping as shown in the web interface:

| Pin | Type    | Description                   | Status      |
|-----|---------|-------------------------------|-------------|
| 1   | Power   | 3.3 VDC Power                | System      |
| 2   | Power   | 5.0 VDC Power                | System      |
| 3   | GPIO    | I2C1_SDA (I2C Bus 7)         | Reserved    |
| 4   | Power   | 5.0 VDC Power                | System      |
| 5   | GPIO    | I2C1_SCL (I2C Bus 7)         | Reserved    |
| 6   | Ground  | GND                          | System      |
| 7   | GPIO    | GPIO09 (AUDIO_MCLK)          | **Controllable** |
| 8   | GPIO    | UART1_TX (/dev/ttyTHS0)      | Reserved    |
| 9   | Ground  | GND                          | System      |
| 10  | GPIO    | UART1_RX (/dev/ttyTHS0)      | Reserved    |
| 11  | GPIO    | UART1_RTS                    | Available   |
| 12  | GPIO    | I2S0_SCLK                    | Available   |
| 13  | GPIO    | SPI1_SCK                     | Available   |
| 14  | Ground  | GND                          | System      |
| 15  | GPIO    | GPIO12 (Alt: PWM)            | **Controllable** |
| 16  | GPIO    | SPI1_CS1                     | Available   |
| 17  | Power   | 3.3 VDC Power                | System      |
| 18  | GPIO    | SPI1_CS0                     | Available   |
| 19  | GPIO    | SPI0_MOSI                    | Available   |
| 20  | Ground  | GND                          | System      |
| 21  | GPIO    | SPI0_MISO                    | Available   |
| 22  | GPIO    | SPI1_MISO                    | Available   |
| 23  | GPIO    | SPI0_SCK                     | Available   |
| 24  | GPIO    | SPI0_CS0                     | Available   |
| 25  | Ground  | GND                          | System      |
| 26  | GPIO    | SPI0_CS1                     | Available   |
| 27  | GPIO    | I2C0_SDA (I2C Bus 1)         | Reserved    |
| 28  | GPIO    | I2C0_SCL (I2C Bus 1)         | Reserved    |
| 29  | GPIO    | GPIO01                       | **Controllable** |
| 30  | Ground  | GND                          | System      |
| 31  | GPIO    | GPIO11                       | **Controllable** |
| 32  | GPIO    | GPIO07 (Alt: PWM)            | **Controllable** |
| 33  | GPIO    | GPIO13 (Alt: PWM)            | **Controllable** |
| 34  | Ground  | GND                          | System      |
| 35  | GPIO    | I2S0_FS                      | Available   |
| 36  | GPIO    | UART1_CTS                    | Available   |
| 37  | GPIO    | SPI1_MOSI                    | Available   |
| 38  | GPIO    | I2S0_SDIN                    | Available   |
| 39  | Ground  | GND                          | System      |
| 40  | GPIO    | I2S0_SDOUT                   | Available   |

### Pin Status Legend
- **System**: Power/Ground pins (cannot be controlled)
- **Reserved**: Communication pins typically used by system services (I2C, UART)
- **Available**: GPIO pins with valid GPIO numbers but not configured in device tree
- **Controllable**: GPIO pins configured in `gpio_pins.dts` and ready for use in the web interface

**Note**: Only pins marked as "Controllable" will be enabled in the web interface. Other GPIO pins appear grayed out with a warning that they need device tree configuration.

## API Endpoints

The application provides REST API endpoints for programmatic access:

- `GET /api/pins` - Get all pin states and configurations
- `POST /api/pin/<pin>/setup` - Configure a pin as INPUT or OUTPUT
- `POST /api/pin/<pin>/write` - Write HIGH/LOW to an OUTPUT pin
- `GET /api/pin/<pin>/read` - Read the current state of a pin

## GPIO Pin Configuration (Device Tree)

This project includes a device tree overlay (`gpio_pins.dts`) that configures specific pins for GPIO operation. The overlay enables pins 7, 15, 29, 31, 32, and 33 as bidirectional GPIO pins.

### Configuring Additional GPIO Pins

To configure additional pins for GPIO use, you'll need to modify the device tree overlay:

1. **Edit the DTS file** (`gpio_pins.dts`):
   ```bash
   nano gpio_pins.dts
   ```

2. **Add pin configuration** within the `jetson_io_pinmux` section. For example, to add pin 40:
   ```dts
   hdr40-pin40 {
       nvidia,pins = "soc_gpio20_pg7";
       nvidia,tristate = <0x0>;
       nvidia,enable-input = <0x1>;
       nvidia,pull = <0x0>;
   };
   ```

3. **Compile the device tree overlay**:
   ```bash
   dtc -I dts -O dtb -o gpio_pins.dtbo gpio_pins.dts
   ```

4. **Install the overlay** (requires root):
   ```bash
   sudo cp gpio_pins.dtbo /boot/
   sudo /opt/nvidia/jetson-io/jetson-io.py -n "Pin Configuration" /boot/gpio_pins.dtbo
   ```

5. **Reboot** to apply the changes:
   ```bash
   sudo reboot
   ```

### Pin Mapping Reference

Each GPIO pin requires its corresponding SOC pin name in the device tree. Common mappings include:
- Pin 7: `soc_gpio59_pac6`
- Pin 15: `soc_gpio39_pn1`
- Pin 29: `soc_gpio32_pq5`
- Pin 31: `soc_gpio33_pq6`
- Pin 32: `soc_gpio19_pg6`
- Pin 33: `soc_gpio21_ph0`

**Note**: Only pins configured in the active device tree overlay will be controllable through the web interface. Unconfigured pins will be disabled in the UI.

## Permissions

GPIO access typically requires elevated permissions. You may need to run the application with sudo:

```bash
sudo jetson-gpio-web
```

Or when running from source:
```bash
sudo python jetson_orin_webgpio/app.py
```

Alternatively, configure udev rules for GPIO access without sudo.

## Safety Notes

- **Exercise Caution**: Incorrectly connecting or controlling GPIO pins can damage your Jetson Orin Nano
- **Check Connections**: Always verify your wiring before enabling OUTPUT mode on pins
- **Current Limits**: Be aware of current limitations when driving external devices
- **Backup Configuration**: The application doesn't persist pin configurations between restarts

## Troubleshooting

### Permission Denied Errors
- Run with sudo or configure GPIO permissions
- Check that your user is in the gpio group

### Pin Already in Use
- Some pins may be used by other system services
- Check for conflicting device tree overlays or drivers

### Web Interface Not Accessible
- Ensure the Flask server is running on 0.0.0.0:5000
- Check firewall settings if accessing remotely
- Verify network connectivity

## Development

The project structure:
```
jetson-orin-webgpio/
├── jetson_orin_webgpio/           # Main Python package
│   ├── __init__.py                # Package initialization
│   ├── app.py                     # Main Flask application
│   ├── templates/
│   │   └── index.html             # Web interface template
│   └── static/
│       ├── css/
│       │   └── style.css          # Stylesheet
│       └── js/
│           └── app.js             # Frontend JavaScript
├── .github/workflows/
│   └── publish-to-pypi.yml        # GitHub Actions for PyPI publishing
├── gpio_pins.dts                  # Device tree overlay source
├── pyproject.toml                 # Python packaging configuration
├── MANIFEST.in                    # Additional files for distribution
├── LICENSE                        # MIT license
└── README.md                      # This file
```

### Installing for Development

```bash
git clone https://github.com/PBrunot/jetson-orin-webgpio.git
cd jetson-orin-webgpio
pip install -e .[dev]
```

## Acknowledgments

This project was developed with reference to the excellent JetsonHacks article on device tree overlays:
- **"Device Tree Overlays on Jetson - Scary but Fun"** by Jim Benson  
- Article URL: https://jetsonhacks.com/2025/04/07/device-tree-overlays-on-jetson-scary-but-fun/

The device tree overlay configuration and GPIO pin mappings are based on the comprehensive documentation and examples provided in this article.

Additional reference documentation:
- **NVIDIA Jetson Orin NX and Orin Nano Pinmux Configuration Template**  
- Official NVIDIA documentation for detailed pin configuration reference

## License

This project is provided as-is for educational and development purposes.
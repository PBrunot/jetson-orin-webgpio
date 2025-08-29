from flask import Flask, render_template, jsonify, request
import os
import json
import threading
import time
import logging
from datetime import datetime

# Fix for Jetson Orin Nano Super - Set model name before importing Jetson.GPIO
os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'

import Jetson.GPIO as GPIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class GPIOController:
    def __init__(self):
        logger.info("🚀 Initializing GPIO Controller...")
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(True)
            logger.info("✅ GPIO mode set to BOARD, warnings disabled")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPIO: {e}")
            raise
        
        self.pin_states = {}
        self.pin_directions = {}
        
        # Jetson Orin 40-pin GPIO header mapping (accurate JetsonHacks PDF pinout)
        self.all_pins = {
            # Physical pin: (type, description, gpio_number or None)
            1: ("power", "3.3 VDC Power", None),
            2: ("power", "5.0 VDC Power", None),
            3: ("gpio", "I2C1_SDA (I2C Bus 7)", None),  # I2C Bus 7, typically not used as GPIO
            4: ("power", "5.0 VDC Power", None),
            5: ("gpio", "I2C1_SCL (I2C Bus 7)", None),  # I2C Bus 7, typically not used as GPIO
            6: ("ground", "GND", None),
            7: ("gpio", "GPIO09 (AUDIO_MCLK)", 492),  # Sysfs: 144
            8: ("gpio", "UART1_TX (/dev/ttyTHS0)", None),  # /dev/ttyTHS0, typically not used as GPIO
            9: ("ground", "GND", None),
            10: ("gpio", "UART1_RX (/dev/ttyTHS0)", None),  # /dev/ttyTHS0, typically not used as GPIO
            11: ("gpio", "UART1_RTS", 460),  # Sysfs: 112
            12: ("gpio", "I2S0_SCLK", 398),  # Sysfs: 50
            13: ("gpio", "SPI1_SCK", 470),  # Sysfs: 122
            14: ("ground", "GND", None),
            15: ("gpio", "GPIO12 (Alt: PWM)", 433),  # Sysfs: 85
            16: ("gpio", "SPI1_CS1", 474),  # Sysfs: 126
            17: ("power", "3.3 VDC Power", None),
            18: ("gpio", "SPI1_CS0", 473),  # Sysfs: 125
            19: ("gpio", "SPI0_MOSI", 483),  # Sysfs: 135
            20: ("ground", "GND", None),
            21: ("gpio", "SPI0_MISO", 482),  # Sysfs: 134
            22: ("gpio", "SPI1_MISO", 471),  # Sysfs: 123
            23: ("gpio", "SPI0_SCK", 481),  # Sysfs: 133
            24: ("gpio", "SPI0_CS0", 484),  # Sysfs: 136
            25: ("ground", "GND", None),
            26: ("gpio", "SPI0_CS1", 485),  # Sysfs: 137
            27: ("gpio", "I2C0_SDA (I2C Bus 1)", None),  # I2C Bus 1, typically not used as GPIO
            28: ("gpio", "I2C0_SCL (I2C Bus 1)", None),  # I2C Bus 1, typically not used as GPIO
            29: ("gpio", "GPIO01", 453),  # Sysfs: 105
            30: ("ground", "GND", None),
            31: ("gpio", "GPIO11", 454),  # Sysfs: 106
            32: ("gpio", "GPIO07 (Alt: PWM)", 389),  # Sysfs: 41
            33: ("gpio", "GPIO13 (Alt: PWM)", 391),  # Sysfs: 43
            34: ("ground", "GND", None),
            35: ("gpio", "I2S0_FS", 401),  # Sysfs: 53
            36: ("gpio", "UART1_CTS", 461),  # Sysfs: 113
            37: ("gpio", "SPI1_MOSI", 472),  # Sysfs: 124
            38: ("gpio", "I2S0_SDIN", 400),  # Sysfs: 52
            39: ("ground", "GND", None),
            40: ("gpio", "I2S0_SDOUT", 399)  # Sysfs: 51
        }
        
        # Pins configured in gpio_pins.dts device tree overlay
        self.dts_configured_pins = {7, 15, 29, 31, 32, 33}
        
        # GPIO pins that can be controlled (have GPIO numbers AND are configured in DTS)
        self.gpio_pins = {
            pin: gpio_num for pin, (pin_type, desc, gpio_num) in self.all_pins.items() 
            if pin_type == "gpio" and gpio_num is not None and pin in self.dts_configured_pins
        }
        
        logger.info(f"📍 Controllable GPIO pins found: {list(self.gpio_pins.keys())}")
        
        # Initialize pin states
        for pin in self.gpio_pins:
            try:
                self.pin_directions[pin] = "INPUT"
                self.pin_states[pin] = False
                logger.debug(f"Pin {pin} initialized as INPUT")
            except Exception as e:
                logger.error(f"❌ Error initializing pin {pin}: {e}")
    
    def get_pin_info(self):
        result = {}
        for pin, (pin_type, description, gpio_num) in self.all_pins.items():
            result[pin] = {
                'type': pin_type,
                'description': description,
                'gpio_num': gpio_num,
                'controllable': pin in self.gpio_pins,
                'dts_configured': pin in self.dts_configured_pins,
                'has_gpio_num': gpio_num is not None and pin_type == 'gpio'
            }
            
            # Add state info for controllable GPIO pins
            if pin in self.gpio_pins:
                result[pin].update({
                    'direction': self.pin_directions.get(pin, 'INPUT'),
                    'state': self.pin_states.get(pin, False)
                })
        
        return result
    
    def setup_pin(self, pin, direction):
        logger.info(f"🔧 SETUP: Pin {pin} -> {direction.upper()}")
        try:
            if pin not in self.gpio_pins:
                logger.error(f"❌ SETUP: Invalid pin {pin}. Valid pins: {list(self.gpio_pins.keys())}")
                return False, f"Invalid pin {pin}"
            
            gpio_num = self.gpio_pins[pin]
            logger.info(f"📌 SETUP: Physical pin {pin} maps to GPIO {gpio_num}")
            
            if direction.upper() == "OUTPUT":
                logger.info(f"⚡ SETUP: Configuring pin {pin} (GPIO {gpio_num}) as OUTPUT")
                GPIO.setup(pin, GPIO.OUT)
                self.pin_directions[pin] = "OUTPUT"
                self.pin_states[pin] = False
                logger.info(f"✅ SETUP: Pin {pin} successfully configured as OUTPUT, state = LOW")
            elif direction.upper() == "INPUT":
                logger.info(f"📥 SETUP: Configuring pin {pin} (GPIO {gpio_num}) as INPUT")
                GPIO.setup(pin, GPIO.IN)
                self.pin_directions[pin] = "INPUT"
                initial_state = GPIO.input(pin)
                self.pin_states[pin] = initial_state
                logger.info(f"✅ SETUP: Pin {pin} successfully configured as INPUT, initial state = {'HIGH' if initial_state else 'LOW'}")
            else:
                logger.error(f"❌ SETUP: Invalid direction '{direction}' for pin {pin}")
                return False, "Invalid direction. Use INPUT or OUTPUT"
            
            return True, f"Pin {pin} configured as {direction.upper()}"
        except Exception as e:
            logger.error(f"💥 SETUP: Exception on pin {pin}: {type(e).__name__}: {e}")
            return False, str(e)
    
    def write_pin(self, pin, state):
        logger.info(f"✍️ WRITE: Pin {pin} -> {'HIGH' if state else 'LOW'}")
        try:
            if pin not in self.gpio_pins:
                logger.error(f"❌ WRITE: Invalid pin {pin}. Valid pins: {list(self.gpio_pins.keys())}")
                return False, f"Invalid pin {pin}"
            
            current_direction = self.pin_directions.get(pin)
            if current_direction != "OUTPUT":
                logger.error(f"❌ WRITE: Pin {pin} direction is '{current_direction}', must be OUTPUT")
                return False, f"Pin {pin} is not configured as OUTPUT (current: {current_direction})"
            
            gpio_num = self.gpio_pins[pin]
            state_bool = bool(state)
            logger.info(f"📤 WRITE: Setting pin {pin} (GPIO {gpio_num}) to {'HIGH' if state_bool else 'LOW'}")
            
            GPIO.output(pin, state_bool)
            self.pin_states[pin] = state_bool
            
            # Verify the write by reading back
            try:
                actual_state = GPIO.input(pin)
                logger.info(f"🔍 WRITE: Verification - pin {pin} actual state: {'HIGH' if actual_state else 'LOW'}")
                if actual_state != state_bool:
                    logger.warning(f"⚠️ WRITE: State mismatch! Requested: {'HIGH' if state_bool else 'LOW'}, Actual: {'HIGH' if actual_state else 'LOW'}")
            except Exception as read_e:
                logger.warning(f"⚠️ WRITE: Could not verify write: {read_e}")
            
            logger.info(f"✅ WRITE: Pin {pin} set to {'HIGH' if state_bool else 'LOW'}")
            return True, f"Pin {pin} set to {'HIGH' if state_bool else 'LOW'}"
        except Exception as e:
            logger.error(f"💥 WRITE: Exception on pin {pin}: {type(e).__name__}: {e}")
            return False, str(e)
    
    def read_pin(self, pin):
        logger.info(f"👁️ READ: Pin {pin}")
        try:
            if pin not in self.gpio_pins:
                logger.error(f"❌ READ: Invalid pin {pin}. Valid pins: {list(self.gpio_pins.keys())}")
                return False, f"Invalid pin {pin}", None
            
            gpio_num = self.gpio_pins[pin]
            current_direction = self.pin_directions.get(pin, 'UNKNOWN')
            
            if current_direction == "INPUT":
                logger.info(f"📥 READ: Reading INPUT pin {pin} (GPIO {gpio_num})")
                state = GPIO.input(pin)
                self.pin_states[pin] = state
                logger.info(f"✅ READ: Pin {pin} state = {'HIGH' if state else 'LOW'}")
                return True, f"Pin {pin} state read", state
            else:
                logger.info(f"📤 READ: Reading OUTPUT pin {pin} (GPIO {gpio_num}) - returning cached state")
                cached_state = self.pin_states[pin]
                logger.info(f"✅ READ: Pin {pin} cached state = {'HIGH' if cached_state else 'LOW'}")
                return True, f"Pin {pin} current state", cached_state
        except Exception as e:
            logger.error(f"💥 READ: Exception on pin {pin}: {type(e).__name__}: {e}")
            return False, str(e), None
    
    def cleanup(self):
        GPIO.cleanup()

gpio_controller = GPIOController()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pins')
def get_pins():
    logger.info("📊 API: /api/pins - Getting all pin info")
    try:
        pin_info = gpio_controller.get_pin_info()
        logger.info(f"✅ API: Returning info for {len(pin_info)} pins")
        return jsonify(pin_info)
    except Exception as e:
        logger.error(f"💥 API: /api/pins failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pin/<int:pin>/setup', methods=['POST'])
def setup_pin(pin):
    logger.info(f"🔧 API: /api/pin/{pin}/setup")
    try:
        data = request.get_json()
        direction = data.get('direction', '').upper()
        logger.info(f"📝 API: Request data: {data}")
        logger.info(f"🎯 API: Pin {pin}, Direction: {direction}")
        
        success, message = gpio_controller.setup_pin(pin, direction)
        
        result = {
            'success': success,
            'message': message,
            'pin_info': gpio_controller.get_pin_info().get(pin, {}),
            'gpio_mode': 'BOARD',  # Current mode
            'physical_pin': pin
        }
        
        logger.info(f"📤 API: Setup result: success={success}, message='{message}'")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 API: /api/pin/{pin}/setup failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/pin/<int:pin>/write', methods=['POST'])
def write_pin(pin):
    logger.info(f"✍️ API: /api/pin/{pin}/write")
    try:
        data = request.get_json()
        state = data.get('state', False)
        logger.info(f"📝 API: Request data: {data}")
        logger.info(f"🎯 API: Pin {pin}, State: {'HIGH' if state else 'LOW'}")
        
        success, message = gpio_controller.write_pin(pin, state)
        
        result = {
            'success': success,
            'message': message,
            'pin_info': gpio_controller.get_pin_info().get(pin, {}),
            'gpio_mode': 'BOARD',
            'physical_pin': pin
        }
        
        logger.info(f"📤 API: Write result: success={success}, message='{message}'")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 API: /api/pin/{pin}/write failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/pin/<int:pin>/read', methods=['GET'])
def read_pin(pin):
    logger.info(f"👁️ API: /api/pin/{pin}/read")
    try:
        success, message, state = gpio_controller.read_pin(pin)
        
        result = {
            'success': success,
            'message': message,
            'state': state,
            'pin_info': gpio_controller.get_pin_info().get(pin, {}),
            'gpio_mode': 'BOARD',
            'physical_pin': pin
        }
        
        logger.info(f"📤 API: Read result: success={success}, state={'HIGH' if state else 'LOW'}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 API: /api/pin/{pin}/read failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/gpio-info')
def gpio_info():
    """Debug endpoint to show GPIO configuration details"""
    logger.info("🔍 API: /api/gpio-info - GPIO debug information")
    
    info = {
        'gpio_mode': 'BOARD (Physical Pin Numbers)',
        'jetson_gpio_mode': 'BOARD',
        'total_pins': 40,
        'controllable_pins': len(gpio_controller.gpio_pins),
        'pin_mapping': {
            pin: {
                'physical_pin': pin,
                'gpio_number': gpio_num,
                'description': gpio_controller.all_pins[pin][1]
            }
            for pin, gpio_num in gpio_controller.gpio_pins.items()
        }
    }
    
    logger.info(f"📤 API: GPIO info returned")
    return jsonify(info)

@app.teardown_appcontext
def cleanup_gpio(error):
    if error:
        gpio_controller.cleanup()

def main():
    """Main entry point for the application."""
    logger.info("🚀 Starting Jetson Orin GPIO Web Controller...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        gpio_controller.cleanup()
        logger.info("🧹 GPIO cleanup completed")

if __name__ == '__main__':
    main()
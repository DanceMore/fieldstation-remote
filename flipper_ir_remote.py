#!/usr/bin/env python3
"""
IR Remote Mapper - Core Library
Maps IR signals to standardized events with intelligent digit queue system and display control
"""

import serial
import sys
import time
import re
import json
import os
import subprocess
import threading
from collections import deque

SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
LOG_PATH = "/home/appuser/FieldStation42/runtime/ir_mapper.log"

# Valid channels - super simple array for now
VALID_CHANNELS = [1, 2, 3, 8, 9, 13]

class DisplayController:
    """Handles 7-segment display communication via serial"""

    def __init__(self, display_device=None, baudrate=9600):
        self.display_serial = None
        self.display_device = display_device
        self.baudrate = baudrate
        self.lock = threading.Lock()
        
        if display_device:
            self.connect_display()
    
    def connect_display(self):
        """Connect to the display serial device"""
        try:
            if self.display_device:
                self.display_serial = serial.Serial(self.display_device, self.baudrate, timeout=1)
                time.sleep(0.1)  # Give display time to initialize
                print(f"📟 Display connected on {self.display_device}")
                # Test the display
                self.display_text("INIT")
                time.sleep(0.5)
                self.clear_display()
        except Exception as e:
            print(f"❌ Failed to connect to display: {e}")
            self.display_serial = None
    
    def send_display_command(self, command):
        """Send command to display with error handling"""
        if not self.display_serial:
            print(f"📟 Display command (no device): {command}")
            return False
            
        try:
            with self.lock:
                cmd_bytes = f"{command}\r\n".encode('ascii')
                self.display_serial.write(cmd_bytes)
                self.display_serial.flush()
                print(f"📟 Display: {command}")
                return True
        except Exception as e:
            print(f"❌ Display error: {e}")
            return False
    
    def display_text(self, text):
        """Display text (up to 4 chars)"""
        text = str(text)[:4].upper()  # Limit to 4 chars and uppercase
        return self.send_display_command(f"DISP:{text}")
    
    def display_number(self, number):
        """Display number (up to 4 digits)"""
        if isinstance(number, str):
            # Preserve string format (including leading zeros)
            num_str = number[:4]
        else:
            # Convert number to string
            num_str = str(int(number))[:4]
        return self.send_display_command(f"DISP:{num_str}")
    
    def clear_display(self):
        """Clear the display"""
        return self.send_display_command("DISP:CLR")
    
    def set_brightness(self, level):
        """Set brightness (0-7)"""
        level = max(0, min(7, int(level)))  # Clamp to 0-7
        return self.send_display_command(f"DISP:BRT:{level}")
    
    def turn_on(self):
        """Turn display on"""
        return self.send_display_command("DISP:ON")
    
    def turn_off(self):
        """Turn display off"""
        return self.send_display_command("DISP:OFF")

class ChannelDialer:
    def __init__(self, digit_timeout=1.5, easter_egg_timeout=1.5, display_controller=None):
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.easter_egg_timeout = easter_egg_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = 1  # Track current channel, default to 1
        
        # Easter egg mappings - add more as needed
        self.easter_eggs = {
            "911": self.emergency_mode,
            "666": self.demon_mode,
            "420": self.party_mode,
            "777": self.lucky_mode,
            "1234": self.test_mode,
            "0000": self.reset_mode,
            "404": self.error_mode,
            "80085": self.fun_mode,  # Support for longer sequences
        }
    
    def add_digit(self, digit):
        """Add a digit to the queue and manage timing"""
        try:
            with self.lock:
                self.digit_queue.append(str(digit))
                self.last_digit_time = time.time()
                
                # Show current digit sequence on display
                current_sequence = ''.join(self.digit_queue)
                if self.display:
                    # Use display_number to handle leading zeros properly
                    self.display.display_number(current_sequence)
                
                # Cancel existing timer
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                
                # Check for immediate Easter egg matches (like 911)
                if current_sequence in self.easter_eggs:
                    print(f"🎯 Easter egg triggered: {current_sequence}")
                    try:
                        self.easter_eggs[current_sequence]()
                    except Exception as e:
                        print(f"Easter egg execution error: {e}")
                    # Clear queue but don't return - system is ready for new input
                    self.digit_queue.clear()
                    # Show current channel on display after easter egg
                    if self.display:
                        time.sleep(1)  # Brief pause to show easter egg feedback
                        self.display.display_number(self.current_channel)
                    print("🎮 Ready for new input...")
                    return
                
                # Set new timer for regular channel processing
                self.timer = threading.Timer(self.digit_timeout, self._process_channel)
                self.timer.start()
        except Exception as e:
            print(f"Add digit error: {e}")
            # Try to recover by clearing the queue
            try:
                self.clear_queue()
            except:
                pass
    
    def clear_queue(self):
        """Clear the digit queue"""
        try:
            with self.lock:
                self.digit_queue.clear()
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                # Show current channel when clearing
                if self.display:
                    self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"Clear queue error: {e}")
            # Force clear even if lock fails
            try:
                self.digit_queue.clear()
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
            except:
                pass
    
    def _process_channel(self):
        """Process accumulated digits as channel number"""
        try:
            with self.lock:
                if not self.digit_queue:
                    return
                
                channel_str = ''.join(self.digit_queue)
                
                # Check for Easter eggs one more time
                if channel_str in self.easter_eggs:
                    print(f"🎯 Easter egg triggered: {channel_str}")
                    try:
                        self.easter_eggs[channel_str]()
                    except Exception as e:
                        print(f"Easter egg execution error: {e}")
                    # Show current channel after easter egg
                    if self.display:
                        time.sleep(1)
                        self.display.display_number(self.current_channel)
                else:
                    try:
                        channel_num = int(channel_str)
                        self.tune_to_channel(channel_num)
                    except ValueError:
                        print(f"❌ Invalid channel sequence: {channel_str}")
                        # Show error briefly, then return to current channel
                        if self.display:
                            self.display.display_text("ERR")
                            time.sleep(1)
                            self.display.display_number(self.current_channel)
                
                self.digit_queue.clear()
                self.timer = None
        except Exception as e:
            print(f"Channel processing error: {e}")
            # Ensure we clean up even if there's an error
            try:
                with self.lock:
                    self.digit_queue.clear()
                    self.timer = None
                    # Fallback to showing current channel
                    if self.display:
                        self.display.display_number(self.current_channel)
            except:
                pass
    
    def tune_to_channel(self, channel):
        """Tune to specific channel number with validation"""
        print(f"📺 Attempting to tune to channel {channel}")
        
        # Check if channel is valid
        if channel in VALID_CHANNELS:
            print(f"✅ Valid channel: {channel}")
            self.current_channel = channel
            if self.display:
                self.display.display_number(channel)
            write_json_to_socket({
                "command": "direct", 
                "channel": channel,
                "valid": True,
                "timestamp": time.time()
            })
        else:
            print(f"❌ Invalid channel: {channel} (valid: {VALID_CHANNELS})")
            # Show invalid channel briefly, then revert to current
            if self.display:
                self.display.display_text("NOPE")
                time.sleep(0.8)
                self.display.display_number(self.current_channel)
            # Still send the command but mark as invalid - let TV decide
            write_json_to_socket({
                "command": "direct", 
                "channel": channel,
                "valid": False,
                "fallback_channel": self.current_channel,
                "timestamp": time.time()
            })

    def channel_up(self):
        """Handle channel up with validation"""
        # Show switching indicator
        if self.display:
            self.display.display_text("UP")
            time.sleep(0.4)  # Brief switching animation

        # Find next valid channel
        current_idx = VALID_CHANNELS.index(self.current_channel) if self.current_channel in VALID_CHANNELS else 0
        next_idx = (current_idx + 1) % len(VALID_CHANNELS)
        next_channel = VALID_CHANNELS[next_idx]

        print(f"📺 Channel UP: {self.current_channel} -> {next_channel}")
        self.current_channel = next_channel
        if self.display:
            self.display.display_number(self.current_channel)

        write_json_to_socket({
            "command": "up", 
            "channel": self.current_channel,
            "timestamp": time.time()
        })  

    def channel_down(self):
        """Handle channel down with validation"""
        # Show switching indicator
        if self.display:
            self.display.display_text("Dn")
            time.sleep(0.4)  # Brief switching animation

        # Find previous valid channel
        current_idx = VALID_CHANNELS.index(self.current_channel) if self.current_channel in VALID_CHANNELS else 0
        prev_idx = (current_idx - 1) % len(VALID_CHANNELS)
        prev_channel = VALID_CHANNELS[prev_idx]

        print(f"📺 Channel DOWN: {self.current_channel} -> {prev_channel}")
        self.current_channel = prev_channel
        if self.display:
            self.display.display_number(self.current_channel)

        write_json_to_socket({
            "command": "down", 
            "channel": self.current_channel,
            "timestamp": time.time()
        })

    # Easter egg functions - all with exception handling
    def emergency_mode(self):
        try:
            print("🚨 EMERGENCY MODE ACTIVATED! 🚨")
            if self.display:
                self.display.display_text("911!")
            # Safely try to send key to mpv
            try:
                send_key_to_mpv('c')  # Could trigger special emergency feed
            except Exception as e:
                print(f"Easter egg mpv command failed: {e}")
        except Exception as e:
            print(f"Emergency mode error: {e}")
    
    def demon_mode(self):
        try:
            print("😈 DEMON MODE ACTIVATED! 😈")
            if self.display:
                self.display.display_text("666")
        except Exception as e:
            print(f"Demon mode error: {e}")
    
    def party_mode(self):
        try:
            print("🎉 PARTY MODE ACTIVATED! 🎉")
            if self.display:
                self.display.display_text("420")
        except Exception as e:
            print(f"Party mode error: {e}")
    
    def lucky_mode(self):
        try:
            print("🍀 LUCKY MODE ACTIVATED! 🍀")
            if self.display:
                self.display.display_text("777")
        except Exception as e:
            print(f"Lucky mode error: {e}")
    
    def test_mode(self):
        try:
            print("🧪 TEST MODE ACTIVATED! 🧪")
            if self.display:
                self.display.display_text("TEST")
        except Exception as e:
            print(f"Test mode error: {e}")
    
    def reset_mode(self):
        try:
            print("🔄 RESET MODE ACTIVATED! 🔄")
            if self.display:
                self.display.display_text("RST")
                time.sleep(1)
            # Reset to first valid channel
            self.current_channel = VALID_CHANNELS[0]
            if self.display:
                self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"Reset mode error: {e}")
    
    def error_mode(self):
        try:
            print("💥 ERROR MODE ACTIVATED! 💥")
            if self.display:
                self.display.display_text("404")
        except Exception as e:
            print(f"Error mode error: {e}")
    
    def fun_mode(self):
        try:
            print("😄 FUN MODE ACTIVATED! 😄")
            if self.display:
                self.display.display_text("BOOB")  # 80085 -> BOOB on 7-segment
        except Exception as e:
            print(f"Fun mode error: {e}")

def write_json_to_socket(data):
    try:
        json_str = json.dumps(data)
        with open(SOCKET_PATH, 'w') as f:
            f.write(json_str)
        print(f"JSON written: {json_str}")
    except Exception as e:
        print(f"Error writing to socket: {e}")

def send_key_to_mpv(key):
    try:
        window_id = subprocess.check_output(
            ['xdotool', 'search', '--onlyvisible', '--class', 'mpv'],
            env={'DISPLAY': ':0'}
        ).decode().strip().split('\n')[0]
        subprocess.run(['xdotool', 'key', '--window', window_id, key], env={'DISPLAY': ':0'})
    except Exception as e:
        print(f"Failed to send key '{key}' to mpv: {e}")

# Enhanced remote configurations with more button mappings
REMOTE_CONFIGS = {
    "nec_0x32": {
        "protocol": "NEC",
        "address": "0x32",
        "mappings": {
            # Channel controls
            "0x11": "CHANNEL_UP",
            "0x14": "CHANNEL_DOWN",
            
            # Effects
            "0x10": "EFFECT_PREV",
            "0x12": "EFFECT_NEXT",
            
            # Digits
            "0x00": "DIGIT_0",
            "0x01": "DIGIT_1",
            "0x02": "DIGIT_2",
            "0x03": "DIGIT_3",
            "0x04": "DIGIT_4",
            "0x05": "DIGIT_5",
            "0x06": "DIGIT_6",
            "0x07": "DIGIT_7",
            "0x08": "DIGIT_8",
            "0x09": "DIGIT_9",
        }
    },
    "samsung_tv": {
        "protocol": "Samsung32",
        "address": "0x07",
        "mappings": {
            "0x12": "CHANNEL_UP",
            "0x10": "CHANNEL_DOWN",
            
            # Samsung digit mappings
            "0x04": "DIGIT_1",
            "0x05": "DIGIT_2",
            "0x06": "DIGIT_3",
            "0x08": "DIGIT_4",
            "0x09": "DIGIT_5",
            "0x0A": "DIGIT_6",
            "0x0C": "DIGIT_7",
            "0x0D": "DIGIT_8",
            "0x0E": "DIGIT_9",
            "0x11": "DIGIT_0",
        }
    },
    "sony": {
        "protocol": "SIRC",
        "address": "0x01",
        "mappings": {
            "0x10": "CHANNEL_UP",
            "0x11": "CHANNEL_DOWN",
            "0x33": "EFFECT_NEXT",
            "0x34": "EFFECT_PREV",
            
            # Sony digit mappings
            "0x00": "DIGIT_1",
            "0x01": "DIGIT_2",
            "0x02": "DIGIT_3",
            "0x03": "DIGIT_4",
            "0x04": "DIGIT_5",
            "0x05": "DIGIT_6",
            "0x06": "DIGIT_7",
            "0x07": "DIGIT_8",
            "0x08": "DIGIT_9",
            "0x09": "DIGIT_0",
        }
    },
    "sony_0x77": {
        "protocol": "SIRC",
        "address": "0x77",
        "mappings": {
            "0x0D": "DIGITAL_ANALOG",
        }
    },
}

class IRRemoteMapper:
    """Main IR Remote Mapper class that coordinates everything"""
    
    def __init__(self, args):
        self.args = args
        self.display_controller = None
        self.channel_dialer = None
        self.flipper = None
        self.log_file = None
        
        # Event state
        self.last_event = None
        self.last_event_time = 0
        
        # Initialize components
        self._setup_logging()
        self._setup_display()
        self._setup_channel_dialer()
        self._setup_event_handlers()
    
    def _setup_logging(self):
        """Setup logging if requested"""
        if self.args.log_to_file:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            self.log_file = open(LOG_PATH, 'a')
            sys.stdout = self.log_file
            sys.stderr = self.log_file
    
    def _setup_display(self):
        """Initialize display controller"""
        self.display_controller = DisplayController(self.args.display_device, self.args.display_baud)
        if self.display_controller.display_serial:
            self.display_controller.set_brightness(self.args.display_brightness)
            self.display_controller.turn_on()
    
    def _setup_channel_dialer(self):
        """Initialize channel dialer with display"""
        self.channel_dialer = ChannelDialer(
            digit_timeout=self.args.digit_timeout,
            display_controller=self.display_controller
        )
    
    def _setup_event_handlers(self):
        """Setup event handler mappings"""
        self.event_handlers = {
            'CHANNEL_UP': self._handle_channel_up,
            'CHANNEL_DOWN': self._handle_channel_down,
            'EFFECT_NEXT': self._handle_effect_next,
            'EFFECT_PREV': self._handle_effect_prev,
            'VOLUME_UP': self._handle_volume_up,
            'VOLUME_DOWN': self._handle_volume_down,
            'MUTE': self._handle_mute,
            'POWER': self._handle_power,
            'PAUSE': self._handle_pause,
            'INFO': self._handle_info,
            'MENU': self._handle_menu,
            'OK': self._handle_ok,
            'BACK': self._handle_back,
            'DIGIT_0': lambda: self._handle_digit(0),
            'DIGIT_1': lambda: self._handle_digit(1),
            'DIGIT_2': lambda: self._handle_digit(2),
            'DIGIT_3': lambda: self._handle_digit(3),
            'DIGIT_4': lambda: self._handle_digit(4),
            'DIGIT_5': lambda: self._handle_digit(5),
            'DIGIT_6': lambda: self._handle_digit(6),
            'DIGIT_7': lambda: self._handle_digit(7),
            'DIGIT_8': lambda: self._handle_digit(8),
            'DIGIT_9': lambda: self._handle_digit(9),
            'DIGITAL_ANALOG': self._handle_digital_analog,
        }
    
    def _boot_sequence(self):
        """Show boot sequence on display"""
        if self.display_controller and self.display_controller.display_serial:
            self.display_controller.display_text("----")
            time.sleep(0.8)
            self.display_controller.display_text("ACId")
            time.sleep(0.4)
            self.display_controller.display_text("BOOT")
            time.sleep(2.0)
            self.display_controller.display_text("redY")
            time.sleep(1.5)
            self.display_controller.display_number(self.channel_dialer.current_channel)
    
    def _handle_channel_up(self):
        print("📺 Channel UP!")
        self.channel_dialer.clear_queue()
        self.channel_dialer.channel_up()
    
    def _handle_channel_down(self):
        print("📺 Channel DOWN!")
        self.channel_dialer.clear_queue()
        self.channel_dialer.channel_down()
    
    def _handle_effect_next(self):
        print("✨ Next effect!")
        if self.display_controller:
            self.display_controller.display_text("EFuP")
            threading.Timer(0.5, lambda: self.display_controller.display_number(self.channel_dialer.current_channel)).start()
        send_key_to_mpv('c')
    
    def _handle_effect_prev(self):
        print("✨ Previous effect!")
        if self.display_controller:
            self.display_controller.display_text("EFdn")
            threading.Timer(0.5, lambda: self.display_controller.display_number(self.channel_dialer.current_channel)).start()
        send_key_to_mpv('z')
    
    def _handle_volume_up(self):
        print("🔊 Volume UP!")
        send_key_to_mpv('0')
    
    def _handle_volume_down(self):
        print("🔉 Volume DOWN!")
        send_key_to_mpv('9')
    
    def _handle_mute(self):
        print("🔇 Mute toggle!")
        send_key_to_mpv('m')
    
    def _handle_power(self):
        print("⚡ Power toggle!")
        if self.display_controller:
            self.display_controller.clear_display()
            time.sleep(0.5)
            self.display_controller.display_number(self.channel_dialer.current_channel)
        write_json_to_socket({"command": "power_toggle", "timestamp": time.time()})
    
    def _handle_pause(self):
        print("⏸️  Pause/Play toggle!")
        send_key_to_mpv('space')
    
    def _handle_info(self):
        print("ℹ️  Info display!")
        if self.display_controller:
            self.display_controller.display_text("INFO")
            time.sleep(1.5)
            self.display_controller.display_number(self.channel_dialer.current_channel)
        write_json_to_socket({"command": "info", "timestamp": time.time()})
    
    def _handle_menu(self):
        print("📋 Menu!")
        if self.display_controller:
            self.display_controller.display_text("MENU")
            time.sleep(1.5)
            self.display_controller.display_number(self.channel_dialer.current_channel)
        write_json_to_socket({"command": "menu", "timestamp": time.time()})
    
    def _handle_ok(self):
        print("✅ OK/Select!")
        send_key_to_mpv('Return')
    
    def _handle_back(self):
        print("⬅️  Back!")
        write_json_to_socket({"command": "back", "timestamp": time.time()})
    
    def _handle_digit(self, digit):
        print(f"{digit}️⃣ Digit {digit}")
        self.channel_dialer.add_digit(digit)
    
    def _handle_digital_analog(self):
        print("✨ Digital / Analog effect!")
        send_key_to_mpv('b')
    
    def _handle_unmapped_event(self, event_name):
        print(f"❓ Unmapped event: {event_name}")
    
    def _handle_unknown_event(self, event_name):
        print(f"❌ Unknown event: {event_name}")
    
    def handle_event(self, event_name, protocol=None, address=None, command=None):
        """Handle an IR event"""
        if event_name.startswith("UNMAPPED_"):
            self._handle_unmapped_event(event_name)
        elif event_name.startswith("UNKNOWN_"):
            self._handle_unknown_event(event_name)
        else:
            handler = self.event_handlers.get(event_name)
            if handler:
                handler()
            else:
                print(f"⚠️  No handler for event: {event_name}")
                write_json_to_socket({"command": "no_handler", "event": event_name})

        if self.args.verbose_unknowns and protocol and address and command:
            print(f"🔍 Raw IR: protocol={protocol}, address={address}, command={command}")
    
    def map_ir_signal(self, protocol, address, command):
        """Map IR signal to event name"""
        for remote_name, config in REMOTE_CONFIGS.items():
            if config["protocol"] == protocol and config["address"] == address:
                if command in config["mappings"]:
                    return config["mappings"][command], protocol, address, command
                else:
                    return f"UNMAPPED_{remote_name}_{command}", protocol, address, command
        return f"UNKNOWN_{protocol}_{address}_{command}", protocol, address, command
    
    def run(self):
        """Main run loop"""
        try:
            # Boot sequence
            self._boot_sequence()

            # Setup socket directory
            os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

            # Connect to Flipper
            self.flipper = serial.Serial(self.args.device, 115200, timeout=1)
            time.sleep(3)
            self.flipper.flushInput()

            self.flipper.write(b'\x03')
            time.sleep(1)
            self.flipper.flushInput()

            self.flipper.write(b'ir rx\r\n')

            # Startup messages
            print(f"Enhanced IR Remote Mapper ready on {self.args.device}...")
            print(f"Writing JSON to: {SOCKET_PATH}")
            print(f"Valid channels: {VALID_CHANNELS}")
            print(f"Current channel: {self.channel_dialer.current_channel}")
            print(f"Channel digit timeout: {self.args.digit_timeout}s")
            if self.display_controller and self.display_controller.display_serial:
                print(f"📟 Display: {self.args.display_device} @ {self.args.display_baud} baud")

            while True:
                line = self.flipper.readline().decode('utf-8').strip()
                if not line:
                    continue
                if self.args.debug:
                    print(f"DEBUG: '{line}'")
                if any(line.startswith(h) for h in ('ir rx', 'Receiving', 'Press Ctrl+C')):
                    continue

                ir_match = re.match(r'(\w+), A:(0x[0-9A-Fa-f]+), C:(0x[0-9A-Fa-f]+)', line)
                if ir_match:
                    protocol, address, command = ir_match.groups()
                    event, proto, addr, cmd = self.map_ir_signal(protocol, address, command)
                    current_time = time.time()

                    if event != self.last_event or (current_time - self.last_event_time) >= self.args.debounce:
                        self.handle_event(event, proto, addr, cmd)
                        self.last_event = event
                        self.last_event_time = current_time

        except KeyboardInterrupt:
            print("\nMapper stopped")
            self.channel_dialer.clear_queue()  # Clean up any pending timers
            if self.display_controller and self.display_controller.display_serial:
                self.display_controller.display_text("BYE")
                time.sleep(1)
                self.display_controller.clear_display()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            try:
                if self.flipper:
                    self.flipper.close()
            except:
                pass
            try:
                if self.display_controller and self.display_controller.display_serial:
                    self.display_controller.display_serial.close()
            except:
                pass
            if self.log_file:
                self.log_file.close()

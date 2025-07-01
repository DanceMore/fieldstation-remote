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

# Import our modular components
from display_controller import DisplayController
from display_queue import DisplayQueue
from channel_dialer import ChannelDialer, VALID_CHANNELS

# Import shared utilities
from utils import safe_execute, send_key_to_mpv, write_json_to_socket

SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
LOG_PATH = "/home/appuser/FieldStation42/runtime/ir_mapper.log"

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

        # set up logging early...
        self.log_file = None
        self._setup_logging()

        # set up hardware / comms...
        self.display_controller = None
        self.channel_dialer = None
        self.flipper = None
        
        # Event state
        self.last_event = None
        self.last_event_time = 0
        
        # Initialize components
        self._setup_display()
        self._setup_channel_dialer()
        self._setup_event_handlers()
        self.display_queue = DisplayQueue(self.display_controller)
        self.display_queue.start()
    
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
            self.display_queue.show_text("ACId")
            self.display_queue.show_text("BOOT")
            self.display_queue.sleep(0.5)
    
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
                self.display_queue.show_text("redY")
                self.display_queue.sleep(0.5)
                self.display_queue.show_number(self.channel_dialer.current_channel)

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

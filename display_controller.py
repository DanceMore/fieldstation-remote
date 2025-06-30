#!/usr/bin/env python3
"""
Display Controller - 7-segment display communication via serial
"""

import serial
import time
import threading


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

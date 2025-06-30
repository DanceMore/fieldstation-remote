#!/usr/bin/env python3
"""
7-segment display controller for IR Remote Mapper
"""

import serial
import time
import threading
from typing import Optional, Union


class DisplayController:
    """Handles 7-segment display communication via serial"""

    def __init__(self, device: Optional[str] = None, baudrate: int = 9600):
        """
        Initialize display controller
        
        Args:
            device: Serial device path (e.g., "/dev/ttyUSB0")
            baudrate: Serial communication baudrate
        """
        self.display_serial: Optional[serial.Serial] = None
        self.device = device
        self.baudrate = baudrate
        self.lock = threading.Lock()
        self.is_connected = False
        
        if device:
            self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the display serial device
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.device:
                self.display_serial = serial.Serial(
                    self.device, 
                    self.baudrate, 
                    timeout=1
                )
                time.sleep(0.1)  # Give display time to initialize
                self.is_connected = True
                print(f"📟 Display connected on {self.device}")
                
                # Test the display
                self.display_text("INIT")
                time.sleep(0.5)
                self.clear()
                return True
                
        except Exception as e:
            print(f"❌ Failed to connect to display: {e}")
            self.display_serial = None
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Safely disconnect from display"""
        try:
            if self.display_serial:
                self.display_serial.close()
                self.display_serial = None
                self.is_connected = False
                print("📟 Display disconnected")
        except Exception as e:
            print(f"❌ Error disconnecting display: {e}")
    
    def _send_command(self, command: str) -> bool:
        """
        Send command to display with error handling
        
        Args:
            command: Command string to send
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not self.is_connected or not self.display_serial:
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
            self.is_connected = False
            return False
    
    def display_text(self, text: str) -> bool:
        """
        Display text (up to 4 characters)
        
        Args:
            text: Text to display (will be truncated to 4 chars and uppercased)
            
        Returns:
            bool: True if successful, False otherwise
        """
        text = str(text)[:4].upper()  # Limit to 4 chars and uppercase
        return self._send_command(f"DISP:{text}")
    
    def display_number(self, number: Union[int, str]) -> bool:
        """
        Display number (up to 4 digits)
        
        Args:
            number: Number to display (int or str, preserves leading zeros for strings)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(number, str):
            # Preserve string format (including leading zeros)
            num_str = number[:4]
        else:
            # Convert number to string
            num_str = str(int(number))[:4]
        
        return self._send_command(f"DISP:{num_str}")
    
    def clear(self) -> bool:
        """
        Clear the display
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._send_command("DISP:CLR")
    
    def set_brightness(self, level: int) -> bool:
        """
        Set display brightness
        
        Args:
            level: Brightness level (0-7, will be clamped to valid range)
            
        Returns:
            bool: True if successful, False otherwise
        """
        level = max(0, min(7, int(level)))  # Clamp to 0-7
        return self._send_command(f"DISP:BRT:{level}")
    
    def turn_on(self) -> bool:
        """
        Turn display on
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._send_command("DISP:ON")
    
    def turn_off(self) -> bool:
        """
        Turn display off
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._send_command("DISP:OFF")
    
    def boot_sequence(self, sequence: list, final_display: Union[int, str] = 1):
        """
        Run boot sequence with timing
        
        Args:
            sequence: List of (text, delay_seconds) tuples
            final_display: Final value to display after sequence
        """
        for text, delay in sequence:
            self.display_text(text)
            time.sleep(delay)
        
        # Show final display value
        if isinstance(final_display, str):
            self.display_text(final_display)
        else:
            self.display_number(final_display)
    
    def show_temporarily(self, text: str, duration: float, return_to: Union[int, str]):
        """
        Show text temporarily, then return to previous display
        
        Args:
            text: Text to show temporarily
            duration: How long to show it (seconds)
            return_to: What to display after duration
        """
        def _delayed_return():
            time.sleep(duration)
            if isinstance(return_to, str):
                self.display_text(return_to)
            else:
                self.display_number(return_to)
        
        self.display_text(text)
        # Use timer to avoid blocking
        timer = threading.Timer(duration, _delayed_return)
        timer.start()
        return timer

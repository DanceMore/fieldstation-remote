"""
Flipper Zero serial communication wrapper for IR signal reception.
"""

import serial
import time
import re
from typing import Optional, Tuple, Iterator, NamedTuple


class IRSignal(NamedTuple):
    """Represents a parsed IR signal."""
    protocol: str
    address: str
    command: str
    raw_line: str


class FlipperZero:
    """
    Handles serial communication with Flipper Zero device for IR signal reception.
    """
    
    def __init__(self, device_path: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize Flipper Zero connection.
        
        Args:
            device_path: Serial device path (e.g., '/dev/ttyACM0')
            baudrate: Serial communication speed
            timeout: Serial read timeout in seconds
        """
        self.device_path = device_path
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_receiving = False
        
        # Pattern to match IR signals: Protocol, Address, Command
        self.ir_pattern = re.compile(r'(\w+), A:(0x[0-9A-Fa-f]+), C:(0x[0-9A-Fa-f]+)')
        
        # Lines to ignore during IR reception
        self.ignore_patterns = [
            'ir rx',
            'Receiving',
            'Press Ctrl+C',
            'Ready to receive',
            'Press CTRL+C to exit'
        ]
    
    def connect(self) -> bool:
        """
        Connect to the Flipper Zero device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                self.device_path, 
                self.baudrate, 
                timeout=self.timeout
            )
            
            # Wait for device to initialize
            time.sleep(3)
            self.serial_connection.flushInput()
            
            print(f"🐬 Connected to Flipper Zero on {self.device_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Flipper Zero: {e}")
            self.serial_connection = None
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the Flipper Zero device."""
        if self.serial_connection:
            try:
                if self.is_receiving:
                    self.stop_ir_reception()
                self.serial_connection.close()
                print("🐬 Disconnected from Flipper Zero")
            except Exception as e:
                print(f"❌ Error disconnecting: {e}")
            finally:
                self.serial_connection = None
    
    def send_command(self, command: str) -> bool:
        """
        Send a command to the Flipper Zero.
        
        Args:
            command: Command string to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.serial_connection:
            print("❌ No connection to Flipper Zero")
            return False
        
        try:
            # Send interrupt first to clear any current operation
            self.serial_connection.write(b'\x03')
            time.sleep(0.5)
            self.serial_connection.flushInput()
            
            # Send the actual command
            cmd_bytes = f"{command}\r\n".encode('utf-8')
            self.serial_connection.write(cmd_bytes)
            print(f"🐬 Sent command: {command}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False
    
    def start_ir_reception(self) -> bool:
        """
        Start IR signal reception mode.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not self.serial_connection:
            print("❌ No connection to Flipper Zero")
            return False
        
        try:
            # Send interrupt to clear any current state
            self.serial_connection.write(b'\x03')
            time.sleep(1)
            self.serial_connection.flushInput()
            
            # Start IR reception
            self.serial_connection.write(b'ir rx\r\n')
            self.is_receiving = True
            print("🐬 Started IR reception mode")
            return True
            
        except Exception as e:
            print(f"❌ Error starting IR reception: {e}")
            return False
    
    def stop_ir_reception(self) -> bool:
        """
        Stop IR signal reception mode.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.serial_connection:
            return False
        
        try:
            # Send interrupt to stop reception
            self.serial_connection.write(b'\x03')
            time.sleep(0.5)
            self.serial_connection.flushInput()
            self.is_receiving = False
            print("🐬 Stopped IR reception mode")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping IR reception: {e}")
            return False
    
    def read_line(self) -> Optional[str]:
        """
        Read a line from the serial connection.
        
        Returns:
            Optional[str]: Line read from device, None if no data or error
        """
        if not self.serial_connection:
            return None
        
        try:
            line = self.serial_connection.readline().decode('utf-8').strip()
            return line if line else None
        except Exception as e:
            print(f"❌ Error reading line: {e}")
            return None
    
    def parse_ir_signal(self, line: str) -> Optional[IRSignal]:
        """
        Parse an IR signal line.
        
        Args:
            line: Raw line from Flipper Zero
            
        Returns:
            Optional[IRSignal]: Parsed signal or None if not a valid IR signal
        """
        if not line:
            return None
        
        # Skip lines we should ignore
        if any(line.startswith(pattern) for pattern in self.ignore_patterns):
            return None
        
        # Try to match IR signal pattern
        match = self.ir_pattern.match(line)
        if match:
            protocol, address, command = match.groups()
            return IRSignal(protocol, address, command, line)
        
        return None
    
    def listen_for_signals(self, debug: bool = False) -> Iterator[IRSignal]:
        """
        Listen for IR signals and yield parsed signals.
        
        Args:
            debug: If True, print all raw lines received
            
        Yields:
            IRSignal: Parsed IR signals
        """
        if not self.is_receiving:
            print("❌ IR reception not started")
            return
        
        while self.is_receiving and self.serial_connection:
            try:
                line = self.read_line()
                if line is None:
                    continue
                
                if debug:
                    print(f"🐬 DEBUG: '{line}'")
                
                signal = self.parse_ir_signal(line)
                if signal:
                    yield signal
                    
            except KeyboardInterrupt:
                print("\n🐬 Signal listening interrupted")
                break
            except Exception as e:
                print(f"❌ Error in signal listening: {e}")
                break
    
    def is_connected(self) -> bool:
        """
        Check if connected to Flipper Zero.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.serial_connection is not None and self.serial_connection.is_open
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

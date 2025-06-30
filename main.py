#!/usr/bin/env python3
"""
IR Remote Mapper - Main Entry Point
Enhanced IR remote control system with channel dialing, Easter eggs, and 7-segment display
"""

import argparse
import signal
import sys
import time
import os

from config.settings import (
    FLIPPER_BAUDRATE, 
    DEFAULT_FLIPPER_DEVICE, 
    DEFAULT_DISPLAY_DEVICE,
    DEFAULT_DISPLAY_BAUDRATE,
    DEFAULT_DEBOUNCE_TIME,
    DEFAULT_DIGIT_TIMEOUT,
    DEFAULT_DISPLAY_BRIGHTNESS,
    VALID_CHANNELS
)
from devices.display import DisplayController
from devices.flipper import FlipperController
from features.channel_dialer import ChannelDialer
from core.mapper import IRMapper
from core.event_handler import EventHandler
from utils.logging import setup_logging


class IRRemoteMapperApp:
    """Main application class that coordinates all components"""
    
    def __init__(self, args):
        self.args = args
        self.running = False
        
        # Initialize components
        self.display_controller = None
        self.flipper_controller = None
        self.channel_dialer = None
        self.ir_mapper = None
        self.event_handler = None
        self.log_file = None
        
        # State tracking for debouncing
        self.last_event = None
        self.last_event_time = 0
        
    def initialize_components(self):
        """Initialize all system components"""
        try:
            # Setup logging first
            self.log_file = setup_logging(self.args.log_to_file)
            
            # Initialize display controller
            print("🔌 Initializing display controller...")
            self.display_controller = DisplayController(
                device=self.args.display_device,
                baudrate=self.args.display_baud
            )
            
            if self.display_controller.is_connected():
                self.display_controller.set_brightness(self.args.display_brightness)
                self.display_controller.turn_on()
                print(f"📟 Display connected on {self.args.display_device}")
            else:
                print("⚠️  Display not connected - continuing without display")
            
            # Initialize channel dialer
            print("📺 Initializing channel dialer...")
            self.channel_dialer = ChannelDialer(
                digit_timeout=self.args.digit_timeout,
                display_controller=self.display_controller
            )
            
            # Initialize event handler
            print("🎮 Initializing event handler...")
            self.event_handler = EventHandler(
                channel_dialer=self.channel_dialer,
                display_controller=self.display_controller
            )
            
            # Initialize IR mapper
            print("🔍 Initializing IR mapper...")
            self.ir_mapper = IRMapper()
            
            # Initialize Flipper controller
            print(f"📡 Connecting to Flipper Zero on {self.args.device}...")
            self.flipper_controller = FlipperController(
                device=self.args.device,
                baudrate=FLIPPER_BAUDRATE
            )
            
            if not self.flipper_controller.connect():
                raise Exception("Failed to connect to Flipper Zero")
                
            print("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            return False
    
    def run_boot_sequence(self):
        """Run the boot sequence on the display"""
        if not self.display_controller or not self.display_controller.is_connected():
            return
            
        print("🚀 Running boot sequence...")
        sequences = [
            ("----", 0.8),
            ("ACId", 0.4), 
            ("BOOT", 2.0),
            ("redY", 1.5)
        ]
        
        for text, delay in sequences:
            self.display_controller.display_text(text)
            time.sleep(delay)
        
        # Show initial channel
        self.display_controller.display_number(self.channel_dialer.current_channel)
        print(f"📺 Boot complete - Channel {self.channel_dialer.current_channel}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def should_process_event(self, event_name):
        """Check if event should be processed based on debouncing"""
        current_time = time.time()
        
        if (event_name != self.last_event or 
            (current_time - self.last_event_time) >= self.args.debounce):
            self.last_event = event_name
            self.last_event_time = current_time
            return True
        return False
    
    def process_ir_line(self, line):
        """Process a line of IR data from Flipper Zero"""
        if self.args.debug:
            print(f"DEBUG: '{line}'")
        
        # Skip header lines
        if any(line.startswith(h) for h in ('ir rx', 'Receiving', 'Press Ctrl+C')):
            return
        
        # Try to parse IR signal
        ir_data = self.ir_mapper.parse_ir_line(line)
        if not ir_data:
            return
        
        # Map IR signal to event
        event_name = self.ir_mapper.map_signal_to_event(
            ir_data['protocol'], 
            ir_data['address'], 
            ir_data['command']
        )
        
        # Check debouncing
        if not self.should_process_event(event_name):
            return
        
        # Handle the event
        self.event_handler.handle_event(
            event_name=event_name,
            protocol=ir_data['protocol'] if self.args.verbose_unknowns else None,
            address=ir_data['address'] if self.args.verbose_unknowns else None,
            command=ir_data['command'] if self.args.verbose_unknowns else None
        )
    
    def run_main_loop(self):
        """Main event processing loop"""
        print("🎯 Starting main event loop...")
        print(f"📡 Listening on {self.args.device}")
        print(f"📺 Valid channels: {VALID_CHANNELS}")
        print(f"📺 Current channel: {self.channel_dialer.current_channel}")
        print(f"⏱️  Channel digit timeout: {self.args.digit_timeout}s")
        print(f"⏱️  Event debounce: {self.args.debounce}s")
        if self.display_controller and self.display_controller.is_connected():
            print(f"📟 Display: {self.args.display_device} @ {self.args.display_baud} baud")
        print("🎮 Ready for IR commands!")
        print("Press Ctrl+C to stop...")
        
        self.running = True
        
        try:
            # Start IR receiving mode
            if not self.flipper_controller.start_ir_receive():
                raise Exception("Failed to start IR receive mode")
            
            # Main processing loop
            while self.running:
                line = self.flipper_controller.read_line()
                if line:
                    self.process_ir_line(line)
                else:
                    # Small sleep to prevent busy waiting
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
        except Exception as e:
            print(f"💥 Main loop error: {e}")
    
    def shutdown(self):
        """Graceful shutdown of all components"""
        print("🔄 Shutting down...")
        self.running = False
        
        # Clean up channel dialer timers
        if self.channel_dialer:
            print("📺 Cleaning up channel dialer...")
            self.channel_dialer.clear_queue()
        
        # Show goodbye message on display
        if self.display_controller and self.display_controller.is_connected():
            print("📟 Displaying goodbye message...")
            self.display_controller.display_text("BYE")
            time.sleep(1)
            self.display_controller.clear_display()
            self.display_controller.disconnect()
        
        # Close Flipper connection
        if self.flipper_controller:
            print("📡 Closing Flipper connection...")
            self.flipper_controller.disconnect()
        
        # Close log file
        if self.log_file:
            print("📝 Closing log file...")
            self.log_file.close()
        
        print("✅ Shutdown complete")
    
    def run(self):
        """Main application entry point"""
        try:
            # Initialize all components
            if not self.initialize_components():
                return 1
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Run boot sequence
            self.run_boot_sequence()
            
            # Run main loop
            self.run_main_loop()
            
            return 0
            
        except Exception as e:
            print(f"💥 Application error: {e}")
            return 1
        finally:
            self.shutdown()


def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description='Enhanced IR Remote Event Mapper with Channel Dialing and 7-Segment Display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Use default settings
  %(prog)s --device /dev/ttyACM1        # Use different Flipper device
  %(prog)s --display-device /dev/ttyUSB0 # Use different display device
  %(prog)s --debug --verbose-unknowns   # Enable debug output
  %(prog)s --digit-timeout 2.0          # Longer digit sequence timeout
        """
    )
    
    # Device configuration
    device_group = parser.add_argument_group('Device Configuration')
    device_group.add_argument(
        '--device', '-d',
        default=DEFAULT_FLIPPER_DEVICE,
        help=f'Flipper Zero serial device (default: {DEFAULT_FLIPPER_DEVICE})'
    )
    device_group.add_argument(
        '--display-device',
        default=DEFAULT_DISPLAY_DEVICE,
        help=f'7-segment display serial device (default: {DEFAULT_DISPLAY_DEVICE})'
    )
    device_group.add_argument(
        '--display-baud',
        type=int,
        default=DEFAULT_DISPLAY_BAUDRATE,
        help=f'Display serial baudrate (default: {DEFAULT_DISPLAY_BAUDRATE})'
    )
    
    # Timing configuration
    timing_group = parser.add_argument_group('Timing Configuration')
    timing_group.add_argument(
        '--debounce', '-t',
        type=float,
        default=DEFAULT_DEBOUNCE_TIME,
        help=f'Event debounce time in seconds (default: {DEFAULT_DEBOUNCE_TIME})'
    )
    timing_group.add_argument(
        '--digit-timeout',
        type=float,
        default=DEFAULT_DIGIT_TIMEOUT,
        help=f'Channel digit sequence timeout in seconds (default: {DEFAULT_DIGIT_TIMEOUT})'
    )
    
    # Display configuration
    display_group = parser.add_argument_group('Display Configuration')
    display_group.add_argument(
        '--display-brightness',
        type=int,
        default=DEFAULT_DISPLAY_BRIGHTNESS,
        choices=range(8),
        help=f'Initial display brightness 0-7 (default: {DEFAULT_DISPLAY_BRIGHTNESS})'
    )
    
    # Debug and logging
    debug_group = parser.add_argument_group('Debug and Logging')
    debug_group.add_argument(
        '--debug',
        action='store_true',
        help='Show raw IR data from Flipper Zero'
    )
    debug_group.add_argument(
        '--verbose-unknowns',
        action='store_true',
        help='Print protocol/address/command for unknown IR signals'
    )
    debug_group.add_argument(
        '--log-to-file',
        action='store_true',
        help='Log output to file instead of terminal'
    )
    
    return parser


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Print startup banner
    print("🎮 IR Remote Mapper - Enhanced Edition")
    print("=" * 50)
    
    # Create and run application
    app = IRRemoteMapperApp(args)
    exit_code = app.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

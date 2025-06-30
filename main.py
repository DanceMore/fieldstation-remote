#!/usr/bin/env python3
"""
IR Remote Mapper - Main Entry Point
Handles command line arguments and starts the IR mapper
"""

import argparse
from flipper_ir_remote import IRRemoteMapper

def main():
    parser = argparse.ArgumentParser(description='Enhanced IR Remote Event Mapper with Channel Dialing and 7-Segment Display')
    parser.add_argument('--device', '-d', default='/dev/ttyACM0',
                        help='Flipper Zero serial device')
    parser.add_argument('--display-device', default='/dev/ttyACM0',
                        help='7-segment display serial device (e.g., /dev/ttyUSB0)')
    parser.add_argument('--display-baud', type=int, default=115200,
                        help='Display serial baudrate')
    parser.add_argument('--debug', action='store_true',
                        help='Show raw IR data')
    parser.add_argument('--debounce', '-t', type=float, default=0.7,
                        help='Debounce time in seconds')
    parser.add_argument('--digit-timeout', type=float, default=1.5,
                        help='Timeout for digit sequence in seconds')
    parser.add_argument('--log-to-file', action='store_true',
                        help='Log output to file instead of terminal')
    parser.add_argument('--verbose-unknowns', action='store_true',
                        help='Print protocol/address/command for unknown signals')
    parser.add_argument('--display-brightness', type=int, default=7, choices=range(8),
                        help='Initial display brightness (0-7)')
    
    args = parser.parse_args()
    
    # Create and run the IR mapper
    mapper = IRRemoteMapper(args)
    mapper.run()

if __name__ == "__main__":
    main()

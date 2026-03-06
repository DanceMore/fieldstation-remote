import unittest
import os
import sys
from unittest.mock import MagicMock, patch
from flipper_ir_remote import IRRemoteMapper

# Set mock environment
os.environ["MOCK_MODE"] = "true"

class MockArgs:
    def __init__(self):
        self.device = 'mock_device'
        self.display_device = None
        self.display_baud = 115200
        self.debug = True
        self.debounce = 0.1
        self.digit_timeout = 0.5
        self.log_to_file = False
        self.verbose_unknowns = True
        self.display_brightness = 7
        self.mock = True
        self.chaos = True

class TestResilience(unittest.TestCase):
    def test_garbage_resilience(self):
        """Feed 100 consecutive lines of random garbage to IRRemoteMapper and assert no exceptions"""
        args = MockArgs()
        mapper = IRRemoteMapper(args)

        # Mock serial device
        mock_serial = MagicMock()
        mapper.flipper = mock_serial

        garbage_data = [
            b"NEC, A:0xZZ, C:0x11\r\n",       # Malformed Hex
            b"Samsung32, A:0x07\r\n",         # Partial Line
            b"UNKNOWN_PROTO, A:0x01, C:0x02\r\n", # Protocol Violation
            b"\xff\xfe\xfd\xaa\xbb\xcc\r\n",   # Random non-ASCII noise
            b"Short\r\n",                      # Very short line
            b"\r\n",                           # Empty line
            b"NEC, A:0x32, C:0x00\r\n",        # Valid signal mixed in
        ]

        # Create 100 lines of random garbage
        import random
        test_lines = [random.choice(garbage_data) for _ in range(100)]

        # Generator for side_effect to return lines one by one
        def line_generator():
            for line in test_lines:
                yield line
            # After 100 lines, raise KeyboardInterrupt to stop the mapper's run loop
            raise KeyboardInterrupt()

        mock_serial.readline.side_effect = line_generator()

        # Run the mapper - it should handle all garbage without crashing
        # and eventually stop when KeyboardInterrupt is raised
        try:
            with patch('utils.sleep', return_value=None): # Speed up the test
                with patch('serial.Serial', return_value=mock_serial):
                    mapper.run()
        except Exception as e:
            self.fail(f"IRRemoteMapper.run() raised an unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()

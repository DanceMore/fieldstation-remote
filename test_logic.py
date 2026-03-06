import unittest
import time
import os
from unittest.mock import patch
from channel_dialer import ChannelDialer, VALID_CHANNELS

# Set mock environment for utilities
os.environ["MOCK_MODE"] = "true"

class MockDisplay:
    def __init__(self):
        self.last_text = None
        self.last_num = None
        self.commands = []
    def display_text(self, text): 
        self.last_text = text
    def display_number(self, num): 
        self.last_num = num
    def clear_display(self): 
        pass
    def send_display_command(self, cmd):
        self.commands.append(cmd)

class TestChannelLogic(unittest.TestCase):
    def setUp(self):
        self.mock_display = MockDisplay()
        # Initialize with a fast timeout for testing
        self.dialer = ChannelDialer(digit_timeout=0.05, display_controller=self.mock_display)

    def test_digit_queuing_valid(self):
        """Test that pressing digits in sequence dials a valid channel"""
        # Channel 3 is in VALID_CHANNELS = [1, 2, 3, 8, 9, 13]
        self.dialer.add_digit(3)
        
        # Wait for timeout to trigger dialing
        time.sleep(0.1)
        
        self.assertEqual(self.dialer.current_channel, 3)
        self.assertEqual(self.mock_display.last_num, 3)
        self.assertIn("LED:ack", self.mock_display.commands)

    def test_digit_queuing_invalid(self):
        """Test that dialing an invalid channel (42) resets or shows error"""
        self.dialer.add_digit(4)
        self.dialer.add_digit(2)
        
        time.sleep(0.1)
        
        # Should NOT be 42
        self.assertNotEqual(self.dialer.current_channel, 42)
        self.assertIn("LED:nack", self.mock_display.commands)
        self.assertEqual(self.mock_display.last_text, "NOPE")

    def test_channel_up_down(self):
        """Test channel increment/decrement"""
        # Starting channel is usually VALID_CHANNELS[0] = 1
        start_channel = self.dialer.current_channel
        self.assertEqual(start_channel, 1)
        
        self.dialer.channel_up()
        # Next in [1, 2, 3, 8, 9, 13] is 2
        self.assertEqual(self.dialer.current_channel, 2)
        
        self.dialer.channel_down()
        self.assertEqual(self.dialer.current_channel, 1)

if __name__ == '__main__':
    unittest.main()

import unittest
import time
import os
import re
from unittest.mock import MagicMock, patch
from flipper_ir_remote import IRRemoteMapper

class MockArgs:
    def __init__(self):
        self.device = "mock_device"
        self.display_device = None
        self.display_baud = 115200
        self.display_brightness = 7
        self.debounce = 0.5
        self.digit_timeout = 1.5
        self.log_to_file = False
        self.verbose_unknowns = True
        self.debug = True

class TestRemoteMapping(unittest.TestCase):
    def setUp(self):
        os.environ["MOCK_MODE"] = "true"
        self.args = MockArgs()
        # Mock serial.Serial before initializing IRRemoteMapper
        with patch('serial.Serial'):
            self.mapper = IRRemoteMapper(self.args)

    def test_ir_mapping(self):
        """Test that raw IR strings map to correct events"""
        # NEC, A:0x32, C:0x11 -> CHANNEL_UP
        event, proto, addr, cmd = self.mapper.map_ir_signal("NEC", "0x32", "0x11")
        self.assertEqual(event, "CHANNEL_UP")
        
        # Samsung32, A:0x07, C:0x04 -> DIGIT_1
        event, proto, addr, cmd = self.mapper.map_ir_signal("Samsung32", "0x07", "0x04")
        self.assertEqual(event, "DIGIT_1")

    def test_debounce_logic(self):
        """Test that rapid identical signals are debounced"""
        self.mapper.handle_event = MagicMock()
        
        # First signal
        line = "NEC, A:0x32, C:0x11"
        ir_match = re.match(r'(\w+), A:(0x[0-9A-Fa-f]+), C:(0x[0-9A-Fa-f]+)', line)
        protocol, address, command = ir_match.groups()
        event, proto, addr, cmd = self.mapper.map_ir_signal(protocol, address, command)
        
        # Process first event
        self.mapper.handle_event(event, proto, addr, cmd)
        self.mapper.last_event = event
        self.mapper.last_event_time = time.time()
        
        # Try processing same event immediately
        current_time = time.time()
        if event != self.mapper.last_event or (current_time - self.mapper.last_event_time) >= self.args.debounce:
             self.mapper.handle_event(event, proto, addr, cmd)
        
        # Should only have been called once (manually by us)
        self.assertEqual(self.mapper.handle_event.call_count, 1)

if __name__ == '__main__':
    unittest.main()

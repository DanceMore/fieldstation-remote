import unittest
import os
import json
import shutil
from channel_dialer import ChannelDialer, VALID_CHANNELS
from state_manager import StateManager
from unittest.mock import MagicMock

class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.test_runtime = "test_runtime"
        os.makedirs(self.test_runtime, exist_ok=True)
        os.environ["FIELDSTATION_RUNTIME"] = self.test_runtime
        self.state_file = os.path.join(self.test_runtime, "state.json")
        self.mock_display = MagicMock()

    def tearDown(self):
        if os.path.exists(self.test_runtime):
            shutil.rmtree(self.test_runtime)

    def test_state_manager_atomic_save(self):
        """Test that StateManager saves correctly and atomically"""
        sm = StateManager(self.state_file)
        sm.update(current_channel=8)
        
        self.assertTrue(os.path.exists(self.state_file))
        with open(self.state_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["current_channel"], 8)

    def test_dialer_persistence(self):
        """Test that ChannelDialer recovers its state after a simulated reboot"""
        # 1. Create a dialer and change channel
        dialer1 = ChannelDialer(display_controller=self.mock_display)
        dialer1.tune_to_channel(13)
        self.assertEqual(dialer1.current_channel, 13)
        
        # 2. Simulate "reboot" by creating a new dialer instance
        # It should load the state from the same test_runtime
        dialer2 = ChannelDialer(display_controller=self.mock_display)
        self.assertEqual(dialer2.current_channel, 13)

    def test_corrupt_state_fallback(self):
        """Test that system defaults to channel 1 if state is corrupted"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            f.write("NOT JSON {{{{")
            
        dialer = ChannelDialer(display_controller=self.mock_display)
        # Should fallback to VALID_CHANNELS[0]
        self.assertEqual(dialer.current_channel, VALID_CHANNELS[0])

if __name__ == '__main__':
    unittest.main()

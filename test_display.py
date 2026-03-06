import unittest
import time
import threading
from unittest.mock import MagicMock
import utils
from display_queue import DisplayQueue

class MockDisplayController:
    def __init__(self):
        self.received = []
    def display_text(self, text): self.received.append(("text", text))
    def display_number(self, num): self.received.append(("number", num))
    def clear_display(self): self.received.append(("clear", None))
    def set_brightness(self, level): self.received.append(("brightness", level))

class TestDisplayQueue(unittest.TestCase):
    def setUp(self):
        self.controller = MockDisplayController()
        self.dq = DisplayQueue(self.controller)
        
        # Virtual time setup
        self.virtual_time = 1000.0
        utils.set_time_source(lambda: self.virtual_time)
        # Note: We keep real sleep for the queue.get() timeout in the worker thread,
        # but our puppeteered utils.sleep will be used for the 'sleep' command logic.
        self.original_sleep = utils._sleep_source
        utils.set_sleep_source(self._mock_sleep)

    def _mock_sleep(self, seconds):
        self.virtual_time += seconds

    def tearDown(self):
        self.dq.stop()
        utils.set_time_source(time.time)
        utils.set_sleep_source(self.original_sleep)

    def test_queue_processing(self):
        """Test that commands are processed in background"""
        self.dq.start()
        
        self.dq.show_text("HI")
        self.dq.show_number(42)
        
        # Give the thread a moment to process (real time)
        # We use real time for the wait because the Queue.get() is real-time
        deadline = time.time() + 2
        while len(self.controller.received) < 2 and time.time() < deadline:
            time.sleep(0.01)
            
        self.assertEqual(self.controller.received, [("text", "HI"), ("number", 42)])

    def test_sleep_command(self):
        """Test that the sleep command uses the puppeteered sleep"""
        self.dq.start()
        
        start_time = self.virtual_time
        self.dq.sleep(5.0)
        self.dq.show_text("DONE")
        
        # Wait for "DONE" to appear
        deadline = time.time() + 2
        while len(self.controller.received) < 1 and time.time() < deadline:
            time.sleep(0.01)
            
        # The virtual time should have jumped by 5.0 in the worker thread
        self.assertGreaterEqual(self.virtual_time - start_time, 5.0)
        self.assertEqual(self.controller.received, [("text", "DONE")])

if __name__ == '__main__':
    unittest.main()

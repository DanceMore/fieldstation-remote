import unittest
import threading
from unittest.mock import MagicMock
import utils
from channel_dialer import ChannelDialer

class MockClock:
    def __init__(self, start_time=1000000.0):
        self.current_time = start_time
    def time(self):
        return self.current_time
    def sleep(self, seconds):
        # We don't advance time on sleep in these tests to avoid debounce
        pass

class TestTimeSensitiveLogic(unittest.TestCase):
    def setUp(self):
        self.mock_clock = MockClock()
        self.mock_display = MagicMock()
        
        # Capture timers
        self.timers = []
        
        # Install transparent interception hooks
        utils.set_time_source(self.mock_clock.time)
        utils.set_sleep_source(self.mock_clock.sleep)
        utils.set_timer_source(self._mock_timer)

        self.dialer = ChannelDialer(digit_timeout=1.5, display_controller=self.mock_display)

    def tearDown(self):
        # Restore real sources
        import time
        utils.set_time_source(time.time)
        utils.set_sleep_source(time.sleep)
        utils.set_timer_source(threading.Timer)

    def _mock_timer(self, interval, function, args=None, kwargs=None):
        timer = MagicMock()
        timer.interval = interval
        timer.function = function
        timer.args = args or []
        timer.kwargs = kwargs or {}
        timer.cancel = MagicMock()
        self.timers.append(timer)
        return timer

    def _trigger_timers(self, interval=None):
        """Trigger timers. If interval is provided, only trigger those."""
        current_timers = list(self.timers)
        for t in current_timers:
            if interval is None or t.interval == interval:
                if t in self.timers:
                    self.timers.remove(t)
                t.function(*t.args, **t.kwargs)

    def test_easter_egg_cooldown_long(self):
        """Test long cooldown display format (MMSS)"""
        # 911 has 1 hour (3600s) cooldown
        self.dialer.add_digit(9)
        self.dialer.add_digit(1)
        self.dialer.add_digit(1)
        self._trigger_timers(interval=1.5)
        
        self.mock_display.send_display_command.assert_any_call("LED:red-blue 10")
        self.mock_display.send_display_command.reset_mock()
        
        # Advance time 10s
        self.mock_clock.current_time += 10.0
        
        self.dialer.add_digit(9)
        self.dialer.add_digit(1)
        self.dialer.add_digit(1)
        self._trigger_timers(interval=1.5)
        
        # 3600 - 10 = 3590s = 59 minutes, 50 seconds -> "5950"
        self.mock_display.send_display_command.assert_any_call("DISP:5950")
        self.mock_display.send_display_command.assert_any_call("LED:nack")

    def test_easter_egg_cooldown_short(self):
        """Test short cooldown display format (00SS)"""
        # 8888 has 5s cooldown
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self._trigger_timers(interval=1.5)
        
        self.mock_display.send_display_command.assert_any_call("DISP:8888")
        self.mock_display.send_display_command.reset_mock()
        
        # Advance time 3s (past 2s debounce but within 5s cooldown)
        self.mock_clock.current_time += 3.0
        
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self.dialer.add_digit(8)
        self._trigger_timers(interval=1.5)
        
        # 5 - 3 = 2s = 0 minutes, 2 seconds -> "0002"
        self.mock_display.send_display_command.assert_any_call("DISP:0002")
        self.mock_display.send_display_command.assert_any_call("LED:nack")

    def test_effect_duration_cleanup(self):
        self.timers = []
        self.dialer.add_digit(9)
        self.dialer.add_digit(1)
        self.dialer.add_digit(1)
        self._trigger_timers(interval=1.5) 
        
        # Find 10s cleanup timer
        self.mock_display.send_display_command.reset_mock()
        self._trigger_timers(interval=10)
        self.mock_display.send_display_command.assert_any_call("LED:off")

if __name__ == '__main__':
    unittest.main()

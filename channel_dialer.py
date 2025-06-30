#!/usr/bin/env python3
"""
Channel Dialer - Intelligent digit queue system for channel switching
"""

import time
import threading
import subprocess
import json
from collections import deque
from contextlib import contextmanager

# Configuration
VALID_CHANNELS = [1, 2, 3, 8, 9, 13]
SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
DIGIT_TIMEOUT = 1.5
DISPLAY_DELAY = 0.4

# Easter egg configurations
EASTER_EGGS = {
    "911": ("🚨 EMERGENCY!", "911!", lambda self: send_key_to_mpv('c')),
    "666": ("😈 DEMON MODE!", "666", lambda self: None),
    "420": ("🎉 PARTY TIME!", "420", lambda self: None),
    "777": ("🍀 LUCKY!", "777", lambda self: None),
    "1234": ("🧪 TEST MODE!", "TEST", lambda self: None),
    "0000": ("🔄 RESET!", "RST", lambda self: self._reset_to_first_channel()),
    "404": ("💥 ERROR!", "404", lambda self: self._show_error("404")),
    "80085": ("😄 FUN TIME!", "BOOB", lambda self: None),
}

def safe_execute(func, error_msg="Operation failed"):
    """Decorator for safe function execution with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"{error_msg}: {e}")
            return None
    return wrapper

@safe_execute
def write_json_to_socket(data):
    """Write JSON data to socket"""
    json_str = json.dumps(data)
    with open(SOCKET_PATH, 'w') as f:
        f.write(json_str)
    print(f"JSON written: {json_str}")

@safe_execute
def send_key_to_mpv(key):
    """Send key to mpv window"""
    window_id = subprocess.check_output(
        ['xdotool', 'search', '--onlyvisible', '--class', 'mpv'],
        env={'DISPLAY': ':0'}
    ).decode().strip().split('\n')[0]
    subprocess.run(['xdotool', 'key', '--window', window_id, key], env={'DISPLAY': ':0'})

class ChannelDialer:
    def __init__(self, digit_timeout=DIGIT_TIMEOUT, display_controller=None):
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = VALID_CHANNELS[0]  # Start with first valid channel

    @contextmanager
    def _safe_lock(self):
        """Context manager for safe locking with cleanup"""
        acquired = False
        try:
            self.lock.acquire()
            acquired = True
            yield
        except Exception as e:
            print(f"Lock operation error: {e}")
            # Force cleanup on error
            try:
                self.digit_queue.clear()
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
            except:
                pass
        finally:
            if acquired:
                self.lock.release()

    def _update_display(self, value, is_text=False):
        """Update display with error handling"""
        if not self.display:
            return
        try:
            if is_text:
                self.display.display_text(value)
            else:
                self.display.display_number(value)
        except Exception as e:
            print(f"Display update error: {e}")

    def _cancel_timer(self):
        """Safely cancel existing timer"""
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def _get_current_sequence(self):
        """Get current digit sequence as string"""
        return ''.join(self.digit_queue)

    def _execute_easter_egg(self, sequence):
        """Execute easter egg with proper error handling"""
        if sequence not in EASTER_EGGS:
            return False

        message, display_text, action = EASTER_EGGS[sequence]
        print(f"🎯 {message}")
        self._update_display(display_text, is_text=True)

        if callable(action):
            try:
                action(self)
            except Exception as e:
                print(f"⚠️ Easter egg action failed: {e}")

        time.sleep(1)
        self._update_display(self.current_channel)
        return True

    def _reset_to_first_channel(self):
        """Reset to first valid channel"""
        self.current_channel = VALID_CHANNELS[0]

    def add_digit(self, digit):
        """Add digit to queue and manage timing"""
        with self._safe_lock():
            self.digit_queue.append(str(digit))
            self.last_digit_time = time.time()

            current_sequence = self._get_current_sequence()
            self._update_display(current_sequence)

            self._cancel_timer()

            # Check for immediate Easter egg matches
            if self._execute_easter_egg(current_sequence):
                self.digit_queue.clear()
                print("🎮 Ready for new input...")
                return

            # Set timer for regular channel processing
            self.timer = threading.Timer(self.digit_timeout, self._process_channel)
            self.timer.start()

    def clear_queue(self):
        """Clear the digit queue"""
        with self._safe_lock():
            self.digit_queue.clear()
            self._cancel_timer()
            self._update_display(self.current_channel)

    def _process_channel(self):
        """Process accumulated digits as channel number"""
        with self._safe_lock():
            if not self.digit_queue:
                return

            channel_str = self._get_current_sequence()

            # Final Easter egg check
            if self._execute_easter_egg(channel_str):
                self.digit_queue.clear()
                self.timer = None
                return

            # Process as channel number
            try:
                channel_num = int(channel_str)
                self.tune_to_channel(channel_num)
            except ValueError:
                self._show_error("ERR")

            self.digit_queue.clear()
            self.timer = None

    def _show_error(self, error_text):
        """Show error message briefly then return to current channel"""
        print(f"❌ Invalid channel sequence")
        self._update_display(error_text, is_text=True)
        time.sleep(1)
        self._update_display(self.current_channel)

    def tune_to_channel(self, channel):
        """Tune to specific channel with validation"""
        print(f"📺 Attempting to tune to channel {channel}")

        is_valid = channel in VALID_CHANNELS

        if is_valid:
            print(f"✅ Valid channel: {channel}")
            self.current_channel = channel
            self._update_display(channel)
        else:
            print(f"❌ Invalid channel: {channel}")
            self._show_error("NOPE")

        # Send command regardless - let TV decide final behavior
        write_json_to_socket({
            "command": "direct",
            "channel": channel,
            "valid": is_valid,
            "fallback_channel": self.current_channel if not is_valid else None,
            "timestamp": time.time()
        })

    def _change_channel(self, direction):
        """Generic channel change handler"""
        display_text = "UP" if direction > 0 else "Dn"
        self._update_display(display_text, is_text=True)
        time.sleep(DISPLAY_DELAY)

        # Calculate new channel index
        try:
            current_idx = VALID_CHANNELS.index(self.current_channel)
        except ValueError:
            current_idx = 0

        new_idx = (current_idx + direction) % len(VALID_CHANNELS)
        new_channel = VALID_CHANNELS[new_idx]

        print(f"📺 Channel {display_text}: {self.current_channel} -> {new_channel}")
        self.current_channel = new_channel
        self._update_display(self.current_channel)

        write_json_to_socket({
            "command": "up" if direction > 0 else "down",
            "channel": self.current_channel,
            "timestamp": time.time()
        })

    def channel_up(self):
        """Handle channel up"""
        self._change_channel(1)

    def channel_down(self):
        """Handle channel down"""
        self._change_channel(-1)

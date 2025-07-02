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

# Import utilities
from utils import safe_execute, write_json_to_socket

# Import Easter egg system
from easter_eggs import EasterEggCooldownManager, EasterEggActions, EasterEggRegistry

# Configuration
VALID_CHANNELS = [1, 2, 3, 8, 9, 13]
SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
DIGIT_TIMEOUT = 1.5
DISPLAY_DELAY = 0.4

class ChannelDialer:
    def __init__(self, digit_timeout=DIGIT_TIMEOUT, display_controller=None):
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = VALID_CHANNELS[0]
        
        # Add Easter egg protection
        self.last_easter_egg_time = 0
        self.easter_egg_debounce = 2.0  # 2 second cooldown after Easter egg

        # Initialize cooldown manager first
        self.cooldown_manager = EasterEggCooldownManager()
        
        # Initialize Easter egg system
        self.easter_actions = EasterEggActions(self)
        self.easter_registry = EasterEggRegistry(self.easter_actions)

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

    def _is_in_easter_egg_debounce(self):
        """Check if we're still in Easter egg debounce period"""
        return (time.time() - self.last_easter_egg_time) < self.easter_egg_debounce

    def _execute_easter_egg(self, sequence):
        """Execute Easter egg with proper error handling and cooldown"""
        if not self.easter_registry.is_easter_egg(sequence):
            return False

        easter_egg = self.easter_registry.get_easter_egg(sequence)
        print(f"🎯 {easter_egg['message']}")
        self._update_display(easter_egg['display'], is_text=True)

        try:
            easter_egg['action']()
        except Exception as e:
            print(f"⚠️ Easter egg action failed: {e}")

        # Set cooldown timestamp
        self.last_easter_egg_time = time.time()
        
        time.sleep(1)
        self._update_display(self.current_channel)
        return True

    def _reset_to_first_channel(self):
        """Reset to first valid channel"""
        self.current_channel = VALID_CHANNELS[0]

    def add_digit(self, digit):
        """Add digit to queue and manage timing"""
        with self._safe_lock():
            # Ignore digits during Easter egg debounce
            if self._is_in_easter_egg_debounce():
                print(f"🔄 Ignoring digit {digit} - Easter egg debounce active")
                return

            self.digit_queue.append(str(digit))
            self.last_digit_time = time.time()

            current_sequence = self._get_current_sequence()
            self._update_display(current_sequence)

            self._cancel_timer()  # Cancel any existing timer

            # Check for immediate Easter egg matches
            if self._execute_easter_egg(current_sequence):
                self.digit_queue.clear()
                self._cancel_timer()  # Double-cancel to be absolutely sure
                print("🎮 Ready for new input...")
                return

            # Set timer for regular channel processing
            self.timer = threading.Timer(self.digit_timeout, self._process_channel)
            self.timer.start()

    def clear_queue(self):
        """Clear the digit queue and reset cooldown"""
        with self._safe_lock():
            self.digit_queue.clear()
            self._cancel_timer()
            # Reset Easter egg debounce when manually clearing
            self.last_easter_egg_time = 0
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
        self.display.send_display_command("LED:ack")

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
        self.display.send_display_command("LED:ack")

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

    def trigger_immediate_easter_egg(self, easter_egg_id):
        """Trigger an immediate Easter egg (for button presses, not dialing)"""
        easter_egg = self.easter_registry.trigger_immediate_easter_egg(easter_egg_id)
        if not easter_egg:
            print(f"❌ Unknown immediate Easter egg: {easter_egg_id}")
            return False

        # Check cooldown
        if not self.cooldown_manager.can_activate(easter_egg_id, easter_egg['cooldown']):
            remaining = self.cooldown_manager.get_time_until_available(easter_egg_id, easter_egg['cooldown'])
            print(f"⏳ {easter_egg_id} still in cooldown ({remaining:.1f}s remaining)")
            return False

        print(f"🎯 {easter_egg['message']}")
        self._update_display(easter_egg['display'], is_text=True)

        try:
            easter_egg['action']()
            self.cooldown_manager.activate_easter_egg(easter_egg_id, easter_egg['cooldown'], easter_egg.get('duration'), easter_egg.get('cleanup'))
            time.sleep(0.5)
            self._update_display(self.current_channel)
            return True
        except Exception as e:
            print(f"⚠️ Immediate Easter egg failed: {e}")
            return False

    # Convenience methods for Easter egg management
    def add_custom_easter_egg(self, sequence, message, display, action_func):
        """Add a custom Easter egg at runtime"""
        self.easter_registry.add_easter_egg(sequence, message, display, action_func)
    
    def list_easter_eggs(self):
        """List all available Easter eggs"""
        return self.easter_registry.list_easter_eggs()

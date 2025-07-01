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

class EasterEggActions:
    """Namespace for Easter egg actions with proper error handling"""
    
    def __init__(self, dialer):
        self.dialer = dialer
    
    def emergency_mode(self):
        """911 - Emergency broadcast mode"""
        try:
            self.dialer.display.send_display_command("LED:red-blue 10")
            send_key_to_mpv('c')
            print("🚨 Emergency mode activated - sent 'c' key to MPV")
        except Exception as e:
            print(f"⚠️ Emergency mode failed: {e}")
    
    def demon_mode(self):
        """666 - Demon mode (visual effect only)"""
        print("😈 Demon mode activated")
        # Could add screen effects, color changes, etc.
    
    def party_time(self):
        """420 - Party mode"""
        print("🎉 Party mode activated")
        # Could add fun visual effects, music, etc.
    
    def lucky_mode(self):
        """777 - Lucky mode"""
        print("🍀 Lucky mode activated")
        # Could add special channel selection logic
    
    def test_mode(self):
        """1234 - Test mode for diagnostics"""
        print("🧪 Test mode activated")
        # Could run diagnostics, show system info, etc.
    
    def full_reset(self):
        """0000 - Complete system reset"""
        try:
            # Reset channel to first valid
            self.dialer._reset_to_first_channel()
            print("🔄 Channel reset to first valid")
            
            # Clear MPV effects
            send_key_to_mpv('h')
            print("🔄 MPV effects cleared")
            
            # Could add more reset operations here:
            # - Clear any cached data
            # - Reset display brightness
            # - Clear any temporary settings
            # - Reset audio levels
            # etc.
            
        except Exception as e:
            print(f"⚠️ Reset operation failed: {e}")
    
    def show_404_error(self):
        """404 - Show error page"""
        try:
            self.dialer._show_error("404")
            print("💥 404 error displayed")
        except Exception as e:
            print(f"⚠️ 404 error display failed: {e}")
    
    def fun_mode(self):
        """80085 - Fun mode"""
        print("😄 Fun mode activated")
        # Could add playful effects, sounds, etc.

class EasterEggRegistry:
    """Registry for managing Easter egg configurations"""
    
    def __init__(self, actions):
        self.actions = actions
        self._registry = {
            "911": {
                "message": "🚨 EMERGENCY!",
                "display": "911!",
                "action": self.actions.emergency_mode
            },
            "666": {
                "message": "😈 DEMON MODE!",
                "display": "666",
                "action": self.actions.demon_mode
            },
            "420": {
                "message": "🎉 PARTY TIME!",
                "display": "420",
                "action": self.actions.party_time
            },
            "777": {
                "message": "🍀 LUCKY!",
                "display": "777",
                "action": self.actions.lucky_mode
            },
            "1234": {
                "message": "🧪 TEST MODE!",
                "display": "TEST",
                "action": self.actions.test_mode
            },
            "0000": {
                "message": "🔄 RESET!",
                "display": "RST",
                "action": self.actions.full_reset
            },
            "404": {
                "message": "💥 ERROR!",
                "display": "404",
                "action": self.actions.show_404_error
            },
            "80085": {
                "message": "😄 FUN TIME!",
                "display": "BOOB",
                "action": self.actions.fun_mode
            }
        }
    
    def get_easter_egg(self, sequence):
        """Get Easter egg configuration for sequence"""
        return self._registry.get(sequence)
    
    def is_easter_egg(self, sequence):
        """Check if sequence is an Easter egg"""
        return sequence in self._registry
    
    def add_easter_egg(self, sequence, message, display, action):
        """Add new Easter egg (for dynamic registration)"""
        self._registry[sequence] = {
            "message": message,
            "display": display,
            "action": action
        }
    
    def list_easter_eggs(self):
        """List all registered Easter eggs"""
        return list(self._registry.keys())

class ChannelDialer:
    def __init__(self, digit_timeout=DIGIT_TIMEOUT, display_controller=None):
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = VALID_CHANNELS[0]  # Start with first valid channel
        
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

    def _execute_easter_egg(self, sequence):
        """Execute Easter egg with proper error handling"""
        if not self.easter_registry.is_easter_egg(sequence):
            return False

        easter_egg = self.easter_registry.get_easter_egg(sequence)
        print(f"🎯 {easter_egg['message']}")
        self._update_display(easter_egg['display'], is_text=True)

        try:
            easter_egg['action']()
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

    # Convenience methods for Easter egg management
    def add_custom_easter_egg(self, sequence, message, display, action_func):
        """Add a custom Easter egg at runtime"""
        self.easter_registry.add_easter_egg(sequence, message, display, action_func)
    
    def list_easter_eggs(self):
        """List all available Easter eggs"""
        return self.easter_registry.list_easter_eggs()

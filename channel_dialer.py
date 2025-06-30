#!/usr/bin/env python3
"""
Channel Dialer - Intelligent digit queue system for channel switching
"""

import time
import threading
import subprocess
from collections import deque


# Valid channels - super simple array for now
VALID_CHANNELS = [1, 2, 3, 8, 9, 13]


def write_json_to_socket(data):
    """Helper function to write JSON data to socket"""
    import json
    SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
    try:
        json_str = json.dumps(data)
        with open(SOCKET_PATH, 'w') as f:
            f.write(json_str)
        print(f"JSON written: {json_str}")
    except Exception as e:
        print(f"Error writing to socket: {e}")


def send_key_to_mpv(key):
    """Helper function to send key to mpv"""
    try:
        window_id = subprocess.check_output(
            ['xdotool', 'search', '--onlyvisible', '--class', 'mpv'],
            env={'DISPLAY': ':0'}
        ).decode().strip().split('\n')[0]
        subprocess.run(['xdotool', 'key', '--window', window_id, key], env={'DISPLAY': ':0'})
    except Exception as e:
        print(f"Failed to send key '{key}' to mpv: {e}")


class ChannelDialer:
    def __init__(self, digit_timeout=1.5, easter_egg_timeout=1.5, display_controller=None):
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.easter_egg_timeout = easter_egg_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = 1  # Track current channel, default to 1
        
        # Easter egg mappings - add more as needed
        self.easter_eggs = {
            "911": self.emergency_mode,
            "666": self.demon_mode,
            "420": self.party_mode,
            "777": self.lucky_mode,
            "1234": self.test_mode,
            "0000": self.reset_mode,
            "404": self.error_mode,
            "80085": self.fun_mode,  # Support for longer sequences
        }
    
    def add_digit(self, digit):
        """Add a digit to the queue and manage timing"""
        try:
            with self.lock:
                self.digit_queue.append(str(digit))
                self.last_digit_time = time.time()
                
                # Show current digit sequence on display
                current_sequence = ''.join(self.digit_queue)
                if self.display:
                    # Use display_number to handle leading zeros properly
                    self.display.display_number(current_sequence)
                
                # Cancel existing timer
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                
                # Check for immediate Easter egg matches (like 911)
                if current_sequence in self.easter_eggs:
                    print(f"🎯 Easter egg triggered: {current_sequence}")
                    try:
                        self.easter_eggs[current_sequence]()
                    except Exception as e:
                        print(f"Easter egg execution error: {e}")
                    # Clear queue but don't return - system is ready for new input
                    self.digit_queue.clear()
                    # Show current channel on display after easter egg
                    if self.display:
                        time.sleep(1)  # Brief pause to show easter egg feedback
                        self.display.display_number(self.current_channel)
                    print("🎮 Ready for new input...")
                    return
                
                # Set new timer for regular channel processing
                self.timer = threading.Timer(self.digit_timeout, self._process_channel)
                self.timer.start()
        except Exception as e:
            print(f"Add digit error: {e}")
            # Try to recover by clearing the queue
            try:
                self.clear_queue()
            except:
                pass
    
    def clear_queue(self):
        """Clear the digit queue"""
        try:
            with self.lock:
                self.digit_queue.clear()
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                # Show current channel when clearing
                if self.display:
                    self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"Clear queue error: {e}")
            # Force clear even if lock fails
            try:
                self.digit_queue.clear()
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
            except:
                pass
    
    def _process_channel(self):
        """Process accumulated digits as channel number"""
        try:
            with self.lock:
                if not self.digit_queue:
                    return
                
                channel_str = ''.join(self.digit_queue)
                
                # Check for Easter eggs one more time
                if channel_str in self.easter_eggs:
                    print(f"🎯 Easter egg triggered: {channel_str}")
                    try:
                        self.easter_eggs[channel_str]()
                    except Exception as e:
                        print(f"Easter egg execution error: {e}")
                    # Show current channel after easter egg
                    if self.display:
                        time.sleep(1)
                        self.display.display_number(self.current_channel)
                else:
                    try:
                        channel_num = int(channel_str)
                        self.tune_to_channel(channel_num)
                    except ValueError:
                        print(f"❌ Invalid channel sequence: {channel_str}")
                        # Show error briefly, then return to current channel
                        if self.display:
                            self.display.display_text("ERR")
                            time.sleep(1)
                            self.display.display_number(self.current_channel)
                
                self.digit_queue.clear()
                self.timer = None
        except Exception as e:
            print(f"Channel processing error: {e}")
            # Ensure we clean up even if there's an error
            try:
                with self.lock:
                    self.digit_queue.clear()
                    self.timer = None
                    # Fallback to showing current channel
                    if self.display:
                        self.display.display_number(self.current_channel)
            except:
                pass
    
    def tune_to_channel(self, channel):
        """Tune to specific channel number with validation"""
        print(f"📺 Attempting to tune to channel {channel}")
        
        # Check if channel is valid
        if channel in VALID_CHANNELS:
            print(f"✅ Valid channel: {channel}")
            self.current_channel = channel
            if self.display:
                self.display.display_number(channel)
            write_json_to_socket({
                "command": "direct", 
                "channel": channel,
                "valid": True,
                "timestamp": time.time()
            })
        else:
            print(f"❌ Invalid channel: {channel} (valid: {VALID_CHANNELS})")
            # Show invalid channel briefly, then revert to current
            if self.display:
                self.display.display_text("NOPE")
                time.sleep(0.8)
                self.display.display_number(self.current_channel)
            # Still send the command but mark as invalid - let TV decide
            write_json_to_socket({
                "command": "direct", 
                "channel": channel,
                "valid": False,
                "fallback_channel": self.current_channel,
                "timestamp": time.time()
            })

    def channel_up(self):
        """Handle channel up with validation"""
        # Show switching indicator
        if self.display:
            self.display.display_text("UP")
            time.sleep(0.4)  # Brief switching animation

        # Find next valid channel
        current_idx = VALID_CHANNELS.index(self.current_channel) if self.current_channel in VALID_CHANNELS else 0
        next_idx = (current_idx + 1) % len(VALID_CHANNELS)
        next_channel = VALID_CHANNELS[next_idx]

        print(f"📺 Channel UP: {self.current_channel} -> {next_channel}")
        self.current_channel = next_channel
        if self.display:
            self.display.display_number(self.current_channel)

        write_json_to_socket({
            "command": "up", 
            "channel": self.current_channel,
            "timestamp": time.time()
        })  

    def channel_down(self):
        """Handle channel down with validation"""
        # Show switching indicator
        if self.display:
            self.display.display_text("Dn")
            time.sleep(0.4)  # Brief switching animation

        # Find previous valid channel
        current_idx = VALID_CHANNELS.index(self.current_channel) if self.current_channel in VALID_CHANNELS else 0
        prev_idx = (current_idx - 1) % len(VALID_CHANNELS)
        prev_channel = VALID_CHANNELS[prev_idx]

        print(f"📺 Channel DOWN: {self.current_channel} -> {prev_channel}")
        self.current_channel = prev_channel
        if self.display:
            self.display.display_number(self.current_channel)

        write_json_to_socket({
            "command": "down", 
            "channel": self.current_channel,
            "timestamp": time.time()
        })

    # Easter egg functions - all with exception handling
    def emergency_mode(self):
        try:
            print("🚨 EMERGENCY MODE ACTIVATED! 🚨")
            if self.display:
                self.display.display_text("911!")
            # Safely try to send key to mpv
            try:
                send_key_to_mpv('c')  # Could trigger special emergency feed
            except Exception as e:
                print(f"Easter egg mpv command failed: {e}")
        except Exception as e:
            print(f"Emergency mode error: {e}")
    
    def demon_mode(self):
        try:
            print("😈 DEMON MODE ACTIVATED! 😈")
            if self.display:
                self.display.display_text("666")
        except Exception as e:
            print(f"Demon mode error: {e}")
    
    def party_mode(self):
        try:
            print("🎉 PARTY MODE ACTIVATED! 🎉")
            if self.display:
                self.display.display_text("420")
        except Exception as e:
            print(f"Party mode error: {e}")
    
    def lucky_mode(self):
        try:
            print("🍀 LUCKY MODE ACTIVATED! 🍀")
            if self.display:
                self.display.display_text("777")
        except Exception as e:
            print(f"Lucky mode error: {e}")
    
    def test_mode(self):
        try:
            print("🧪 TEST MODE ACTIVATED! 🧪")
            if self.display:
                self.display.display_text("TEST")
        except Exception as e:
            print(f"Test mode error: {e}")
    
    def reset_mode(self):
        try:
            print("🔄 RESET MODE ACTIVATED! 🔄")
            if self.display:
                self.display.display_text("RST")
                time.sleep(1)
            # Reset to first valid channel
            self.current_channel = VALID_CHANNELS[0]
            if self.display:
                self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"Reset mode error: {e}")
    
    def error_mode(self):
        try:
            print("💥 ERROR MODE ACTIVATED! 💥")
            if self.display:
                self.display.display_text("404")
        except Exception as e:
            print(f"Error mode error: {e}")
    
    def fun_mode(self):
        try:
            print("😄 FUN MODE ACTIVATED! 😄")
            if self.display:
                self.display.display_text("BOOB")  # 80085 -> BOOB on 7-segment
        except Exception as e:
            print(f"Fun mode error: {e}")

"""
Channel dialing system with digit queue management and validation.
"""

import time
import threading
from collections import deque
from typing import Optional, List, Dict, Callable

from config.settings import VALID_CHANNELS
from core.socket_writer import write_channel_command
from features.easter_eggs import EasterEggHandler


class ChannelDialer:
    """
    Manages channel dialing with digit queue system and Easter egg support.
    """
    
    def __init__(self, digit_timeout: float = 1.5, display_controller=None):
        """
        Initialize the channel dialer.
        
        Args:
            digit_timeout: Timeout for digit sequence processing
            display_controller: Optional display controller for visual feedback
        """
        self.digit_queue = deque()
        self.digit_timeout = digit_timeout
        self.last_digit_time = 0
        self.timer = None
        self.lock = threading.Lock()
        self.display = display_controller
        self.current_channel = VALID_CHANNELS[0] if VALID_CHANNELS else 1
        
        # Initialize easter egg handler
        self.easter_egg_handler = EasterEggHandler(display_controller)
        
    def add_digit(self, digit: int) -> None:
        """
        Add a digit to the queue and manage timing.
        
        Args:
            digit: Digit to add (0-9)
        """
        try:
            with self.lock:
                self.digit_queue.append(str(digit))
                self.last_digit_time = time.time()
                
                # Show current digit sequence on display
                current_sequence = ''.join(self.digit_queue)
                if self.display:
                    self.display.display_number(current_sequence)
                
                # Cancel existing timer
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                
                # Check for immediate Easter egg matches
                if self.easter_egg_handler.check_and_execute(current_sequence):
                    # Clear queue and return to current channel display
                    self.digit_queue.clear()
                    if self.display:
                        time.sleep(1)  # Brief pause to show easter egg feedback
                        self.display.display_number(self.current_channel)
                    print("🎮 Ready for new input...")
                    return
                
                # Set new timer for regular channel processing
                self.timer = threading.Timer(self.digit_timeout, self._process_channel)
                self.timer.start()
                
        except Exception as e:
            print(f"❌ Add digit error: {e}")
            self._safe_clear_queue()
    
    def clear_queue(self) -> None:
        """Clear the digit queue and return to current channel display."""
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
            print(f"❌ Clear queue error: {e}")
            self._safe_clear_queue()
    
    def _safe_clear_queue(self) -> None:
        """Force clear the queue even if lock fails."""
        try:
            self.digit_queue.clear()
            if self.timer:
                self.timer.cancel()
                self.timer = None
            if self.display:
                self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"❌ Safe clear queue error: {e}")
    
    def _process_channel(self) -> None:
        """Process accumulated digits as channel number."""
        try:
            with self.lock:
                if not self.digit_queue:
                    return
                
                channel_str = ''.join(self.digit_queue)
                
                # Check for Easter eggs one more time
                if self.easter_egg_handler.check_and_execute(channel_str):
                    if self.display:
                        time.sleep(1)
                        self.display.display_number(self.current_channel)
                else:
                    # Process as channel number
                    try:
                        channel_num = int(channel_str)
                        self.tune_to_channel(channel_num)
                    except ValueError:
                        print(f"❌ Invalid channel sequence: {channel_str}")
                        self._show_error_and_return_to_channel()
                
                self.digit_queue.clear()
                self.timer = None
                
        except Exception as e:
            print(f"❌ Channel processing error: {e}")
            self._safe_cleanup()
    
    def _show_error_and_return_to_channel(self) -> None:
        """Show error on display and return to current channel."""
        if self.display:
            self.display.display_text("ERR")
            time.sleep(1)
            self.display.display_number(self.current_channel)
    
    def _safe_cleanup(self) -> None:
        """Safely clean up after errors."""
        try:
            with self.lock:
                self.digit_queue.clear()
                self.timer = None
                if self.display:
                    self.display.display_number(self.current_channel)
        except Exception as e:
            print(f"❌ Safe cleanup error: {e}")
    
    def tune_to_channel(self, channel: int) -> None:
        """
        Tune to specific channel number with validation.
        
        Args:
            channel: Channel number to tune to
        """
        print(f"📺 Attempting to tune to channel {channel}")
        
        # Check if channel is valid
        if channel in VALID_CHANNELS:
            print(f"✅ Valid channel: {channel}")
            self.current_channel = channel
            if self.display:
                self.display.display_number(channel)
            write_channel_command("direct", channel=channel, valid=True)
        else:
            print(f"❌ Invalid channel: {channel} (valid: {VALID_CHANNELS})")
            # Show invalid channel briefly, then revert to current
            if self.display:
                self.display.display_text("NOPE")
                time.sleep(0.8)
                self.display.display_number(self.current_channel)
            # Still send the command but mark as invalid
            write_channel_command(
                "direct", 
                channel=channel, 
                valid=False, 
                fallback_channel=self.current_channel
            )
    
    def channel_up(self) -> None:
        """Handle channel up with validation."""
        # Show switching indicator
        if self.display:
            self.display.display_text("UP")
            time.sleep(0.4)
        
        # Find next valid channel
        try:
            current_idx = VALID_CHANNELS.index(self.current_channel)
        except ValueError:
            current_idx = 0
        
        next_idx = (current_idx + 1) % len(VALID_CHANNELS)
        next_channel = VALID_CHANNELS[next_idx]
        
        print(f"📺 Channel UP: {self.current_channel} -> {next_channel}")
        self.current_channel = next_channel
        
        if self.display:
            self.display.display_number(self.current_channel)
        
        write_channel_command("up", channel=self.current_channel)
    
    def channel_down(self) -> None:
        """Handle channel down with validation."""
        # Show switching indicator
        if self.display:
            self.display.display_text("Dn")
            time.sleep(0.4)
        
        # Find previous valid channel
        try:
            current_idx = VALID_CHANNELS.index(self.current_channel)
        except ValueError:
            current_idx = 0
        
        prev_idx = (current_idx - 1) % len(VALID_CHANNELS)
        prev_channel = VALID_CHANNELS[prev_idx]
        
        print(f"📺 Channel DOWN: {self.current_channel} -> {prev_channel}")
        self.current_channel = prev_channel
        
        if self.display:
            self.display.display_number(self.current_channel)
        
        write_channel_command("down", channel=self.current_channel)
    
    def get_current_channel(self) -> int:
        """Get the current channel number."""
        return self.current_channel
    
    def set_current_channel(self, channel: int) -> None:
        """
        Set the current channel (for initialization).
        
        Args:
            channel: Channel number to set as current
        """
        if channel in VALID_CHANNELS:
            self.current_channel = channel
            if self.display:
                self.display.display_number(self.current_channel)
    
    def cleanup(self) -> None:
        """Clean up resources and cancel any pending timers."""
        try:
            with self.lock:
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                self.digit_queue.clear()
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

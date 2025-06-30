#!/usr/bin/env python3
"""
MPV player control utilities for IR Remote Mapper
"""

import subprocess
from typing import Optional
from config.settings import MPV_WINDOW_CLASS, X_DISPLAY


def send_key_to_mpv(key: str, window_class: str = MPV_WINDOW_CLASS, display: str = X_DISPLAY) -> bool:
    """
    Send a key press to the MPV player window
    
    Args:
        key: Key to send (e.g., 'space', 'c', 'm', '0', '9')
        window_class: Window class to search for (default: 'mpv')
        display: X display to use (default: ':0')
        
    Returns:
        bool: True if key was sent successfully, False otherwise
    """
    try:
        # Find the MPV window
        window_id = subprocess.check_output(
            ['xdotool', 'search', '--onlyvisible', '--class', window_class],
            env={'DISPLAY': display}
        ).decode().strip().split('\n')[0]
        
        # Send the key to the window
        subprocess.run(
            ['xdotool', 'key', '--window', window_id, key], 
            env={'DISPLAY': display},
            check=True
        )
        
        print(f"🎬 Sent key '{key}' to MPV window {window_id}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to send key '{key}' to MPV: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending key '{key}' to MPV: {e}")
        return False


def find_mpv_windows(window_class: str = MPV_WINDOW_CLASS, display: str = X_DISPLAY) -> list:
    """
    Find all visible MPV windows
    
    Args:
        window_class: Window class to search for
        display: X display to use
        
    Returns:
        list: List of window IDs
    """
    try:
        output = subprocess.check_output(
            ['xdotool', 'search', '--onlyvisible', '--class', window_class],
            env={'DISPLAY': display}
        ).decode().strip()
        
        if output:
            return output.split('\n')
        else:
            return []
            
    except subprocess.CalledProcessError:
        return []
    except Exception as e:
        print(f"❌ Error finding MPV windows: {e}")
        return []


def is_mpv_running(window_class: str = MPV_WINDOW_CLASS, display: str = X_DISPLAY) -> bool:
    """
    Check if MPV is currently running and visible
    
    Args:
        window_class: Window class to search for
        display: X display to use
        
    Returns:
        bool: True if MPV is running and visible, False otherwise
    """
    windows = find_mpv_windows(window_class, display)
    return len(windows) > 0


class MPVController:
    """High-level MPV control interface"""
    
    def __init__(self, window_class: str = MPV_WINDOW_CLASS, display: str = X_DISPLAY):
        """
        Initialize MPV controller
        
        Args:
            window_class: Window class to search for
            display: X display to use
        """
        self.window_class = window_class
        self.display = display
    
    def send_key(self, key: str) -> bool:
        """Send key to MPV player"""
        return send_key_to_mpv(key, self.window_class, self.display)
    
    def is_running(self) -> bool:
        """Check if MPV is running"""
        return is_mpv_running(self.window_class, self.display)
    
    def get_windows(self) -> list:
        """Get list of MPV window IDs"""
        return find_mpv_windows(self.window_class, self.display)
    
    # Convenience methods for common controls
    def play_pause(self) -> bool:
        """Toggle play/pause"""
        return self.send_key('space')
    
    def volume_up(self) -> bool:
        """Increase volume"""
        return self.send_key('0')
    
    def volume_down(self) -> bool:
        """Decrease volume"""
        return self.send_key('9')
    
    def mute(self) -> bool:
        """Toggle mute"""
        return self.send_key('m')
    
    def next_effect(self) -> bool:
        """Next video effect"""
        return self.send_key('c')
    
    def prev_effect(self) -> bool:
        """Previous video effect"""
        return self.send_key('z')
    
    def digital_analog_toggle(self) -> bool:
        """Toggle digital/analog effect"""
        return self.send_key('b')
    
    def confirm(self) -> bool:
        """Send Return/Enter key"""
        return self.send_key('Return')

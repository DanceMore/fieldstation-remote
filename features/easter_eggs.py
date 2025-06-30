#!/usr/bin/env python3
"""
Easter egg implementations for IR Remote Mapper
"""

import time
from typing import Optional, Callable
from devices.mpv_controller import send_key_to_mpv


class EasterEggs:
    """Container for all easter egg implementations"""
    
    def __init__(self, display_controller=None, current_channel_callback: Optional[Callable] = None):
        """
        Initialize easter eggs
        
        Args:
            display_controller: DisplayController instance for visual feedback
            current_channel_callback: Function that returns current channel number
        """
        self.display = display_controller
        self.get_current_channel = current_channel_callback or (lambda: 1)
        
        # Easter egg mappings - add more as needed
        self.mappings = {
            "911": self.emergency_mode,
            "666": self.demon_mode,
            "420": self.party_mode,
            "777": self.lucky_mode,
            "123": self.test_mode,
            "000": self.reset_mode,
            "404": self.error_mode,
            "80085": self.fun_mode,  # Support for longer sequences
        }
    
    def get_easter_egg(self, sequence: str) -> Optional[Callable]:
        """
        Get easter egg function for given sequence
        
        Args:
            sequence: Digit sequence string
            
        Returns:
            Easter egg function or None if not found
        """
        return self.mappings.get(sequence)
    
    def emergency_mode(self):
        """Emergency mode easter egg (911)"""
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
        """Demon mode easter egg (666)"""
        try:
            print("😈 DEMON MODE ACTIVATED! 😈")
            if self.display:
                self.display.display_text("666")
        except Exception as e:
            print(f"Demon mode error: {e}")
    
    def party_mode(self):
        """Party mode easter egg (420)"""
        try:
            print("🎉 PARTY MODE ACTIVATED! 🎉")
            if self.display:
                self.display.display_text("420")
        except Exception as e:
            print(f"Party mode error: {e}")
    
    def lucky_mode(self):
        """Lucky mode easter egg (777)"""
        try:
            print("🍀 LUCKY MODE ACTIVATED! 🍀")
            if self.display:
                self.display.display_text("777")
        except Exception as e:
            print(f"Lucky mode error: {e}")
    
    def test_mode(self):
        """Test mode easter egg (123)"""
        try:
            print("🧪 TEST MODE ACTIVATED! 🧪")
            if self.display:
                self.display.display_text("TEST")
        except Exception as e:
            print(f"Test mode error: {e}")
    
    def reset_mode(self):
        """Reset mode easter egg (000)"""
        try:
            print("🔄 RESET MODE ACTIVATED! 🔄")
            if self.display:
                self.display.display_text("RST")
                time.sleep(1)
            
            # This would need to be handled by the channel dialer
            # For now, just show feedback
            current = self.get_current_channel()
            if self.display:
                self.display.display_number(current)
                
        except Exception as e:
            print(f"Reset mode error: {e}")
    
    def error_mode(self):
        """Error mode easter egg (404)"""
        try:
            print("💥 ERROR MODE ACTIVATED! 💥")
            if self.display:
                self.display.display_text("404")
        except Exception as e:
            print(f"Error mode error: {e}")
    
    def fun_mode(self):
        """Fun mode easter egg (80085)"""
        try:
            print("😄 FUN MODE ACTIVATED! 😄")
            if self.display:
                self.display.display_text("BOOB")  # 80085 -> BOOB on 7-segment
        except Exception as e:
            print(f"Fun mode error: {e}")
    
    def add_easter_egg(self, sequence: str, callback: Callable):
        """
        Add a new easter egg
        
        Args:
            sequence: Digit sequence to trigger
            callback: Function to call when triggered
        """
        self.mappings[sequence] = callback
    
    def remove_easter_egg(self, sequence: str):
        """
        Remove an easter egg
        
        Args:
            sequence: Digit sequence to remove
        """
        if sequence in self.mappings:
            del self.mappings[sequence]
    
    def list_easter_eggs(self) -> list:
        """
        Get list of all easter egg sequences
        
        Returns:
            List of easter egg sequences
        """
        return list(self.mappings.keys())

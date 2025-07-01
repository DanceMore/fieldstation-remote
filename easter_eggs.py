import time
import threading
from collections import defaultdict

# Import shared utilities
from utils import safe_execute, send_key_to_mpv

class EasterEggCooldownManager:
    """Manages cooldowns, expirations, and automatic cleanup for Easter eggs"""
    
    def __init__(self):
        # Track when each Easter egg was last activated
        self.last_activation = {}
        
        # Track active effects and their expiration times
        self.active_effects = {}
        
        # Track cleanup timers for automatic expiration
        self.cleanup_timers = {}
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def can_activate(self, easter_egg_id, cooldown_duration):
        """Check if Easter egg can be activated (not in cooldown)"""
        with self.lock:
            last_time = self.last_activation.get(easter_egg_id, 0)
            time_since_last = time.time() - last_time
            return time_since_last >= cooldown_duration
    
    def activate_easter_egg(self, easter_egg_id, cooldown_duration, effect_duration=None, cleanup_callback=None):
        """Activate Easter egg and set up expiration if needed"""
        with self.lock:
            now = time.time()
            self.last_activation[easter_egg_id] = now
            
            # If this has an expiring effect, set up automatic cleanup
            if effect_duration and cleanup_callback:
                # Cancel any existing cleanup timer for this effect
                if easter_egg_id in self.cleanup_timers:
                    self.cleanup_timers[easter_egg_id].cancel()
                
                # Set expiration time
                self.active_effects[easter_egg_id] = now + effect_duration
                
                # Set up cleanup timer
                cleanup_timer = threading.Timer(effect_duration, self._cleanup_effect, 
                                               args=[easter_egg_id, cleanup_callback])
                cleanup_timer.start()
                self.cleanup_timers[easter_egg_id] = cleanup_timer
                
                print(f"⏰ Effect '{easter_egg_id}' will expire in {effect_duration/60:.1f} minutes")
    
    def _cleanup_effect(self, easter_egg_id, cleanup_callback):
        """Internal method to clean up expired effects"""
        with self.lock:
            if easter_egg_id in self.active_effects:
                del self.active_effects[easter_egg_id]
            if easter_egg_id in self.cleanup_timers:
                del self.cleanup_timers[easter_egg_id]
        
        print(f"⏰ Effect '{easter_egg_id}' has expired - cleaning up")
        try:
            cleanup_callback()
        except Exception as e:
            print(f"⚠️ Cleanup failed for {easter_egg_id}: {e}")
    
    def is_effect_active(self, easter_egg_id):
        """Check if an effect is currently active"""
        with self.lock:
            return easter_egg_id in self.active_effects
    
    def get_time_until_available(self, easter_egg_id, cooldown_duration):
        """Get time in seconds until Easter egg is available again"""
        with self.lock:
            last_time = self.last_activation.get(easter_egg_id, 0)
            time_since_last = time.time() - last_time
            remaining = cooldown_duration - time_since_last
            return max(0, remaining)
    
    def get_effect_time_remaining(self, easter_egg_id):
        """Get time in seconds until effect expires"""
        with self.lock:
            if easter_egg_id not in self.active_effects:
                return 0
            remaining = self.active_effects[easter_egg_id] - time.time()
            return max(0, remaining)
    
    def force_cleanup(self, easter_egg_id):
        """Manually clean up an effect"""
        with self.lock:
            if easter_egg_id in self.cleanup_timers:
                self.cleanup_timers[easter_egg_id].cancel()
                del self.cleanup_timers[easter_egg_id]
            if easter_egg_id in self.active_effects:
                del self.active_effects[easter_egg_id]
    
    def cleanup_all(self):
        """Clean up all active effects and timers"""
        with self.lock:
            for timer in self.cleanup_timers.values():
                timer.cancel()
            self.cleanup_timers.clear()
            self.active_effects.clear()

class EasterEggActions:
    """Enhanced Easter egg actions with expiration support"""
    
    def __init__(self, dialer):
        self.dialer = dialer
        self.cooldown_manager = dialer.cooldown_manager
    
    def emergency_mode(self):
        """911 - Emergency broadcast mode with 30 min duration"""
        try:
            self.dialer.display.send_display_command("LED:red-blue 10")
            time.sleep(0.5)
            self.dialer.display.send_display_command("DISP:COPS")
            print("🚨 Emergency mode activated - sent 'c' key to MPV")
            print("🚨 Emergency LED effects active for 30 minutes")
        except Exception as e:
            print(f"⚠️ Emergency mode failed: {e}")
    
    def _cleanup_emergency_mode(self):
        """Cleanup for emergency mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            send_key_to_mpv('h')  # Clear MPV effects
            print("🚨 Emergency mode effects cleared")
        except Exception as e:
            print(f"⚠️ Emergency cleanup failed: {e}")
    
    def demon_mode(self):
        """666 - Demon mode with visual effects for 15 minutes"""
        print("😈 Demon mode activated")
        try:
            self.dialer.display.send_display_command("LED:red-pulse 5")
            print("😈 Demon effects active for 15 minutes")
        except Exception as e:
            print(f"⚠️ Demon mode failed: {e}")
    
    def _cleanup_demon_mode(self):
        """Cleanup for demon mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            print("😈 Demon mode effects cleared")
        except Exception as e:
            print(f"⚠️ Demon cleanup failed: {e}")
    
    def party_time(self):
        """420 - Party mode with effects for 20 minutes"""
        print("🎉 Party mode activated")
        try:
            self.dialer.display.send_display_command("LED:rainbow 30")
            time.sleep(1)
            self.dialer.display.send_display_command("DISP:RAST")
            time.sleep(1)
            self.dialer.display.send_display_command("DISP:FARI")
            time.sleep(1)
            print("🎉 Party effects active for 20 minutes")
        except Exception as e:
            print(f"⚠️ Party mode failed: {e}")
    
    def _cleanup_party_time(self):
        """Cleanup for party mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            print("🎉 Party mode effects cleared")
        except Exception as e:
            print(f"⚠️ Party cleanup failed: {e}")
    
    def lucky_mode(self):
        """777 - Lucky mode (instant effect, no duration)"""
        print("🍀 Lucky mode activated")
        # This is an instant effect, no cleanup needed
    
    def test_mode(self):
        """1234 - Test mode (instant effect)"""
        print("🧪 Test mode activated")
        # Run diagnostics, instant effect
    
    def full_reset(self):
        """0000 - Complete system reset (instant effect + cleanup all)"""
        try:
            # Force cleanup of ALL active effects
            self.cooldown_manager.cleanup_all()
            
            # Clear LED effects
            self.dialer.display.send_display_command("LED:off")
            
            # Reset channel to first valid
            self.dialer._reset_to_first_channel()
            print("🔄 Channel reset to first valid")
            
            # Clear MPV effects
            send_key_to_mpv('h')
            print("🔄 All effects cleared and system reset")
            
        except Exception as e:
            print(f"⚠️ Reset operation failed: {e}")
    
    def show_404_error(self):
        """404 - Show error page (instant effect)"""
        try:
            self.dialer._show_error("404")
            print("💥 404 error displayed")
        except Exception as e:
            print(f"⚠️ 404 error display failed: {e}")
    
    def fun_mode(self):
        """80085 - Fun mode with effects for 10 minutes"""
        print("😄 Fun mode activated")
        try:
            self.dialer.display.send_display_command("LED:bounce-green 2")
            print("😄 Fun effects active for 10 minutes")
        except Exception as e:
            print(f"⚠️ Fun mode failed: {e}")
    
    def _cleanup_fun_mode(self):
        """Cleanup for fun mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            print("😄 Fun mode effects cleared")
        except Exception as e:
            print(f"⚠️ Fun cleanup failed: {e}")

    def digital_analog_effect(self):
        """DIGITAL_ANALOG - Digital/Analog visual effect (instant)"""
        print("✨ Digital/Analog effect activated")
        try:
            send_key_to_mpv('b')
        except Exception as e:
            print(f"⚠️ Digital/Analog effect failed: {e}")

class EasterEggRegistry:
    """Enhanced registry with cooldown and expiration support"""
    
    def __init__(self, actions):
        self.actions = actions
        self._registry = {
            "911": {
                "message": "🚨 EMERGENCY!",
                "display": "SHIT",
                "action": self.actions.emergency_mode,
                "cleanup": self.actions._cleanup_emergency_mode,
                "cooldown": 3600,  # 1 hour cooldown
                "duration": 1800,  # 30 minutes active
                "description": "Emergency mode (30m active, 1h cooldown)"
            },
            "666": {
                "message": "😈 DEMON MODE!",
                "display": "666",
                "action": self.actions.demon_mode,
                "cleanup": self.actions._cleanup_demon_mode,
                "cooldown": 1800,  # 30 min cooldown
                "duration": 900,   # 15 minutes active
                "description": "Demon mode (15m active, 30m cooldown)"
            },
            "420": {
                "message": "🎉 PARTY TIME!",
                "display": "YAH",
                "action": self.actions.party_time,
                "cleanup": self.actions._cleanup_party_time,
                "cooldown": 2400,  # 40 min cooldown
                "duration": 1200,  # 20 minutes active
                "description": "Party mode (20m active, 40m cooldown)"
            },
            "777": {
                "message": "🍀 LUCKY!",
                "display": "777",
                "action": self.actions.lucky_mode,
                "cooldown": 300,   # 5 min cooldown for instant effects
                "description": "Lucky mode (instant, 5m cooldown)"
            },
            "1234": {
                "message": "🧪 TEST MODE!",
                "display": "TEST",
                "action": self.actions.test_mode,
                "cooldown": 60,    # 1 min cooldown
                "description": "Test mode (instant, 1m cooldown)"
            },
            "0000": {
                "message": "🔄 RESET!",
                "display": "RST",
                "action": self.actions.full_reset,
                "cooldown": 30,    # 30 sec cooldown
                "description": "Full reset (instant, 30s cooldown)"
            },
            "404": {
                "message": "💥 ERROR!",
                "display": "404",
                "action": self.actions.show_404_error,
                "cooldown": 60,    # 1 min cooldown
                "description": "404 error (instant, 1m cooldown)"
            },
            "80085": {
                "message": "😄 FUN TIME!",
                "display": "BOOB",
                "action": self.actions.fun_mode,
                "cleanup": self.actions._cleanup_fun_mode,
                "cooldown": 900,   # 15 min cooldown
                "duration": 600,   # 10 minutes active
                "description": "Fun mode (10m active, 15m cooldown)"
            },
            "DIGITAL_ANALOG": {
                "message": "✨ Digital/Analog effect!",
                "display": "8bit",
                "action": self.actions.digital_analog_effect,
                "cooldown": 3,     # 3 second cooldown
                "description": "Digital/Analog effect (instant, 3s cooldown)"
        }
    }

    def get_easter_egg(self, sequence):
        """Get Easter egg configuration for sequence"""
        return self._registry.get(sequence)

    def is_easter_egg(self, sequence):
        """Check if sequence is an Easter egg"""
        return sequence in self._registry

    def trigger_immediate_easter_egg(self, easter_egg_id):
        """Trigger an Easter egg immediately by ID (for button presses)"""
        if easter_egg_id in self._registry:
            return self._registry[easter_egg_id]

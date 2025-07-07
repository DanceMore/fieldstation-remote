import time
import threading
import random
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
        # Note: cooldown_manager will be accessed via dialer.cooldown_manager

    def emergency_mode(self):
        """911 - Emergency broadcast mode with 30 min duration"""
        try:
            print("🚨 Emergency mode activated")
            self.dialer.display.send_display_command("LED:red-blue 10")
            time.sleep(0.5)
            self.dialer.display.send_display_command("DISP:COPS")
            print("🚨 Emergency LED effects active for 30 minutes")
        except Exception as e:
            print(f"⚠️ Emergency mode failed: {e}")

    def _cleanup_emergency_mode(self):
        """Cleanup for emergency mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            print("🚨 Emergency mode effects cleared")
        except Exception as e:
            print(f"⚠️ Emergency cleanup failed: {e}")

    def demon_mode(self):
        """666 - Demon mode with visual effects for 15 minutes"""
        print("😈 Demon mode activated")
        try:
            send_key_to_mpv('m')
            self.dialer.display.send_display_command("LED:pulse-red 20")
            print("😈 Demon effects active for 15 minutes")
        except Exception as e:
            print(f"⚠️ Demon mode failed: {e}")

    def _cleanup_demon_mode(self):
        """Cleanup for demon mode"""
        try:
            self.dialer.display.send_display_command("LED:off")
            send_key_to_mpv('h')  # Clear MPV effects
            print("😈 Demon mode effects cleared")
        except Exception as e:
            print(f"⚠️ Demon cleanup failed: {e}")

    def party_time(self):
        """420 - Party mode with effects for 20 minutes"""
        print("🎉 Party mode activated")
        try:
            send_key_to_mpv('b')
            self.dialer.display.send_display_command("LED:rainbow 60")
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
            send_key_to_mpv('h')  # Clear MPV effects
            print("🎉 Party mode effects cleared")
        except Exception as e:
            print(f"⚠️ Party cleanup failed: {e}")

    def full_reset(self):
        """0000 - Complete system reset (instant effect + cleanup all)"""
        try:
            # Force cleanup of ALL active effects
            self.dialer.cooldown_manager.cleanup_all()

            # Clear LED effects
            self.dialer.display.send_display_command("LED:off")
            print("🔄 LED reset to off")

            # Reset channel to first valid
            self.dialer.tune_to_channel(1)
            print("🔄 Channel reset to first valid")

            # Clear MPV effects
            send_key_to_mpv('h')
            print("🔄 All effects cleared and system reset")

        except Exception as e:
            print(f"⚠️ Reset operation failed: {e}")

    def show_404_error(self):
        """404 - Show error page (instant effect)"""
        try:
            self.dialer.display.send_display_command("LED:nack")
            self.dialer.display.send_display_command("DISP:404")
            time.sleep(1.1)
            self.dialer.display.send_display_command("LED:nack")
            self.dialer.display.send_display_command("DISP:huh")
            time.sleep(1.4)
            self.dialer.display.send_display_command("LED:nack")
            self.dialer.display.send_display_command("DISP:.404")
            time.sleep(1)
            self.dialer.display.send_display_command("LED:ack")
            self.dialer.display.send_display_command("DISP:.huh")
            time.sleep(1.4)
            self.dialer.display.send_display_command("LED:nack")
            self.dialer.display.send_display_command("DISP:.404")
            time.sleep(1.4)
            self.dialer.display.send_display_command("LED:nack")
            self.dialer.display.send_display_command("DISP:8888")
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("LED:nack")
            time.sleep(0.3)
            self.dialer.display.send_display_command("DISP:DUNO")
            time.sleep(1.3)
            print("💥 404 error displayed")
        except Exception as e:
            print(f"⚠️ 404 error display failed: {e}")

    def digital_analog_effect(self):
        """DIGITAL_ANALOG - Digital/Analog visual effect (instant)"""
        print("✨ Digital/Analog effect activated")
        try:
            self.dialer.display.send_display_command("LED:matrix 20")
            send_key_to_mpv('d')
        except Exception as e:
            print(f"⚠️ Digital/Analog effect failed: {e}")

    def celestial_mode(self):
        """6969 - Random celestial object selector (instant)"""
        # VNUS
        # MERC
        # MARS
        # AQUA
        celestial_objects = [
            "GAIA", "JPTR", "SATN", "URNS", "NPTN", "PLTO",
            "ARES", "TAUR", "GEMI", "CRAB", "LEOb", "VIRG", "LIBR", "SCRP", "SAGI",
            "CAPR", "PISC"
        ]

        selected_object = random.choice(celestial_objects)
        print(f"🌌 Celestial mode activated - Selected: {selected_object}")

        try:
            # Show selection with cosmic LED effect
            self.dialer.display.send_display_command("LED:pulse-blue 7")
            time.sleep(1.3)
            self.dialer.display.send_display_command(f"DISP:{selected_object}")
            time.sleep(4.7)
            print(f"🌌 Displaying celestial object: {selected_object}")
        except Exception as e:
            print(f"⚠️ Celestial mode failed: {e}")

    def magic_8_ball(self):
        """8888 - Magic 8 Ball with random responses (instant)"""
        responses = [
            "YES", "NO", "MAYB", "L8R", "SURE", "NOPE", "DUNNO", "WAIT",
            "GOOD", "BAD", "PROB", "NEVA", "YOLO", "HMPH", "OBVI", "NADA",
            "DEFS", "RELY", "SKIP", "FINE", "COOL", "NOPE", "YEAH", "PASS"
        ]

        selected_response = random.choice(responses)
        print(f"🎱 Magic 8 Ball activated - Response: {selected_response}")

        try:
            # Show thinking animation
            self.dialer.display.send_display_command("LED:thinking 3")
            self.dialer.display.send_display_command("DISP:8888")
            time.sleep(3)
            # Show the response
            self.dialer.display.send_display_command(f"DISP:{selected_response}")
            print(f"🎱 Magic 8 Ball says: {selected_response}")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Magic 8 Ball failed: {e}")

    def clear_effects(self):
        """CLEAR - Clear effects (instant)"""
        print("✨ Clear effects activated")
        try:
            self.dialer.display.send_display_command("LED:ack")
            send_key_to_mpv('h')
        except Exception as e:
            print(f"⚠️ Clear effects failed: {e}")

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
                "cooldown": 3600, # 1 hour cooldown
                "duration": 10,
                "description": "Emergency mode (10s active, 1h cooldown)"
            },
            "666": {
                "message": "😈 DEMON MODE!",
                "display": "666",
                "action": self.actions.demon_mode,
                "cleanup": self.actions._cleanup_demon_mode,
                "cooldown": 1800, # 30 min cooldown
                "duration": 300,  # 5 minutes active
                "description": "Demon mode (5m active, 30m cooldown)"
            },
            "420": {
                "message": "🎉 PARTY TIME!",
                "display": "YAH",
                "action": self.actions.party_time,
                "cleanup": self.actions._cleanup_party_time,
                "cooldown": 2520,  # 42 min cooldown
                "duration": 1200,  # 20 minutes active
                "description": "Party mode (20m active, 42m cooldown)"
            },
            "1234": {
                "message": "🧪 TEST MODE! (aka reset)",
                "display": " RST",
                "action": self.actions.full_reset,
                "cooldown": 2,
                "description": "Test mode (aka reset) (instant, 2s cooldown)"
            },
            "0000": {
                "message": "🔄 RESET!",
                "display": "RST",
                "action": self.actions.full_reset,
                "cooldown": 2,
                "description": "Full reset (instant, 2s cooldown)"
            },
            "404": {
                "message": "💥 ERROR!",
                "display": "404",
                "action": self.actions.show_404_error,
                "cooldown": 60,    # 1 min cooldown
                "description": "404 error (instant, 1m cooldown)"
            },
            "6969": {
                "message": "🌌 Celestial mode!",
                "display": "STAR",
                "action": self.actions.celestial_mode,
                "cooldown": 20,    # 30 second cooldown
                "description": "Random celestial object (instant, 30s cooldown)"
            },
            "9696": {
                "message": "🌌 Celestial mode!",
                "display": "STAR",
                "action": self.actions.celestial_mode,
                "cooldown": 20,    # 30 second cooldown
                "description": "Random celestial object (instant, 30s cooldown)"
            },
            "8888": {
                "message": "🎱 Magic 8 Ball!",
                "display": "8888",
                "action": self.actions.magic_8_ball,
                "cooldown": 5, # 5 second cooldown
                "description": "Magic 8 Ball (instant, 5s cooldown)"
            },
            "DIGITAL_ANALOG": {
                "message": "✨ Digital/Analog effect!",
                "display": "8bit",
                "action": self.actions.digital_analog_effect,
                "cooldown": 2,     # 2 second cooldown
                "description": "Digital/Analog effect (instant, 2s cooldown)"
            },
            "CLEAR": {
                "message": "✨ Clear effects!",
                "display": "RTN",
                "action": self.actions.clear_effects,
                "cooldown": 2,     # 2 second cooldown
                "description": "Clear effects (instant, 2s cooldown)"
            },
        }

    def get_easter_egg(self, sequence):
        """Get Easter egg configuration for sequence"""
        return self._registry.get(sequence)

    def is_easter_egg(self, sequence):
        """Check if sequence is an Easter egg"""
        return sequence in self._registry

    def trigger_easter_egg(self, dialer, sequence):
        """Trigger an Easter egg with proper cooldown checking"""
        config = self.get_easter_egg(sequence)
        if not config:
            return False

        # Check if on cooldown
        if not dialer.cooldown_manager.can_activate(sequence, config["cooldown"]):
            dialer.display.send_display_command("LED:nack")
            remaining = dialer.cooldown_manager.get_time_until_available(sequence, config["cooldown"])
            minutes = remaining // 60
            seconds = remaining % 60
            if minutes > 0:
                print(f"⏰ {sequence} still on cooldown for {minutes:.0f}m {seconds:.0f}s")
                disp_text = f"{int(minutes):02d}{int(seconds):02d}" # Format as MMSS with zero-padding
            else:
                print(f"⏰ {sequence} still on cooldown for {seconds:.0f}s")
                disp_text = f"00{int(seconds):02d}" # Format as 00SS with zero-padding

            dialer.display.send_display_command(f"DISP:{disp_text}")
            return False

        # Display the message and show on display
        print(config["message"])
        if "display" in config:
            try:
                dialer.display.send_display_command(f"DISP:{config['display']}")
            except Exception as e:
                print(f"⚠️ Display update failed: {e}")

        # Activate the easter egg in the cooldown manager
        dialer.cooldown_manager.activate_easter_egg(
            sequence, 
            config["cooldown"], 
            config.get("duration"), 
            config.get("cleanup")
        )

        # Execute the action
        try:
            config["action"]()
        except Exception as e:
            print(f"⚠️ Easter egg action failed: {e}")
            # If action failed, we should still respect the cooldown

        return True

    def get_status_info(self, dialer):
        """Get status information about all easter eggs"""
        status = {}
        for egg_id, config in self._registry.items():
            remaining_cooldown = dialer.cooldown_manager.get_time_until_available(egg_id, config["cooldown"])
            remaining_effect = dialer.cooldown_manager.get_effect_time_remaining(egg_id)
            is_active = dialer.cooldown_manager.is_effect_active(egg_id)

            status[egg_id] = {
                "description": config["description"],
                "cooldown_remaining": remaining_cooldown,
                "effect_remaining": remaining_effect,
                "is_active": is_active,
                "available": remaining_cooldown == 0
            }
        return status

    def add_easter_egg(self, sequence, message, display, action_func, cooldown=60):
        """Add a custom Easter egg at runtime"""
        self._registry[sequence] = {
            "message": message,
            "display": display,
            "action": action_func,
            "cooldown": cooldown,
            "description": f"Custom Easter egg ({cooldown}s cooldown)"
        }

    def list_easter_eggs(self):
        """List all available Easter eggs"""
        return {seq: config["description"] for seq, config in self._registry.items()}

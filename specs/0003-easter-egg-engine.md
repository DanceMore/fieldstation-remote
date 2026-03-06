# Spec: Easter Egg Engine (0003)

## Reality
Managed by `easter_eggs.py` with three core components:
- **Registry**: Map of sequences (911, 666, etc.) to metadata (cooldown, duration, action).
- **CooldownManager**: Uses `utils.get_now()` to track `last_activation` and `active_effects`.
- **Actions**: High-level effects that trigger display text, LED commands, and MPV/VLC key presses via `utils.send_key_to_mpv`.

## Intent
Reward discovery in the art installation. Cooldowns prevent hardware "meltdown" (excessive serial commands) or software "noise" (overlapping effects). MMSS display feedback explains *why* an egg might be temporarily disabled.

## Learning
Cooldowns are better than "blocking." If we just blocked the input, the user might think the remote is broken. By showing the remaining time (e.g., "5950" for 59m 50s), we turn a restriction into a status update.

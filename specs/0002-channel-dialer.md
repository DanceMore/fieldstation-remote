# Spec: Intelligent Channel Dialer (0002)

## Reality
Logic resides in `channel_dialer.py`.
- **Queuing**: Uses a `collections.deque` to store digits.
- **Timing**: Employs `utils.start_timer` with a 1.5s timeout (`DIGIT_TIMEOUT`). 
- **Validation**: Only tunes if the resulting integer is in `VALID_CHANNELS = [1, 2, 3, 8, 9, 13]`.
- **Threading**: Uses a `threading.Lock` (`_safe_lock`) to coordinate between the main loop adding digits and the timer thread processing them.

## Intent
Provide a "vintage television" user experience. Users should be able to dial "1" then "3" to get to channel 13. The 7-segment display should show the digits as they are being typed to confirm the system is "listening."

## Learning
Timer-based processing is dangerous without locking. If a user types faster than the serial port can update the display, the state can drift. The `_safe_lock` pattern ensures that we never process a partial channel or clear the queue mid-press.

# Feature: Intelligent Channel Dialer (F-002)

## Intent
Traditional TV remotes use digit sequences to dial channels. This feature implements a smart queue that accumulates digits over a specific timeout (e.g., 1.5s) before attempting to tune to a channel.

## Success Criteria
- **Smart Queuing**: Pressing "1" then "3" dials channel 13, not channel 1 and then channel 3.
- **Validation**: Only channels in the `VALID_CHANNELS` list are tuned; others show a "NOPE" error.
- **Timeout Feedback**: The 7-segment display shows the accumulating digits in real-time.

## Intent Vectors
- **Appliance Feel**: Emulate the behavior of vintage television sets.
- **Immediate Feedback**: Users should see exactly what they are typing.

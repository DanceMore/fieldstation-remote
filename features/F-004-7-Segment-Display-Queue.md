# Feature: 7-Segment Display Queue (F-004)

## Intent
Provide real-time status feedback to the user without blocking the main event-handling thread. This feature manages communication with the TM1637 4-digit display via a serial command queue.

## Success Criteria
- **Non-blocking IO**: Display commands are queued and processed by a background thread so the IR receiver never "misses" a button press.
- **Support for Mixed Content**: Handles numbers (channels), text (INIT, BOOT, REDY), and formatted time (MMSS).
- **Graceful Error Handling**: If the display is disconnected, the application continues to function normally.

## Intent Vectors
- **Asynchronous Fluidity**: The application feels fast and responsive.
- **Hardware Abstraction**: The display logic is isolated from the main remote control logic.

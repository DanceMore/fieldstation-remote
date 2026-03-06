# Feature: State Persistence (F-005)

## Intent
Ensure the "Wilderness Appliance" feels like a persistent physical device. If the power is pulled and restored, the system should resume exactly where it left off, specifically remembered the last tuned channel.

## Success Criteria
- **Boot Recovery**: On startup, the system loads the last saved state from `runtime/state.json`.
- **Atomic Updates**: State is saved whenever a major change occurs (e.g., successful channel tune).
- **Graceful Fallback**: If the state file is corrupted or missing, the system defaults to Channel 1 without crashing.
- **Portability**: Uses relative paths to ensure it works in any deployment environment.

## Intent Vectors
- **Appliance Continuity**: The device "remembers" its history.
- **Resilience**: Protect against filesystem corruption during sudden power loss.

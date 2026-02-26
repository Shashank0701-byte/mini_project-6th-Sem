"""
Full-State Sync — Transmits entire device state at fixed intervals.

Highest accuracy but highest energy and bandwidth cost.
"""


class FullStateSync:
    """Sync strategy: send complete device state at every sync interval."""

    def __init__(self, config: dict):
        self.interval_s = config.get("full_state_interval_s", 10)
        self.last_sync_tick = 0

    def should_sync(self, tick: int, device_state: dict, battery_pct: float = 1.0) -> bool:
        """Sync at fixed intervals."""
        return (tick - self.last_sync_tick) >= self.interval_s

    def prepare_payload(self, device_state: dict) -> dict:
        """Send the complete device state."""
        self.last_sync_tick = device_state.get("tick", self.last_sync_tick + self.interval_s)
        return {
            "type": "full_state",
            "data": device_state,
        }

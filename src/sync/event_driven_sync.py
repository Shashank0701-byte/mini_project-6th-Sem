"""
Event-Driven Sync — Only syncs when a significant change is detected.

Lowest energy cost when the system is stable, but may miss gradual drift.
"""


class EventDrivenSync:
    """Sync strategy: sync only when significant state change is detected."""

    def __init__(self, config: dict):
        self.change_threshold = config.get("event_change_threshold", 0.05)
        self.max_silent_interval = config.get("full_state_interval_s", 10) * 6
        self.last_sync_tick = 0
        self.last_synced_state = None

    def should_sync(self, tick: int, device_state: dict, battery_pct: float = 1.0) -> bool:
        """
        Sync only if:
        1. A significant change is detected, OR
        2. Too much time has passed (heartbeat sync)
        """
        # Heartbeat: force sync after long silence
        if (tick - self.last_sync_tick) >= self.max_silent_interval:
            return True

        if self.last_synced_state is None:
            return True

        # Check for significant changes
        return self._detect_significant_change(device_state)

    def _detect_significant_change(self, current_state: dict) -> bool:
        """Detect if any key metric changed beyond the threshold."""
        if self.last_synced_state is None:
            return True

        checks = [
            ("cpu.utilization", "cpu", "utilization"),
            ("memory.utilization", "memory", "utilization"),
            ("battery.percentage", "battery", "percentage"),
            ("network.bandwidth_utilization", "network", "bandwidth_utilization"),
        ]

        for _label, section, field in checks:
            old_val = self.last_synced_state.get(section, {}).get(field, 0)
            new_val = current_state.get(section, {}).get(field, 0)
            if abs(new_val - old_val) > self.change_threshold:
                return True

        return False

    def prepare_payload(self, device_state: dict) -> dict:
        """Send full state (event-triggered syncs always send full state for simplicity)."""
        self.last_synced_state = {
            "cpu": device_state.get("cpu", {}),
            "memory": device_state.get("memory", {}),
            "battery": device_state.get("battery", {}),
            "network": device_state.get("network", {}),
        }
        self.last_sync_tick = device_state.get("tick", self.last_sync_tick)

        return {
            "type": "event_driven",
            "data": device_state,
        }

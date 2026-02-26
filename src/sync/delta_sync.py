"""
Delta Sync — Transmits only values that have changed significantly.

Reduces bandwidth by sending differential updates instead of full state.
"""


class DeltaSync:
    """Sync strategy: send only changed values (differential updates)."""

    def __init__(self, config: dict):
        self.interval_s = config.get("full_state_interval_s", 10)
        self.delta_threshold = config.get("delta_threshold", 0.02)
        self.last_sync_tick = 0
        self.last_synced_state = None

    def should_sync(self, tick: int, device_state: dict, battery_pct: float = 1.0) -> bool:
        """Sync at fixed intervals (but payload is smaller)."""
        return (tick - self.last_sync_tick) >= self.interval_s

    def prepare_payload(self, device_state: dict) -> dict:
        """Send only values that changed beyond the delta threshold."""
        if self.last_synced_state is None:
            # First sync — send everything
            self.last_synced_state = self._extract_numerics(device_state)
            self.last_sync_tick = device_state.get("tick", 0)
            return {
                "type": "full_state",
                "data": device_state,
            }

        current = self._extract_numerics(device_state)
        delta = {}

        for key, value in current.items():
            old_value = self.last_synced_state.get(key)
            if old_value is None or self._changed_significantly(old_value, value):
                delta[key] = value

        self.last_synced_state = current
        self.last_sync_tick = device_state.get("tick", self.last_sync_tick + self.interval_s)

        return {
            "type": "delta",
            "data": delta,
            "fields_changed": len(delta),
            "fields_total": len(current),
        }

    def _extract_numerics(self, state: dict) -> dict:
        """Flatten state dict to key-value pairs of numeric values."""
        flat = {}
        self._flatten(state, "", flat)
        return flat

    def _flatten(self, d: dict, prefix: str, result: dict):
        """Recursively flatten a nested dict."""
        if not isinstance(d, dict):
            return
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (int, float)):
                result[full_key] = value
            elif isinstance(value, dict):
                self._flatten(value, full_key, result)

    def _changed_significantly(self, old: float, new: float) -> bool:
        """Check if a value changed beyond the delta threshold."""
        if old == 0:
            return new != 0
        return abs(new - old) / abs(old) > self.delta_threshold

"""
Adaptive Sync — Adjusts sync frequency based on battery level and system activity.

Most energy-efficient strategy. Syncs frequently when battery is high,
and conserves energy by reducing frequency when battery is low.
"""


class AdaptiveSync:
    """Sync strategy: battery-aware, adaptive frequency synchronization."""

    def __init__(self, config: dict):
        adaptive_config = config.get("adaptive_config", {})
        self.high_battery_interval = adaptive_config.get("high_battery_interval_s", 5)
        self.medium_battery_interval = adaptive_config.get("medium_battery_interval_s", 15)
        self.low_battery_interval = adaptive_config.get("low_battery_interval_s", 60)
        self.high_battery_threshold = adaptive_config.get("high_battery_threshold", 0.50)
        self.low_battery_threshold = adaptive_config.get("low_battery_threshold", 0.15)
        self.last_sync_tick = 0
        self.current_interval = self.high_battery_interval

    def should_sync(self, tick: int, device_state: dict, battery_pct: float = 1.0) -> bool:
        """Sync based on adaptive interval determined by battery level."""
        self._update_interval(battery_pct)
        return (tick - self.last_sync_tick) >= self.current_interval

    def _update_interval(self, battery_pct: float):
        """Adjust sync interval based on remaining battery."""
        if battery_pct > self.high_battery_threshold:
            self.current_interval = self.high_battery_interval
        elif battery_pct > self.low_battery_threshold:
            self.current_interval = self.medium_battery_interval
        else:
            self.current_interval = self.low_battery_interval

    def prepare_payload(self, device_state: dict) -> dict:
        """Prepare payload — sends full state but at adaptive intervals."""
        self.last_sync_tick = device_state.get("tick", self.last_sync_tick)
        return {
            "type": "adaptive",
            "interval_used": self.current_interval,
            "data": device_state,
        }

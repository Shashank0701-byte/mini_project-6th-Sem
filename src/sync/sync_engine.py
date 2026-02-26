"""
Sync Engine — Manages synchronization between the physical device and its Digital Twin.

Supports multiple sync strategies: full-state, delta, event-driven, and adaptive.
Each strategy has different trade-offs between accuracy, energy, and bandwidth.
"""

import json
from .full_state_sync import FullStateSync
from .delta_sync import DeltaSync
from .event_driven_sync import EventDrivenSync
from .adaptive_sync import AdaptiveSync


STRATEGY_MAP = {
    "full_state": FullStateSync,
    "delta": DeltaSync,
    "event_driven": EventDrivenSync,
    "adaptive": AdaptiveSync,
}


class SyncEngine:
    """Controls data synchronization between the device and its Digital Twin."""

    def __init__(self, config: dict, strategy_name: str = None):
        sync_config = config["sync"]
        self.strategy_name = strategy_name or sync_config["default_strategy"]

        if self.strategy_name not in STRATEGY_MAP:
            raise ValueError(
                f"Unknown sync strategy: {self.strategy_name}. "
                f"Available: {list(STRATEGY_MAP.keys())}"
            )

        self.strategy = STRATEGY_MAP[self.strategy_name](sync_config)

        # Stats
        self.total_syncs = 0
        self.total_bytes_synced = 0
        self.sync_events = []  # Log of all sync events

    def should_sync(self, tick: int, device_state: dict, battery_pct: float = 1.0) -> bool:
        """
        Determine if a sync should occur at this tick.
        
        Args:
            tick: Current simulation tick
            device_state: Current device state
            battery_pct: Current battery percentage (0.0 to 1.0)
            
        Returns:
            True if sync should occur
        """
        return self.strategy.should_sync(tick, device_state, battery_pct)

    def prepare_payload(self, device_state: dict) -> dict:
        """
        Prepare the sync payload based on the strategy.
        
        Returns:
            dict with 'payload' (data to send) and 'size_bytes' (payload size)
        """
        payload = self.strategy.prepare_payload(device_state)
        payload_json = json.dumps(payload, default=str)
        size_bytes = len(payload_json.encode("utf-8"))

        return {
            "payload": payload,
            "size_bytes": size_bytes,
        }

    def record_sync(self, tick: int, size_bytes: int, success: bool):
        """Record a sync event for statistics."""
        self.total_syncs += 1
        if success:
            self.total_bytes_synced += size_bytes
        self.sync_events.append({
            "tick": tick,
            "size_bytes": size_bytes,
            "success": success,
            "strategy": self.strategy_name,
        })

    def get_stats(self) -> dict:
        """Return sync statistics."""
        return {
            "strategy": self.strategy_name,
            "total_syncs": self.total_syncs,
            "total_bytes_synced": self.total_bytes_synced,
            "avg_payload_bytes": (
                self.total_bytes_synced / self.total_syncs
                if self.total_syncs > 0 else 0
            ),
        }

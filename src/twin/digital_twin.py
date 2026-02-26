"""
Digital Twin — Virtual mirror of the physical IoT device.

Maintains a copy of the device state, tracks state drift between
the physical device and its twin, and provides state interpolation
between sync events.
"""

import copy
import math


class DigitalTwin:
    """Virtual representation of the physical IoT sensor node."""

    def __init__(self, config: dict):
        self.config = config
        self.device_state = None          # Last known device state
        self.predicted_state = None       # Interpolated/predicted state
        self.state_history = []           # History of received states
        self.drift_history = []           # State drift over time

        # Sync tracking
        self.total_syncs = 0
        self.last_sync_tick = 0
        self.sync_success_count = 0
        self.sync_fail_count = 0

        # Accuracy tracking
        self.accuracy_history = []
        self.current_drift = 0.0

    def receive_sync(self, device_state: dict, tick: int):
        """
        Receive a state update from the physical device.
        
        Args:
            device_state: Full device state snapshot
            tick: Current simulation tick
        """
        # Calculate drift before updating
        if self.predicted_state is not None:
            self.current_drift = self._calculate_drift(self.predicted_state, device_state)
        else:
            self.current_drift = 0.0

        self.device_state = copy.deepcopy(device_state)
        self.predicted_state = copy.deepcopy(device_state)
        self.last_sync_tick = tick
        self.total_syncs += 1
        self.sync_success_count += 1

        accuracy = 1.0 - self.current_drift
        self.accuracy_history.append(accuracy)
        self.drift_history.append(self.current_drift)

        self.state_history.append({
            "tick": tick,
            "state": copy.deepcopy(device_state),
            "drift": self.current_drift,
        })

    def record_sync_failure(self, tick: int):
        """Record a failed sync attempt."""
        self.sync_fail_count += 1
        self.total_syncs += 1

    def tick(self, current_tick: int):
        """
        Advance the twin by one tick. If no sync occurred, the twin
        predicts/interpolates the device state based on trends.
        """
        if self.predicted_state is None:
            return

        ticks_since_sync = current_tick - self.last_sync_tick

        # Drift increases with time since last sync
        # Simple model: drift grows linearly with time since sync
        self.current_drift = min(1.0, ticks_since_sync * 0.0005)

        # Interpolate battery drain (predict continued depletion)
        if "battery" in self.predicted_state:
            bat = self.predicted_state["battery"]
            if "remaining_mah" in bat and bat["remaining_mah"] > 0:
                # Estimate drain rate from total consumed / total ticks
                if self.last_sync_tick > 0:
                    drain_rate = bat.get("total_consumed_mah", 0) / max(self.last_sync_tick, 1)
                    bat["remaining_mah"] = max(
                        0, bat["remaining_mah"] - drain_rate * (current_tick - self.last_sync_tick)
                    )

        accuracy = max(0.0, 1.0 - self.current_drift)
        self.accuracy_history.append(accuracy)
        self.drift_history.append(self.current_drift)

    def _calculate_drift(self, predicted: dict, actual: dict) -> float:
        """
        Calculate normalized drift between predicted and actual states.
        Compares key numeric fields and returns average relative error.
        """
        diffs = []

        # Compare battery
        pred_bat = predicted.get("battery", {})
        actual_bat = actual.get("battery", {})
        if pred_bat.get("remaining_mah") and actual_bat.get("remaining_mah"):
            cap = actual_bat.get("capacity_mah", 1000)
            diff = abs(pred_bat["remaining_mah"] - actual_bat["remaining_mah"]) / cap
            diffs.append(diff)

        # Compare memory
        pred_mem = predicted.get("memory", {})
        actual_mem = actual.get("memory", {})
        if pred_mem.get("total_kb") and actual_mem.get("total_kb"):
            diff = abs(pred_mem.get("used_kb", 0) - actual_mem.get("used_kb", 0)) / actual_mem["total_kb"]
            diffs.append(diff)

        # Compare CPU
        pred_cpu = predicted.get("cpu", {})
        actual_cpu = actual.get("cpu", {})
        if "utilization" in actual_cpu:
            diff = abs(pred_cpu.get("utilization", 0) - actual_cpu.get("utilization", 0))
            diffs.append(diff)

        if not diffs:
            return 0.0
        return sum(diffs) / len(diffs)

    def get_avg_accuracy(self) -> float:
        """Return average twin accuracy across all ticks."""
        if not self.accuracy_history:
            return 1.0
        return sum(self.accuracy_history) / len(self.accuracy_history)

    def get_max_drift(self) -> tuple:
        """Return (max_drift, tick_index) of the maximum state drift."""
        if not self.drift_history:
            return (0.0, 0)
        max_drift = max(self.drift_history)
        max_tick = self.drift_history.index(max_drift)
        return (max_drift, max_tick)

    def get_sync_success_rate(self) -> float:
        """Return sync success rate."""
        if self.total_syncs == 0:
            return 1.0
        return self.sync_success_count / self.total_syncs

    def get_state(self) -> dict:
        """Return current twin state."""
        max_drift, max_drift_tick = self.get_max_drift()
        return {
            "device_state": self.device_state,
            "current_drift": round(self.current_drift, 4),
            "avg_accuracy": round(self.get_avg_accuracy(), 4),
            "max_drift": round(max_drift, 4),
            "max_drift_tick": max_drift_tick,
            "total_syncs": self.total_syncs,
            "sync_success_rate": round(self.get_sync_success_rate(), 4),
            "last_sync_tick": self.last_sync_tick,
        }

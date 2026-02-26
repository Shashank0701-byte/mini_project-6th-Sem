"""Tests for the Digital Twin state mirroring and drift tracking."""

import json
import os
import pytest
import numpy as np

TEST_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "default_config.json"
)

with open(TEST_CONFIG_PATH, "r") as f:
    TEST_CONFIG = json.load(f)


SAMPLE_DEVICE_STATE = {
    "cpu": {"utilization": 0.35, "cycles_used": 2500, "peak_utilization": 0.45,
            "overload_events": 0, "consecutive_overload_ticks": 0},
    "memory": {"used_kb": 45.0, "total_kb": 256, "utilization": 0.176,
               "buffer_count": 3, "leaked_kb": 0.5, "peak_usage_kb": 50.0, "oom_events": 0},
    "battery": {"remaining_mah": 950.0, "capacity_mah": 1000, "percentage": 95.0,
                "total_consumed_mah": 50.0, "depleted": False,
                "energy_breakdown_mah": {"sensing": 5, "processing": 20, "transmission": 24, "idle": 1},
                "energy_breakdown_pct": {"sensing": 10, "processing": 40, "transmission": 48, "idle": 2}},
    "network": {"type": "LoRa", "bandwidth_utilization": 0.15, "peak_bandwidth_utilization": 0.3,
                "total_bytes_sent": 5000, "total_packets_sent": 50, "total_packets_lost": 1,
                "packet_loss_rate": 0.02, "congestion_events": 0},
    "sensors": {"last_reading": {"temperature": 25.3, "humidity": 58.1, "light": 400, "anomalies": []},
                "total_readings": 100, "anomaly_count": 2},
    "is_active": True,
    "tick": 500,
}


class TestDigitalTwin:
    """Test Digital Twin state mirroring."""

    def setup_method(self):
        from src.twin.digital_twin import DigitalTwin
        self.twin = DigitalTwin(TEST_CONFIG)

    def test_initial_state(self):
        """Twin should start with no state."""
        state = self.twin.get_state()
        assert state["device_state"] is None
        assert state["total_syncs"] == 0

    def test_receive_sync(self):
        """Twin should store device state after sync."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=500)
        state = self.twin.get_state()
        assert state["device_state"] is not None
        assert state["total_syncs"] == 1
        assert state["last_sync_tick"] == 500

    def test_drift_increases_without_sync(self):
        """Drift should increase when twin doesn't receive syncs."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=100)
        initial_drift = self.twin.current_drift

        # Advance many ticks without sync
        for t in range(101, 300):
            self.twin.tick(t)

        assert self.twin.current_drift > initial_drift

    def test_drift_resets_on_sync(self):
        """Drift should reset when a new sync is received."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=100)
        for t in range(101, 200):
            self.twin.tick(t)

        high_drift = self.twin.current_drift
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=200)

        # Drift should be lower after sync
        assert self.twin.current_drift <= high_drift

    def test_accuracy_tracking(self):
        """Average accuracy should be tracked."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=100)
        accuracy = self.twin.get_avg_accuracy()
        assert 0 <= accuracy <= 1.0

    def test_sync_success_rate(self):
        """Sync success rate should be calculated correctly."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=100)
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=200)
        self.twin.record_sync_failure(tick=300)

        rate = self.twin.get_sync_success_rate()
        assert rate == pytest.approx(2 / 3, abs=0.01)

    def test_max_drift(self):
        """Max drift should be tracked."""
        self.twin.receive_sync(SAMPLE_DEVICE_STATE, tick=100)
        for t in range(101, 500):
            self.twin.tick(t)

        max_drift, max_tick = self.twin.get_max_drift()
        assert max_drift > 0
        assert max_tick > 0

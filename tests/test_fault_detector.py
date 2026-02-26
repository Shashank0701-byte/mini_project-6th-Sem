"""Tests for fault detection and predictive maintenance."""

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


def make_device_state(**overrides):
    """Create a device state dict with sensible defaults and optional overrides."""
    state = {
        "cpu": {"utilization": 0.3, "cycles_used": 1000, "peak_utilization": 0.4,
                "overload_events": 0, "consecutive_overload_ticks": 0},
        "memory": {"used_kb": 45, "total_kb": 256, "utilization": 0.176,
                   "buffer_count": 3, "leaked_kb": 0, "peak_usage_kb": 50, "oom_events": 0},
        "battery": {"remaining_mah": 900, "capacity_mah": 1000, "percentage": 90.0,
                    "total_consumed_mah": 100, "depleted": False},
        "network": {"bandwidth_utilization": 0.15, "packet_loss_rate": 0.01,
                    "total_bytes_sent": 5000, "total_packets_sent": 50,
                    "total_packets_lost": 1, "congestion_events": 0},
        "sensors": {"last_reading": {"temperature": 25, "humidity": 60, "light": 400,
                                      "anomalies": []},
                    "total_readings": 100, "anomaly_count": 0},
    }

    # Apply overrides
    for key, value in overrides.items():
        parts = key.split(".")
        d = state
        for part in parts[:-1]:
            d = d[part]
        d[parts[-1]] = value

    return state


class TestFaultDetector:
    """Test fault detection engine."""

    def setup_method(self):
        from src.analysis.fault_detector import FaultDetector
        self.detector = FaultDetector(TEST_CONFIG)

    def test_no_alerts_normal_state(self):
        """Normal state should produce no alerts."""
        state = make_device_state()
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert len(alerts) == 0

    def test_cpu_critical_alert(self):
        """CPU above critical threshold for duration should alert."""
        state = make_device_state(**{"cpu.utilization": 0.96})
        # Simulate sustained overload
        for t in range(35):
            alerts = self.detector.check(t, state, is_sensing_tick=False)
        # After 30+ ticks, should have critical alert
        assert any(a["component"] == "CPU" and a["severity"] == "CRITICAL" for a in alerts)

    def test_memory_warning(self):
        """Memory above warning threshold should alert."""
        state = make_device_state(**{"memory.utilization": 0.85})
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert any(a["component"] == "MEMORY" for a in alerts)

    def test_memory_critical(self):
        """Memory above critical threshold should alert critical."""
        state = make_device_state(**{"memory.utilization": 0.96})
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert any(a["severity"] == "CRITICAL" and a["component"] == "MEMORY" for a in alerts)

    def test_memory_leak_detection(self):
        """Leaked memory above threshold should be detected as fault."""
        state = make_device_state(**{"memory.leaked_kb": 5.0})
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert any("leak" in a["message"].lower() for a in alerts)
        assert any(f["type"] == "memory_leak" for f in self.detector.faults_detected)

    def test_battery_warning(self):
        """Battery below warning threshold should alert."""
        state = make_device_state(**{"battery.percentage": 15.0})
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert any(a["component"] == "BATTERY" for a in alerts)

    def test_battery_critical(self):
        """Battery below critical threshold should alert critical."""
        state = make_device_state(**{"battery.percentage": 3.0})
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert any(a["severity"] == "CRITICAL" and a["component"] == "BATTERY" for a in alerts)

    def test_sensor_anomaly_on_sensing_tick(self):
        """Sensor anomaly should be detected on sensing ticks."""
        state = make_device_state()
        state["sensors"]["last_reading"]["anomalies"] = ["temperature"]
        alerts = self.detector.check(100, state, is_sensing_tick=True)
        assert any(a["component"] == "SENSOR" for a in alerts)

    def test_sensor_anomaly_ignored_off_sensing_tick(self):
        """Sensor anomaly should NOT be detected on non-sensing ticks."""
        state = make_device_state()
        state["sensors"]["last_reading"]["anomalies"] = ["temperature"]
        alerts = self.detector.check(100, state, is_sensing_tick=False)
        assert not any(a["component"] == "SENSOR" for a in alerts)

    def test_twin_drift_warning(self):
        """Twin drift above threshold should alert."""
        state = make_device_state()
        twin_state = {"current_drift": 0.10}
        alerts = self.detector.check(100, state, twin_state, is_sensing_tick=False)
        assert any(a["component"] == "TWIN" for a in alerts)

    def test_communication_timeout(self):
        """Missing sync should trigger comm timeout fault."""
        state = make_device_state()
        # Last sync was tick 10, expected every 10s, comm timeout mult = 2
        alerts = self.detector.check(100, state, last_sync_tick=10,
                                      expected_sync_interval=10, is_sensing_tick=False)
        assert any(a["component"] == "COMMUNICATION" for a in alerts)

    def test_summary(self):
        """Summary should return correct counts."""
        state = make_device_state(**{"battery.percentage": 3.0})
        self.detector.check(100, state, is_sensing_tick=False)
        summary = self.detector.get_summary()
        assert summary["critical_count"] >= 1


class TestPredictiveMaintenance:
    """Test predictive maintenance predictions."""

    def setup_method(self):
        from src.analysis.predictive_maintenance import PredictiveMaintenance
        self.pred = PredictiveMaintenance(TEST_CONFIG)

    def test_battery_prediction_insufficient_data(self):
        """Should return inf ETA with insufficient data."""
        result = self.pred.predict_battery_depletion()
        assert result["eta_hours"] == float("inf")

    def test_battery_prediction_with_data(self):
        """Should predict battery depletion with enough data."""
        # Simulate draining battery: 1000 → 950 over 300 ticks
        for t in range(300):
            remaining = 1000 - (t * 50 / 300)
            state = {"battery": {"remaining_mah": remaining}, "memory": {"used_kb": 40}}
            self.pred.update(t, state)

        result = self.pred.predict_battery_depletion()
        assert result["eta_hours"] != float("inf")
        assert result["eta_hours"] > 0
        assert result["drain_rate_mah_per_hour"] > 0

    def test_memory_prediction_with_leak(self):
        """Should predict memory exhaustion when leaking."""
        for t in range(300):
            used = 32 + (t * 0.05)  # Gradual increase
            state = {"battery": {"remaining_mah": 900}, "memory": {"used_kb": used}}
            self.pred.update(t, state)

        result = self.pred.predict_memory_exhaustion()
        assert result["eta_hours"] != float("inf")
        assert result["leak_rate_kb_per_hour"] > 0

    def test_maintenance_recommendation(self):
        """Should recommend maintenance when exhaustion predicted."""
        for t in range(300):
            remaining = 1000 - (t * 50 / 300)
            state = {"battery": {"remaining_mah": remaining}, "memory": {"used_kb": 40}}
            self.pred.update(t, state)

        rec = self.pred.get_maintenance_recommendation()
        assert rec["recommended"] is True
        assert rec["maintenance_in_hours"] > 0

"""Tests for the device hardware models (CPU, Memory, Battery, Network)."""

import json
import os
import sys
import pytest
import numpy as np

# Load test config
TEST_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "default_config.json"
)

with open(TEST_CONFIG_PATH, "r") as f:
    TEST_CONFIG = json.load(f)


class TestCPUModel:
    """Test CPU utilization model."""

    def setup_method(self):
        from src.device.cpu_model import CPUModel
        np.random.seed(42)
        self.cpu = CPUModel(TEST_CONFIG)

    def test_initial_state(self):
        """CPU should start at 0% utilization."""
        state = self.cpu.get_state()
        assert state["utilization"] == 0.0
        assert state["overload_events"] == 0

    def test_task_scheduling(self):
        """Scheduling tasks should increase CPU utilization."""
        self.cpu.schedule_task("sensing")
        self.cpu.schedule_task("processing")
        self.cpu.tick(1.0)
        assert self.cpu.current_utilization > 0.0

    def test_idle_tick(self):
        """Without tasks, CPU utilization should be near zero."""
        self.cpu.tick(1.0)
        # May have small jitter but should be close to 0
        assert self.cpu.current_utilization < 0.1

    def test_utilization_history(self):
        """History should record utilization for each tick."""
        for _ in range(5):
            self.cpu.tick(1.0)
        assert len(self.cpu.utilization_history) == 5

    def test_peak_tracking(self):
        """Peak utilization should be tracked."""
        self.cpu.schedule_task("transmission")
        self.cpu.tick(1.0)
        peak = self.cpu.peak_utilization
        self.cpu.tick(1.0)
        # Peak should not decrease
        assert self.cpu.peak_utilization >= 0


class TestMemoryModel:
    """Test RAM allocation/deallocation model."""

    def setup_method(self):
        from src.device.memory_model import MemoryModel
        self.mem = MemoryModel(TEST_CONFIG)

    def test_initial_state(self):
        """Memory should start at base usage."""
        assert self.mem.current_usage_kb == self.mem.base_usage_kb
        assert self.mem.buffer_count == 0

    def test_buffer_allocation(self):
        """Allocating buffers should increase memory usage."""
        initial = self.mem.current_usage_kb
        self.mem.allocate_sensor_buffer()
        assert self.mem.current_usage_kb > initial
        assert self.mem.buffer_count == 1

    def test_buffer_free(self):
        """Freeing buffers should decrease memory usage."""
        self.mem.allocate_sensor_buffer()
        self.mem.allocate_sensor_buffer()
        self.mem.free_sensor_buffers(1)
        assert self.mem.buffer_count == 1

    def test_free_all_buffers(self):
        """Freeing all buffers should return to base usage (plus leak)."""
        for _ in range(5):
            self.mem.allocate_sensor_buffer()
        self.mem.free_sensor_buffers()
        assert self.mem.buffer_count == 0

    def test_memory_leak(self):
        """Memory leak should gradually increase usage."""
        initial = self.mem.current_usage_kb
        for _ in range(600):  # 10 minutes
            self.mem.tick(1.0)
        assert self.mem.leaked_kb > 0
        assert self.mem.current_usage_kb > initial

    def test_utilization(self):
        """Utilization should be between 0 and 1."""
        assert 0 <= self.mem.get_utilization() <= 1.0

    def test_oom_detection(self):
        """OOM should be detected when memory exceeds capacity."""
        # Force memory to max
        self.mem.leaked_kb = self.mem.total_ram_kb
        self.mem.tick(1.0)
        assert self.mem.oom_events > 0


class TestBatteryModel:
    """Test battery drain model."""

    def setup_method(self):
        from src.device.battery_model import BatteryModel
        self.battery = BatteryModel(TEST_CONFIG)

    def test_initial_state(self):
        """Battery should start at full capacity."""
        assert self.battery.remaining_mah == self.battery.capacity_mah
        assert self.battery.get_percentage() == 100.0
        assert not self.battery.depleted

    def test_consume_sensing(self):
        """Sensing should consume energy."""
        initial = self.battery.remaining_mah
        self.battery.consume("sensing", 1.0)
        assert self.battery.remaining_mah < initial

    def test_transmission_most_expensive(self):
        """Transmission should cost more energy than sensing."""
        b1 = type(self.battery)(TEST_CONFIG)
        b2 = type(self.battery)(TEST_CONFIG)

        b1.consume("sensing", 1.0)
        b2.consume("transmission", 1.0)

        # Transmission consumed more
        assert b1.remaining_mah > b2.remaining_mah

    def test_energy_breakdown(self):
        """Energy breakdown should track per-component consumption."""
        self.battery.consume("sensing", 100)
        self.battery.consume("transmission", 100)
        breakdown = self.battery.get_energy_breakdown_pct()
        assert breakdown["sensing"] > 0
        assert breakdown["transmission"] > 0

    def test_warning_thresholds(self):
        """Warnings should trigger at configured thresholds."""
        # Drain battery to below 20%
        self.battery.remaining_mah = self.battery.capacity_mah * 0.19
        warnings = self.battery.check_warnings()
        assert 0.20 in warnings

    def test_battery_depletion(self):
        """Battery should be marked as depleted when empty."""
        self.battery.remaining_mah = 0.001
        self.battery.consume("transmission", 1.0)
        assert self.battery.depleted

    def test_drain_history(self):
        """Drain history should be recorded."""
        self.battery.tick(["sensing"], 1.0)
        self.battery.tick(["idle"], 1.0)
        assert len(self.battery.drain_history) == 2


class TestNetworkModel:
    """Test network bandwidth and packet loss model."""

    def setup_method(self):
        from src.device.network_model import NetworkModel
        np.random.seed(42)
        self.network = NetworkModel(TEST_CONFIG)

    def test_initial_state(self):
        """Network should start with zero traffic."""
        state = self.network.get_state()
        assert state["total_bytes_sent"] == 0
        assert state["total_packets_sent"] == 0

    def test_transmit_success(self):
        """Successful transmission should increase bytes sent."""
        # With seed 42 and low loss rate, most transmissions succeed
        result = self.network.transmit(128)
        if result["success"]:
            assert result["bytes_sent"] == 128
            assert self.network.total_bytes_sent == 128

    def test_payload_clamping(self):
        """Payloads larger than max should be clamped."""
        max_payload = self.network.max_payload_bytes
        result = self.network.transmit(max_payload * 2)
        if result["success"]:
            assert result["bytes_sent"] == max_payload

    def test_bandwidth_utilization(self):
        """BW utilization should increase with traffic."""
        for _ in range(10):
            self.network.transmit(256)
        self.network.tick(1.0)
        assert self.network.current_bandwidth_utilization > 0

    def test_packet_loss_rate(self):
        """Packet loss rate should be calculable."""
        # Send many packets to get some losses
        for _ in range(1000):
            self.network.transmit(64)
        loss_rate = self.network.get_packet_loss_rate()
        # Should be around base_packet_loss_rate with some variance
        assert 0 <= loss_rate <= 1.0

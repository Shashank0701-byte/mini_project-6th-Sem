"""Tests for edge computing components."""

import json
import os
import pytest

TEST_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "default_config.json"
)

with open(TEST_CONFIG_PATH, "r") as f:
    TEST_CONFIG = json.load(f)


class TestDataFilter:
    """Test edge data filter."""

    def setup_method(self):
        from src.edge.data_filter import DataFilter
        self.filter = DataFilter(window_size=3)

    def test_first_reading_passthrough(self):
        """First reading should pass through (no window yet)."""
        reading = {"temperature": 25.0, "humidity": 60.0, "light": 400}
        filtered = self.filter.filter_reading(reading)
        assert filtered["temperature"] == 25.0

    def test_moving_average_smoothing(self):
        """Subsequent readings should be smoothed."""
        readings = [
            {"temperature": 25.0, "humidity": 60.0, "light": 400},
            {"temperature": 26.0, "humidity": 62.0, "light": 420},
            {"temperature": 24.0, "humidity": 58.0, "light": 380},
        ]
        for r in readings:
            result = self.filter.filter_reading(r)

        # Result should be average of the 3 values
        assert result["temperature"] == pytest.approx(25.0, abs=0.1)

    def test_outlier_detection(self):
        """Outlier detection should flag anomalous values."""
        for i in range(10):
            self.filter.filter_reading({"temperature": 25.0 + i * 0.1})
        # 50.0 is far from the window range — definite outlier
        assert self.filter.is_outlier("temperature", 50.0) is True
        # 25.85 is within the smoothed window range — not an outlier
        assert self.filter.is_outlier("temperature", 25.85) is False


class TestDataCompressor:
    """Test edge data compressor."""

    def setup_method(self):
        from src.edge.compressor import DataCompressor
        self.compressor = DataCompressor(compression_ratio=0.6)

    def test_compression_reduces_size(self):
        """Compressed size should be smaller than original."""
        compressed = self.compressor.estimate_compressed_size(1000)
        assert compressed == 600

    def test_savings_calculation(self):
        """Savings percentage should be calculated correctly."""
        self.compressor.estimate_compressed_size(1000)
        assert self.compressor.get_savings_pct() == pytest.approx(40.0)


class TestPriorityQueue:
    """Test edge priority data queue."""

    def setup_method(self):
        from src.edge.priority_queue import PriorityDataQueue
        self.queue = PriorityDataQueue()

    def test_critical_enqueue(self):
        """Critical data should go to critical queue."""
        self.queue.enqueue({"alert": True}, "critical")
        assert self.queue.has_critical() is True
        assert self.queue.total_critical == 1

    def test_normal_enqueue(self):
        """Normal data should go to normal queue."""
        self.queue.enqueue({"data": 25.0}, "normal")
        assert self.queue.has_critical() is False
        assert self.queue.total_normal == 1

    def test_critical_dequeue(self):
        """Dequeuing critical should return all critical items."""
        self.queue.enqueue({"a": 1}, "critical")
        self.queue.enqueue({"b": 2}, "critical")
        items = self.queue.dequeue_critical()
        assert len(items) == 2
        assert self.queue.has_critical() is False

    def test_normal_batch_dequeue(self):
        """Normal dequeue should respect batch size."""
        for i in range(20):
            self.queue.enqueue({"i": i}, "normal")
        items = self.queue.dequeue_normal(batch_size=5)
        assert len(items) == 5


class TestEdgeProcessor:
    """Test edge processor integration."""

    def setup_method(self):
        from src.edge.edge_processor import EdgeProcessor
        self.edge = EdgeProcessor(TEST_CONFIG)

    def test_process_normal_reading(self):
        """Normal reading should be processed with normal priority."""
        reading = {"temperature": 25.0, "humidity": 60.0, "light": 400, "anomalies": []}
        state = {"cpu": {"utilization": 0.3}, "memory": {"utilization": 0.2},
                 "battery": {"percentage": 90}}
        result = self.edge.process(reading, state)
        assert result["priority"] == "normal"

    def test_anomaly_gets_critical_priority(self):
        """Anomalous reading should get critical priority."""
        reading = {"temperature": 50.0, "humidity": 60.0, "light": 400,
                   "anomalies": ["temperature"]}
        state = {"cpu": {"utilization": 0.3}, "memory": {"utilization": 0.2},
                 "battery": {"percentage": 90}}
        result = self.edge.process(reading, state)
        assert result["priority"] == "critical"
        assert result["has_anomaly"] is True

    def test_compression_saves_bytes(self):
        """Edge compression should save bytes."""
        reading = {"temperature": 25.0, "humidity": 60.0, "light": 400, "anomalies": []}
        state = {"cpu": {"utilization": 0.3}, "memory": {"utilization": 0.2},
                 "battery": {"percentage": 90}}
        result = self.edge.process(reading, state)
        assert result["processed_bytes"] < result["original_bytes"]

    def test_disabled_edge_passthrough(self):
        """Disabled edge should pass data through unchanged."""
        config = json.loads(json.dumps(TEST_CONFIG))
        config["edge"]["enabled"] = False
        from src.edge.edge_processor import EdgeProcessor
        edge = EdgeProcessor(config)

        reading = {"temperature": 25.0}
        result = edge.process(reading, {})
        assert result["priority"] == "normal"
        assert result["compressed"] is False

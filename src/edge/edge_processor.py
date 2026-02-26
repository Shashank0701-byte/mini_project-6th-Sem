"""
Edge Processor — Simulates edge computing layer between device and cloud/twin.

Handles local data filtering, compression, priority queuing, and anomaly detection
to reduce bandwidth and save energy on the constrained device.
"""

from .data_filter import DataFilter
from .compressor import DataCompressor
from .priority_queue import PriorityDataQueue


class EdgeProcessor:
    """Orchestrates edge computing operations on device data."""

    def __init__(self, config: dict):
        edge_config = config.get("edge", {})
        self.enabled = edge_config.get("enabled", True)
        self.compression_enabled = edge_config.get("compression_enabled", True)
        self.anomaly_immediate_sync = edge_config.get("anomaly_immediate_sync", True)

        self.data_filter = DataFilter(
            window_size=edge_config.get("filter_window_size", 5)
        )
        self.compressor = DataCompressor(
            compression_ratio=edge_config.get("compression_ratio", 0.6)
        )
        self.priority_queue = PriorityDataQueue()

        # Stats
        self.total_processed = 0
        self.total_filtered = 0
        self.total_compressed_bytes_saved = 0
        self.anomalies_fast_tracked = 0

    def process(self, sensor_reading: dict, device_state: dict) -> dict:
        """
        Process a sensor reading through the edge pipeline.
        
        Pipeline: Filter → Compress → Prioritize
        
        Args:
            sensor_reading: Raw sensor data
            device_state: Current device state
            
        Returns:
            dict with processed data, priority, and metadata
        """
        if not self.enabled:
            return {
                "data": sensor_reading,
                "priority": "normal",
                "compressed": False,
                "filtered": False,
                "original_bytes": 0,
                "processed_bytes": 0,
            }

        self.total_processed += 1

        # Step 1: Filter noise
        filtered_reading = self.data_filter.filter_reading(sensor_reading)
        is_filtered = filtered_reading != sensor_reading
        if is_filtered:
            self.total_filtered += 1

        # Step 2: Determine priority
        has_anomaly = bool(sensor_reading.get("anomalies", []))
        has_critical_resource = self._check_critical_resources(device_state)

        if has_anomaly or has_critical_resource:
            priority = "critical"
            if has_anomaly:
                self.anomalies_fast_tracked += 1
        else:
            priority = "normal"

        self.priority_queue.enqueue(filtered_reading, priority)

        # Step 3: Estimate compression savings
        import json
        original_json = json.dumps(sensor_reading, default=str)
        original_bytes = len(original_json.encode("utf-8"))
        processed_bytes = original_bytes

        if self.compression_enabled:
            processed_bytes = self.compressor.estimate_compressed_size(original_bytes)
            self.total_compressed_bytes_saved += (original_bytes - processed_bytes)

        return {
            "data": filtered_reading,
            "priority": priority,
            "compressed": self.compression_enabled,
            "filtered": is_filtered,
            "original_bytes": original_bytes,
            "processed_bytes": processed_bytes,
            "has_anomaly": has_anomaly,
        }

    def _check_critical_resources(self, state: dict) -> bool:
        """Check if any resource is in critical state."""
        cpu_util = state.get("cpu", {}).get("utilization", 0)
        mem_util = state.get("memory", {}).get("utilization", 0)
        bat_pct = state.get("battery", {}).get("percentage", 100) / 100.0

        return cpu_util > 0.95 or mem_util > 0.95 or bat_pct < 0.05

    def get_data_reduction_ratio(self) -> float:
        """Return the ratio of data saved by edge processing."""
        if self.total_processed == 0:
            return 0.0
        return self.total_filtered / self.total_processed

    def get_stats(self) -> dict:
        """Return edge processing statistics."""
        return {
            "enabled": self.enabled,
            "total_processed": self.total_processed,
            "total_filtered": self.total_filtered,
            "data_reduction_ratio": round(self.get_data_reduction_ratio(), 4),
            "bytes_saved_by_compression": self.total_compressed_bytes_saved,
            "anomalies_fast_tracked": self.anomalies_fast_tracked,
        }

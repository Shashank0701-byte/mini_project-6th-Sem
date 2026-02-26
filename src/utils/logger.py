"""
Logger — Tick-by-tick data logger for simulation output.

Logs device state, twin state, and alerts as JSON or CSV files.
"""

import json
import os
import csv
from datetime import datetime


class SimulationLogger:
    """Logs simulation data tick-by-tick to JSON or CSV files."""

    def __init__(self, config: dict):
        sim_config = config["simulation"]
        self.log_format = sim_config.get("log_format", "json")
        self.output_dir = sim_config.get("log_output_dir", "logs")
        self.tick_data = []

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_base = f"simulation_{timestamp}"

    def log_tick(self, tick: int, device_state: dict, twin_state: dict,
                 alerts: list, sync_event: bool = False):
        """Log data for a single tick."""
        entry = {
            "tick": tick,
            "timestamp_s": tick,
            "time": f"{tick//3600:02d}:{(tick%3600)//60:02d}:{tick%60:02d}",
            "device": {
                "cpu_utilization": device_state.get("cpu", {}).get("utilization", 0),
                "memory_used_kb": device_state.get("memory", {}).get("used_kb", 0),
                "memory_total_kb": device_state.get("memory", {}).get("total_kb", 0),
                "battery_remaining_mah": device_state.get("battery", {}).get("remaining_mah", 0),
                "battery_percent": device_state.get("battery", {}).get("percentage", 0),
                "sensors": device_state.get("sensors", {}).get("last_reading", {}),
                "network": {
                    "bytes_sent": device_state.get("network", {}).get("total_bytes_sent", 0),
                    "bandwidth_utilization": device_state.get("network", {}).get("bandwidth_utilization", 0),
                    "packet_loss_rate": device_state.get("network", {}).get("packet_loss_rate", 0),
                },
            },
            "twin": {
                "state_accuracy": 1.0 - twin_state.get("current_drift", 0),
                "state_drift": twin_state.get("current_drift", 0),
                "last_sync_tick": twin_state.get("last_sync_tick", 0),
            },
            "alerts": [a.get("message", "") for a in alerts],
            "sync_event": sync_event,
        }
        self.tick_data.append(entry)

    def save(self):
        """Save all logged data to file."""
        if self.log_format == "json":
            self._save_json()
        elif self.log_format == "csv":
            self._save_csv()
        else:
            self._save_json()  # Default to JSON

    def _save_json(self):
        """Save data as JSON file."""
        filepath = os.path.join(self.output_dir, f"{self.filename_base}.json")
        with open(filepath, "w") as f:
            json.dump(self.tick_data, f, indent=2, default=str)
        return filepath

    def _save_csv(self):
        """Save data as CSV file (flattened)."""
        filepath = os.path.join(self.output_dir, f"{self.filename_base}.csv")

        if not self.tick_data:
            return filepath

        # Flatten the first entry to get headers
        flat = self._flatten(self.tick_data[0])
        headers = list(flat.keys())

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for entry in self.tick_data:
                writer.writerow(self._flatten(entry))

        return filepath

    def _flatten(self, d: dict, prefix: str = "") -> dict:
        """Flatten nested dict for CSV output."""
        flat = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flat.update(self._flatten(v, key))
            elif isinstance(v, list):
                flat[key] = "; ".join(str(item) for item in v)
            else:
                flat[key] = v
        return flat

    def get_filepath(self) -> str:
        """Return the output file path."""
        ext = "json" if self.log_format == "json" else "csv"
        return os.path.join(self.output_dir, f"{self.filename_base}.{ext}")

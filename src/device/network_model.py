"""
Network Model — Simulates bandwidth usage and packet transmission for a LoRa/BLE device.

Models limited bandwidth, payload sizes, congestion, and packet loss.
"""

import numpy as np


class NetworkModel:
    """Simulates network communication for a constrained IoT device."""

    def __init__(self, config: dict):
        net_config = config["device"]["network"]
        self.net_type = net_config["type"]
        self.max_bandwidth_kbps = net_config["max_bandwidth_kbps"]
        self.max_payload_bytes = net_config["max_payload_bytes"]
        self.base_packet_loss_rate = net_config["base_packet_loss_rate"]
        self.congestion_threshold = net_config["congestion_threshold"]
        self.congested_packet_loss_rate = net_config["congested_packet_loss_rate"]

        # State
        self.bytes_sent_this_tick = 0
        self.total_bytes_sent = 0
        self.total_packets_sent = 0
        self.total_packets_lost = 0
        self.current_bandwidth_utilization = 0.0
        self.peak_bandwidth_utilization = 0.0
        self.congestion_events = 0
        self.utilization_history = []

    def transmit(self, payload_bytes: int) -> dict:
        """
        Attempt to transmit a packet.
        
        Returns:
            dict with 'success', 'bytes_sent', 'packet_loss'
        """
        # Check congestion
        is_congested = self.current_bandwidth_utilization >= self.congestion_threshold

        # Determine packet loss
        loss_rate = (
            self.congested_packet_loss_rate if is_congested
            else self.base_packet_loss_rate
        )
        packet_lost = np.random.random() < loss_rate

        if packet_lost:
            self.total_packets_lost += 1
            self.total_packets_sent += 1
            return {
                "success": False,
                "bytes_sent": 0,
                "packet_loss": True,
                "congested": is_congested,
            }

        # Clamp payload to max size
        actual_bytes = min(payload_bytes, self.max_payload_bytes)
        self.bytes_sent_this_tick += actual_bytes
        self.total_bytes_sent += actual_bytes
        self.total_packets_sent += 1

        return {
            "success": True,
            "bytes_sent": actual_bytes,
            "packet_loss": False,
            "congested": is_congested,
        }

    def tick(self, time_step_s: float = 1.0):
        """Update bandwidth utilization for this tick."""
        # Max bytes per tick = max_bandwidth_kbps * 1000/8 * time_step
        max_bytes = (self.max_bandwidth_kbps * 1000 / 8) * time_step_s
        self.current_bandwidth_utilization = (
            self.bytes_sent_this_tick / max_bytes if max_bytes > 0 else 0.0
        )
        self.current_bandwidth_utilization = min(1.0, self.current_bandwidth_utilization)

        if self.current_bandwidth_utilization > self.peak_bandwidth_utilization:
            self.peak_bandwidth_utilization = self.current_bandwidth_utilization

        if self.current_bandwidth_utilization >= self.congestion_threshold:
            self.congestion_events += 1

        self.utilization_history.append(self.current_bandwidth_utilization)

        # Reset per-tick counter
        self.bytes_sent_this_tick = 0

        return self.current_bandwidth_utilization

    def get_packet_loss_rate(self) -> float:
        """Return overall packet loss rate."""
        if self.total_packets_sent == 0:
            return 0.0
        return self.total_packets_lost / self.total_packets_sent

    def get_state(self) -> dict:
        """Return current network state."""
        return {
            "type": self.net_type,
            "bandwidth_utilization": round(self.current_bandwidth_utilization, 4),
            "peak_bandwidth_utilization": round(self.peak_bandwidth_utilization, 4),
            "total_bytes_sent": self.total_bytes_sent,
            "total_packets_sent": self.total_packets_sent,
            "total_packets_lost": self.total_packets_lost,
            "packet_loss_rate": round(self.get_packet_loss_rate(), 4),
            "congestion_events": self.congestion_events,
        }

    def get_avg_utilization(self) -> float:
        """Return average bandwidth utilization across all ticks."""
        if not self.utilization_history:
            return 0.0
        return sum(self.utilization_history) / len(self.utilization_history)

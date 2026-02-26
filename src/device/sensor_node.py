"""
Sensor Node — Orchestrates the physical IoT device simulation.

Combines CPU, Memory, Battery, Network, and Sensor models into a
unified device that performs sensing, processing, and transmission cycles.
"""

from .cpu_model import CPUModel
from .memory_model import MemoryModel
from .battery_model import BatteryModel
from .network_model import NetworkModel
from .sensor_data import SensorDataGenerator


class SensorNode:
    """Simulates a complete IoT sensor node with constrained resources."""

    def __init__(self, config: dict):
        self.config = config
        self.sampling_rate_s = config["simulation"]["sampling_rate_seconds"]

        # Hardware components
        self.cpu = CPUModel(config)
        self.memory = MemoryModel(config)
        self.battery = BatteryModel(config)
        self.network = NetworkModel(config)
        self.sensors = SensorDataGenerator(config)

        # Device state
        self.tick_count = 0
        self.total_readings = 0
        self.last_reading = None
        self.is_active = True

    def tick(self, time_step_s: float = 1.0) -> dict:
        """
        Advance the device by one simulation tick.
        
        Returns:
            dict with device state and any new sensor reading
        """
        if not self.is_active or self.battery.depleted:
            self.is_active = False
            return self._get_inactive_state()

        self.tick_count += 1
        new_reading = None
        active_operations = []

        # Determine if this tick is a sensing tick
        is_sensing_tick = (self.tick_count % self.sampling_rate_s == 0)

        if is_sensing_tick:
            # --- SENSING PHASE ---
            self.cpu.schedule_task("sensing")
            active_operations.append("sensing")

            reading = self.sensors.generate_reading(self.tick_count, time_step_s)
            self.last_reading = reading
            self.total_readings += 1

            # Allocate buffer for the reading
            self.memory.allocate_sensor_buffer()

            # --- PROCESSING PHASE ---
            self.cpu.schedule_task("processing")
            active_operations.append("processing")

            new_reading = reading
        else:
            # Idle tick
            active_operations.append("idle")

        # Advance all component models
        self.cpu.tick(time_step_s)
        self.memory.tick(time_step_s)
        self.battery.tick(active_operations, time_step_s)
        self.network.tick(time_step_s)

        # Check battery warnings
        battery_warnings = self.battery.check_warnings()

        return {
            "tick": self.tick_count,
            "is_active": self.is_active,
            "new_reading": new_reading,
            "is_sensing_tick": is_sensing_tick,
            "battery_warnings": battery_warnings,
            "state": self.get_full_state(),
        }

    def transmit_data(self, payload_bytes: int) -> dict:
        """
        Transmit data over the network. Consumes CPU, battery, and bandwidth.
        
        Args:
            payload_bytes: Size of payload in bytes
            
        Returns:
            Transmission result dict
        """
        if not self.is_active:
            return {"success": False, "reason": "device_inactive"}

        # CPU cost for transmission
        self.cpu.schedule_task("transmission")

        # Battery cost for transmission
        # Transmission duration based on bandwidth
        max_bytes_per_sec = self.network.max_bandwidth_kbps * 1000 / 8
        tx_duration_s = payload_bytes / max_bytes_per_sec if max_bytes_per_sec > 0 else 1.0
        self.battery.consume("transmission", tx_duration_s)

        # Network transmission
        result = self.network.transmit(payload_bytes)

        # Free buffers on successful transmission
        if result["success"]:
            self.memory.free_sensor_buffers()

        return result

    def get_full_state(self) -> dict:
        """Return complete device state snapshot."""
        return {
            "cpu": self.cpu.get_state(),
            "memory": self.memory.get_state(),
            "battery": self.battery.get_state(),
            "network": self.network.get_state(),
            "sensors": {
                "last_reading": self.last_reading,
                "total_readings": self.total_readings,
                "anomaly_count": self.sensors.total_anomalies,
            },
            "is_active": self.is_active,
            "tick": self.tick_count,
        }

    def _get_inactive_state(self) -> dict:
        """Return state for an inactive/depleted device."""
        return {
            "tick": self.tick_count,
            "is_active": False,
            "new_reading": None,
            "is_sensing_tick": False,
            "battery_warnings": [],
            "state": self.get_full_state(),
        }

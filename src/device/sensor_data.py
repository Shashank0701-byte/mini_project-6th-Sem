"""
Sensor Data Generator — Simulates temperature, humidity, and light sensor readings.

Generates realistic sensor data with configurable noise, anomaly injection,
and day/night cycles for the light sensor.
"""

import numpy as np


class SensorDataGenerator:
    """Generates simulated sensor readings with noise and anomalies."""

    def __init__(self, config: dict):
        self.sensor_config = config["sensors"]
        self.temp_config = self.sensor_config["temperature"]
        self.humid_config = self.sensor_config["humidity"]
        self.light_config = self.sensor_config["light"]

        # Track anomalies
        self.total_anomalies = 0
        self.anomaly_log = []

    def generate_reading(self, tick: int, time_step_s: float = 1.0) -> dict:
        """
        Generate sensor readings for the current tick.
        
        Args:
            tick: Current simulation tick
            time_step_s: Time step in seconds
            
        Returns:
            dict with temperature, humidity, light, and anomaly flags
        """
        temp = self._generate_temperature(tick)
        humidity = self._generate_humidity(tick)
        light = self._generate_light(tick, time_step_s)

        reading = {
            "temperature": round(temp["value"], 2),
            "humidity": round(humidity["value"], 2),
            "light": round(light["value"], 1),
            "anomalies": [],
        }

        if temp["is_anomaly"]:
            reading["anomalies"].append("temperature")
            self.total_anomalies += 1
            self.anomaly_log.append({"tick": tick, "sensor": "temperature", "value": temp["value"]})

        if humidity["is_anomaly"]:
            reading["anomalies"].append("humidity")
            self.total_anomalies += 1
            self.anomaly_log.append({"tick": tick, "sensor": "humidity", "value": humidity["value"]})

        return reading

    def _generate_temperature(self, tick: int) -> dict:
        """Generate temperature reading with optional anomaly."""
        base = self.temp_config["base_value"]
        noise = np.random.normal(0, self.temp_config["noise_std_dev"])
        
        # Slight drift over time (simulates environment warming/cooling)
        time_hours = tick / 3600.0
        drift = 2.0 * np.sin(2 * np.pi * time_hours / 24)  # Daily temp cycle

        is_anomaly = np.random.random() < self.temp_config["anomaly_probability"]
        if is_anomaly:
            spike_range = self.temp_config["anomaly_spike_range"]
            spike = np.random.uniform(spike_range[0], spike_range[1])
            spike *= np.random.choice([-1, 1])
            return {"value": base + drift + spike, "is_anomaly": True}

        return {"value": base + drift + noise, "is_anomaly": False}

    def _generate_humidity(self, tick: int) -> dict:
        """Generate humidity reading with optional anomaly."""
        base = self.humid_config["base_value"]
        noise = np.random.normal(0, self.humid_config["noise_std_dev"])

        is_anomaly = np.random.random() < self.humid_config["anomaly_probability"]
        if is_anomaly:
            spike_range = self.humid_config["anomaly_spike_range"]
            spike = np.random.uniform(spike_range[0], spike_range[1])
            spike *= np.random.choice([-1, 1])
            value = max(0, min(100, base + spike))  # Clamp 0-100%
            return {"value": value, "is_anomaly": True}

        value = max(0, min(100, base + noise))
        return {"value": value, "is_anomaly": False}

    def _generate_light(self, tick: int, time_step_s: float) -> dict:
        """Generate light reading with day/night cycle."""
        time_hours = tick * time_step_s / 3600.0
        cycle = self.light_config["cycle_period_hours"]
        day_val = self.light_config["day_value"]
        night_val = self.light_config["night_value"]

        # Sinusoidal day/night cycle
        # Peak at noon (6 hours offset), minimum at midnight
        phase = (time_hours % cycle) / cycle * 2 * np.pi
        # Shift so that t=0 is 6 AM (sunrise ramp)
        sine_val = np.sin(phase - np.pi / 2)
        # Map [-1, 1] to [night_val, day_val]
        normalized = (sine_val + 1) / 2
        base_light = night_val + (day_val - night_val) * normalized

        # No negative light
        noise = np.random.normal(0, self.light_config["noise_std_dev"])
        value = max(0, base_light + noise)

        return {"value": value, "is_anomaly": False}

    def get_state(self) -> dict:
        """Return sensor generator state."""
        return {
            "total_anomalies": self.total_anomalies,
            "anomaly_log": self.anomaly_log[-10:],  # Last 10 anomalies
        }

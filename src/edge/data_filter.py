"""
Data Filter — Removes noise and outliers from sensor readings at the edge.

Uses a sliding window moving average to smooth sensor data.
"""

from collections import deque


class DataFilter:
    """Filters sensor data using a sliding window for noise removal."""

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.windows = {}  # sensor_name -> deque of recent values

    def filter_reading(self, reading: dict) -> dict:
        """
        Apply moving average filter to numeric sensor values.
        
        Args:
            reading: Raw sensor reading dict
            
        Returns:
            Filtered reading dict
        """
        filtered = dict(reading)

        for key in ["temperature", "humidity", "light"]:
            if key not in reading:
                continue

            value = reading[key]

            if key not in self.windows:
                self.windows[key] = deque(maxlen=self.window_size)

            self.windows[key].append(value)

            # Apply moving average
            if len(self.windows[key]) >= 2:
                avg = sum(self.windows[key]) / len(self.windows[key])
                filtered[key] = round(avg, 2)

        return filtered

    def is_outlier(self, sensor_name: str, value: float, sigma: float = 3.0) -> bool:
        """Check if a value is an outlier based on the sliding window."""
        if sensor_name not in self.windows or len(self.windows[sensor_name]) < 3:
            return False

        values = list(self.windows[sensor_name])
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return False

        return abs(value - mean) > sigma * std_dev

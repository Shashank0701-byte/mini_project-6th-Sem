"""
Memory Model — Simulates RAM usage on a resource-constrained device.

Models a fixed-size RAM pool with allocation/deallocation for sensor buffers,
task working memory, and optional memory leak simulation.
"""


class MemoryModel:
    """Simulates RAM allocation and deallocation for a constrained device."""

    def __init__(self, config: dict):
        mem_config = config["device"]["memory"]
        self.total_ram_kb = mem_config["total_ram_kb"]
        self.base_usage_kb = mem_config["base_usage_kb"]
        self.per_reading_buffer_kb = mem_config["per_reading_buffer_kb"]
        self.max_buffer_readings = mem_config["max_buffer_readings"]
        self.leak_enabled = mem_config.get("leak_enabled", False)
        self.leak_rate_kb_per_minute = mem_config.get("leak_rate_kb_per_minute", 0.0)

        # State
        self.current_usage_kb = self.base_usage_kb
        self.buffer_count = 0
        self.leaked_kb = 0.0
        self.peak_usage_kb = self.base_usage_kb
        self.oom_events = 0
        self.usage_history = []

    def allocate_sensor_buffer(self):
        """Allocate memory for one sensor reading buffer."""
        if self.buffer_count < self.max_buffer_readings:
            self.buffer_count += 1
            self._update_usage()

    def free_sensor_buffers(self, count: int = None):
        """Free sensor reading buffers (e.g., after transmission)."""
        if count is None:
            count = self.buffer_count
        self.buffer_count = max(0, self.buffer_count - count)
        self._update_usage()

    def tick(self, time_step_s: float = 1.0):
        """Advance memory state by one tick. Applies leak if enabled."""
        if self.leak_enabled and self.leak_rate_kb_per_minute > 0:
            leak_this_tick = self.leak_rate_kb_per_minute * (time_step_s / 60.0)
            self.leaked_kb += leak_this_tick

        self._update_usage()
        self.usage_history.append(self.current_usage_kb)

        return self.current_usage_kb

    def _update_usage(self):
        """Recalculate current memory usage."""
        buffer_usage = self.buffer_count * self.per_reading_buffer_kb
        self.current_usage_kb = self.base_usage_kb + buffer_usage + self.leaked_kb

        # Cap at total RAM
        if self.current_usage_kb >= self.total_ram_kb:
            self.current_usage_kb = self.total_ram_kb
            self.oom_events += 1

        if self.current_usage_kb > self.peak_usage_kb:
            self.peak_usage_kb = self.current_usage_kb

    def get_utilization(self) -> float:
        """Return memory utilization as a fraction (0.0 to 1.0)."""
        return self.current_usage_kb / self.total_ram_kb

    def get_available_kb(self) -> float:
        """Return available memory in KB."""
        return max(0, self.total_ram_kb - self.current_usage_kb)

    def get_state(self) -> dict:
        """Return current memory state."""
        return {
            "used_kb": round(self.current_usage_kb, 2),
            "total_kb": self.total_ram_kb,
            "utilization": round(self.get_utilization(), 4),
            "buffer_count": self.buffer_count,
            "leaked_kb": round(self.leaked_kb, 2),
            "peak_usage_kb": round(self.peak_usage_kb, 2),
            "oom_events": self.oom_events,
        }

    def get_avg_utilization(self) -> float:
        """Return average memory utilization across all ticks."""
        if not self.usage_history:
            return 0.0
        avg_usage = sum(self.usage_history) / len(self.usage_history)
        return avg_usage / self.total_ram_kb

    def is_leak_detected(self, window_size: int = 300) -> bool:
        """Detect memory leak by checking for monotonic increase over a window."""
        if len(self.usage_history) < window_size:
            return False
        window = self.usage_history[-window_size:]
        # Check if memory is consistently increasing
        increases = sum(1 for i in range(1, len(window)) if window[i] > window[i - 1])
        return increases / (len(window) - 1) > 0.85

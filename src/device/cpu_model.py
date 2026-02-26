"""
CPU Model — Simulates processor utilization on a resource-constrained device.

Models an ARM Cortex-M4 class processor with limited clock cycles.
Tasks consume CPU cycles, and utilization is tracked as a percentage.
"""

import numpy as np


class CPUModel:
    """Simulates CPU utilization for a constrained embedded processor."""

    def __init__(self, config: dict):
        proc_config = config["device"]["processor"]
        self.clock_mhz = proc_config["clock_mhz"]
        self.max_cycles_per_tick = self.clock_mhz * 1_000_000  # cycles per second
        self.task_costs = proc_config["task_costs"]

        # State
        self.current_utilization = 0.0
        self.cycles_used_this_tick = 0
        self.task_queue = []
        self.total_cycles_used = 0
        self.peak_utilization = 0.0
        self.overload_events = 0
        self.consecutive_overload_ticks = 0
        self.utilization_history = []

    def schedule_task(self, task_type: str):
        """Add a task to the CPU queue for this tick."""
        cost = self.task_costs.get(f"{task_type}_cycles", 0)
        self.task_queue.append((task_type, cost))

    def tick(self, time_step_s: float = 1.0):
        """Process all queued tasks for this tick and update utilization."""
        self.cycles_used_this_tick = 0

        for task_type, cost in self.task_queue:
            self.cycles_used_this_tick += cost

        # Scale cycles by time step
        available_cycles = self.max_cycles_per_tick * time_step_s
        self.current_utilization = min(
            self.cycles_used_this_tick / available_cycles, 1.0
        ) if available_cycles > 0 else 0.0

        # Add some realistic jitter
        jitter = np.random.normal(0, 0.02)
        self.current_utilization = max(0.0, min(1.0, self.current_utilization + jitter))

        # Track stats
        self.total_cycles_used += self.cycles_used_this_tick
        if self.current_utilization > self.peak_utilization:
            self.peak_utilization = self.current_utilization

        if self.current_utilization > 0.90:
            self.consecutive_overload_ticks += 1
        else:
            self.consecutive_overload_ticks = 0

        if self.current_utilization > 0.95:
            self.overload_events += 1

        self.utilization_history.append(self.current_utilization)

        # Clear queue
        self.task_queue.clear()

        return self.current_utilization

    def get_state(self) -> dict:
        """Return current CPU state."""
        return {
            "utilization": round(self.current_utilization, 4),
            "cycles_used": self.cycles_used_this_tick,
            "peak_utilization": round(self.peak_utilization, 4),
            "overload_events": self.overload_events,
            "consecutive_overload_ticks": self.consecutive_overload_ticks,
        }

    def get_avg_utilization(self) -> float:
        """Return average utilization across all ticks."""
        if not self.utilization_history:
            return 0.0
        return sum(self.utilization_history) / len(self.utilization_history)

"""
Battery Model — Simulates energy consumption and drain on a battery-powered device.

Models a Li-Po battery with different current draws for each operation type
(sensing, processing, transmission, idle). Tracks energy breakdown by component.
"""


class BatteryModel:
    """Simulates battery drain for a constrained IoT device."""

    def __init__(self, config: dict):
        bat_config = config["device"]["battery"]
        self.capacity_mah = bat_config["capacity_mah"]
        self.voltage = bat_config["voltage"]
        self.current_draw_ma = bat_config["current_draw_ma"]
        self.warning_thresholds = sorted(bat_config["warning_thresholds"], reverse=True)

        # State
        self.remaining_mah = self.capacity_mah
        self.total_consumed_mah = 0.0
        self.energy_breakdown = {
            "sensing": 0.0,
            "processing": 0.0,
            "transmission": 0.0,
            "idle": 0.0,
        }
        self.warnings_triggered = set()
        self.depleted = False
        self.drain_history = []  # (tick, remaining_mah)

    def consume(self, operation: str, duration_s: float = 1.0):
        """
        Consume energy for a given operation.
        
        Args:
            operation: One of 'sensing', 'processing', 'transmission', 'idle'
            duration_s: Duration of the operation in seconds
        """
        if self.depleted:
            return

        current_ma = self.current_draw_ma.get(operation, 0.0)
        # mAh = mA * hours = mA * (seconds / 3600)
        consumed_mah = current_ma * (duration_s / 3600.0)

        self.remaining_mah = max(0.0, self.remaining_mah - consumed_mah)
        self.total_consumed_mah += consumed_mah
        self.energy_breakdown[operation] = self.energy_breakdown.get(operation, 0.0) + consumed_mah

        if self.remaining_mah <= 0:
            self.depleted = True

    def tick(self, active_operations: list = None, time_step_s: float = 1.0):
        """
        Advance battery state by one tick.
        
        Args:
            active_operations: List of operations active during this tick
            time_step_s: Duration of this tick in seconds
        """
        if self.depleted:
            self.drain_history.append(self.remaining_mah)
            return self.remaining_mah

        if active_operations:
            for op in active_operations:
                self.consume(op, time_step_s)
        else:
            self.consume("idle", time_step_s)

        self.drain_history.append(self.remaining_mah)
        return self.remaining_mah

    def get_percentage(self) -> float:
        """Return remaining battery as percentage."""
        return (self.remaining_mah / self.capacity_mah) * 100.0

    def check_warnings(self) -> list:
        """Check if any warning thresholds have been crossed. Returns new warnings."""
        new_warnings = []
        current_pct = self.remaining_mah / self.capacity_mah

        for threshold in self.warning_thresholds:
            if current_pct <= threshold and threshold not in self.warnings_triggered:
                self.warnings_triggered.add(threshold)
                new_warnings.append(threshold)

        return new_warnings

    def estimate_remaining_hours(self) -> float:
        """Estimate remaining battery life based on recent drain rate."""
        if len(self.drain_history) < 60:  # Need at least 60 ticks
            if self.total_consumed_mah > 0:
                ticks = len(self.drain_history) or 1
                drain_per_tick = self.total_consumed_mah / ticks
                if drain_per_tick > 0:
                    ticks_remaining = self.remaining_mah / drain_per_tick
                    return ticks_remaining / 3600.0  # Convert ticks (seconds) to hours
            return float("inf")

        # Use last 60 ticks to estimate drain rate
        recent = self.drain_history[-60:]
        drain_in_window = recent[0] - recent[-1]
        if drain_in_window <= 0:
            return float("inf")

        # drain_in_window mAh consumed in 60 seconds
        drain_per_second = drain_in_window / 60.0
        seconds_remaining = self.remaining_mah / drain_per_second
        return seconds_remaining / 3600.0

    def get_energy_breakdown_pct(self) -> dict:
        """Return energy breakdown as percentages."""
        total = self.total_consumed_mah
        if total == 0:
            return {k: 0.0 for k in self.energy_breakdown}
        return {k: round((v / total) * 100, 1) for k, v in self.energy_breakdown.items()}

    def get_state(self) -> dict:
        """Return current battery state."""
        return {
            "remaining_mah": round(self.remaining_mah, 2),
            "capacity_mah": self.capacity_mah,
            "percentage": round(self.get_percentage(), 2),
            "total_consumed_mah": round(self.total_consumed_mah, 2),
            "depleted": self.depleted,
            "energy_breakdown_mah": {
                k: round(v, 3) for k, v in self.energy_breakdown.items()
            },
            "energy_breakdown_pct": self.get_energy_breakdown_pct(),
        }

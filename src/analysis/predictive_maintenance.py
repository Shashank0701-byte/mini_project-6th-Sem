"""
Predictive Maintenance — Predicts resource exhaustion and maintenance windows.

Uses linear regression on recent resource consumption trends to predict
when battery will deplete, memory will fill up, and when maintenance is needed.
"""

import numpy as np


class PredictiveMaintenance:
    """Predicts resource exhaustion times using trend analysis."""

    def __init__(self, config: dict):
        self.config = config
        self.battery_history = []      # (tick, remaining_mah)
        self.memory_history = []       # (tick, used_kb)
        self.prediction_window = 300   # Use last 5 minutes of data for regression

    def update(self, tick: int, device_state: dict):
        """
        Feed new device state data for trend analysis.
        
        Args:
            tick: Current simulation tick
            device_state: Full device state snapshot
        """
        bat = device_state.get("battery", {})
        mem = device_state.get("memory", {})

        if "remaining_mah" in bat:
            self.battery_history.append((tick, bat["remaining_mah"]))
        if "used_kb" in mem:
            self.memory_history.append((tick, mem["used_kb"]))

        # Keep only recent history for efficiency
        max_history = self.prediction_window * 2
        if len(self.battery_history) > max_history:
            self.battery_history = self.battery_history[-max_history:]
        if len(self.memory_history) > max_history:
            self.memory_history = self.memory_history[-max_history:]

    def predict_battery_depletion(self) -> dict:
        """
        Predict when the battery will be depleted.
        
        Returns:
            dict with 'eta_hours', 'eta_ticks', 'confidence', 'drain_rate_mah_per_hour'
        """
        if len(self.battery_history) < 60:
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "drain_rate_mah_per_hour": 0}

        # Use recent data for linear regression
        window = self.battery_history[-self.prediction_window:]
        ticks = np.array([t for t, _ in window])
        values = np.array([v for _, v in window])

        if len(ticks) < 2:
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "drain_rate_mah_per_hour": 0}

        # Linear regression: value = slope * tick + intercept
        slope, intercept = np.polyfit(ticks, values, 1)

        if slope >= 0:
            # Battery not draining (unlikely but handle it)
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "drain_rate_mah_per_hour": 0}

        # Find tick where value reaches 0
        depletion_tick = -intercept / slope
        current_tick = ticks[-1]
        remaining_ticks = max(0, depletion_tick - current_tick)
        remaining_hours = remaining_ticks / 3600.0

        # Drain rate in mAh per hour
        drain_rate = abs(slope) * 3600  # slope is mAh/tick, * 3600 = mAh/hour

        # Confidence based on R² of the fit
        predicted = slope * ticks + intercept
        ss_res = np.sum((values - predicted) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        confidence = "high" if r_squared > 0.95 else "medium" if r_squared > 0.8 else "low"

        return {
            "eta_hours": round(remaining_hours, 2),
            "eta_ticks": int(remaining_ticks),
            "confidence": confidence,
            "drain_rate_mah_per_hour": round(drain_rate, 2),
            "r_squared": round(r_squared, 4),
        }

    def predict_memory_exhaustion(self) -> dict:
        """
        Predict when memory will be full (if a leak is present).
        
        Returns:
            dict with 'eta_hours', 'eta_ticks', 'confidence', 'leak_rate_kb_per_hour'
        """
        total_kb = self.config["device"]["memory"]["total_ram_kb"]

        if len(self.memory_history) < 60:
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "leak_rate_kb_per_hour": 0}

        window = self.memory_history[-self.prediction_window:]
        ticks = np.array([t for t, _ in window])
        values = np.array([v for _, v in window])

        if len(ticks) < 2:
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "leak_rate_kb_per_hour": 0}

        slope, intercept = np.polyfit(ticks, values, 1)

        if slope <= 0:
            # Memory not growing
            return {"eta_hours": float("inf"), "eta_ticks": float("inf"),
                    "confidence": "low", "leak_rate_kb_per_hour": 0}

        # Find tick where usage reaches total_kb
        full_tick = (total_kb - intercept) / slope
        current_tick = ticks[-1]
        remaining_ticks = max(0, full_tick - current_tick)
        remaining_hours = remaining_ticks / 3600.0

        leak_rate = slope * 3600  # KB per hour

        # Confidence
        predicted = slope * ticks + intercept
        ss_res = np.sum((values - predicted) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        confidence = "high" if r_squared > 0.9 else "medium" if r_squared > 0.7 else "low"

        return {
            "eta_hours": round(remaining_hours, 2),
            "eta_ticks": int(remaining_ticks),
            "confidence": confidence,
            "leak_rate_kb_per_hour": round(leak_rate, 2),
            "r_squared": round(r_squared, 4),
        }

    def get_maintenance_recommendation(self) -> dict:
        """
        Recommend a maintenance window based on predictions.
        """
        bat_pred = self.predict_battery_depletion()
        mem_pred = self.predict_memory_exhaustion()

        # Maintenance should happen before the earliest critical event
        earliest_hours = min(
            bat_pred["eta_hours"] if bat_pred["eta_hours"] != float("inf") else 9999,
            mem_pred["eta_hours"] if mem_pred["eta_hours"] != float("inf") else 9999,
        )

        if earliest_hours >= 9999:
            return {
                "recommended": False,
                "reason": "No resource exhaustion predicted in the near future",
                "eta_hours": None,
            }

        # Recommend maintenance at 70% of time to failure
        maintenance_hours = earliest_hours * 0.7

        return {
            "recommended": True,
            "maintenance_in_hours": round(maintenance_hours, 2),
            "reason_battery_eta": bat_pred["eta_hours"],
            "reason_memory_eta": mem_pred["eta_hours"],
        }

    def get_predictions(self) -> dict:
        """Return all predictions."""
        return {
            "battery_depletion": self.predict_battery_depletion(),
            "memory_exhaustion": self.predict_memory_exhaustion(),
            "maintenance": self.get_maintenance_recommendation(),
        }

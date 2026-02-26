"""
What-If Analysis Engine — Compares base scenario with modified configurations.

Runs a second simulation with different parameters and presents
a side-by-side comparison of key metrics.
"""


class WhatIfAnalyzer:
    """Compares simulation results between different configurations."""

    def __init__(self):
        self.base_results = None
        self.whatif_results = None

    def set_base_results(self, results: dict):
        """Store the base scenario results."""
        self.base_results = results

    def set_whatif_results(self, results: dict):
        """Store the what-if scenario results."""
        self.whatif_results = results

    def compare(self) -> dict:
        """
        Generate a comparison between base and what-if scenarios.
        
        Returns:
            dict with per-metric comparisons and improvement percentages
        """
        if not self.base_results or not self.whatif_results:
            return {"error": "Both base and what-if results are required"}

        comparisons = {}

        # Compare key metrics
        metrics = [
            ("sync_strategy", "Sync Strategy", False),
            ("total_syncs", "Total Syncs Performed", True),
            ("total_energy_consumed_mah", "Total Energy Consumed (mAh)", True),
            ("battery_remaining_pct", "Battery Remaining (%)", True),
            ("estimated_battery_life_hours", "Estimated Battery Life (hours)", True),
            ("total_bandwidth_bytes", "Total Bandwidth Used (bytes)", True),
            ("twin_avg_accuracy_pct", "Twin Avg Accuracy (%)", True),
            ("faults_detected", "Faults Detected", False),
            ("critical_alerts", "Critical Alerts", True),
            ("warning_alerts", "Warning Alerts", True),
            ("avg_sync_payload_bytes", "Avg Sync Payload (bytes)", True),
            ("data_packets_sent", "Data Packets Sent", True),
        ]

        for key, label, is_numeric in metrics:
            base_val = self.base_results.get(key, "N/A")
            whatif_val = self.whatif_results.get(key, "N/A")

            entry = {
                "label": label,
                "base": base_val,
                "whatif": whatif_val,
            }

            if is_numeric and isinstance(base_val, (int, float)) and isinstance(whatif_val, (int, float)):
                if base_val != 0:
                    change_pct = ((whatif_val - base_val) / abs(base_val)) * 100
                    entry["change_pct"] = round(change_pct, 1)
                    entry["change_direction"] = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "─"
                else:
                    entry["change_pct"] = 0
                    entry["change_direction"] = "─"

            comparisons[key] = entry

        # Compute computed insights
        insights = self._generate_insights(comparisons)

        return {
            "comparisons": comparisons,
            "insights": insights,
        }

    def _generate_insights(self, comparisons: dict) -> list:
        """Generate human-readable insights from the comparison."""
        insights = []

        energy = comparisons.get("total_energy_consumed_mah", {})
        if "change_pct" in energy and energy["change_pct"] < -10:
            insights.append(
                f"⚡ Energy savings of {abs(energy['change_pct']):.1f}% "
                f"({energy['base']} → {energy['whatif']} mAh)"
            )

        bw = comparisons.get("total_bandwidth_bytes", {})
        if "change_pct" in bw and bw["change_pct"] < -10:
            insights.append(
                f"📡 Bandwidth reduced by {abs(bw['change_pct']):.1f}% "
                f"({bw['base']} → {bw['whatif']} bytes)"
            )

        accuracy = comparisons.get("twin_avg_accuracy_pct", {})
        if "change_pct" in accuracy and accuracy["change_pct"] < -2:
            insights.append(
                f"⚠️ Twin accuracy decreased by {abs(accuracy['change_pct']):.1f}% — "
                f"trade-off for energy savings"
            )

        battery_life = comparisons.get("estimated_battery_life_hours", {})
        if "change_pct" in battery_life and battery_life["change_pct"] > 10:
            insights.append(
                f"🔋 Battery life extended by {battery_life['change_pct']:.1f}% "
                f"({battery_life['base']:.1f} → {battery_life['whatif']:.1f} hours)"
            )

        if not insights:
            insights.append("No significant differences detected between configurations.")

        return insights

    @staticmethod
    def extract_results(device, twin, sync_engine, fault_detector, edge_processor, predictive) -> dict:
        """
        Extract key metrics from simulation components into a results dict.
        """
        device_state = device.get_full_state()
        twin_state = twin.get_state()
        sync_stats = sync_engine.get_stats()
        fault_summary = fault_detector.get_summary()
        edge_stats = edge_processor.get_stats()
        predictions = predictive.get_predictions()

        bat = device_state["battery"]

        return {
            "sync_strategy": sync_stats["strategy"],
            "total_syncs": sync_stats["total_syncs"],
            "total_energy_consumed_mah": round(bat["total_consumed_mah"], 2),
            "battery_remaining_pct": round(bat["percentage"], 2),
            "estimated_battery_life_hours": round(
                predictions["battery_depletion"].get("eta_hours", 0), 2
            ),
            "total_bandwidth_bytes": sync_stats["total_bytes_synced"],
            "twin_avg_accuracy_pct": round(twin_state["avg_accuracy"] * 100, 2),
            "faults_detected": len(fault_summary["faults_detected"]),
            "critical_alerts": fault_summary["critical_count"],
            "warning_alerts": fault_summary["warning_count"],
            "avg_sync_payload_bytes": round(sync_stats["avg_payload_bytes"], 0),
            "data_packets_sent": device_state["network"]["total_packets_sent"],
            "edge_bytes_saved": edge_stats["bytes_saved_by_compression"],
        }

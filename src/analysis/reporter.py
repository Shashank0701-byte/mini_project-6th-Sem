"""
Reporter — Generates rich terminal summary reports for the simulation.

Outputs a comprehensive report with device stats, resource utilization,
energy breakdown, twin accuracy, fault detection, and predictive maintenance.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box


console = Console()


class Reporter:
    """Generates formatted terminal reports for simulation results."""

    @staticmethod
    def print_summary(device, twin, sync_engine, fault_detector,
                      edge_processor, predictive, duration_hours: float):
        """Print the full simulation summary report."""

        device_state = device.get_full_state()
        twin_state = twin.get_state()
        sync_stats = sync_engine.get_stats()
        fault_summary = fault_detector.get_summary()
        edge_stats = edge_processor.get_stats()
        predictions = predictive.get_predictions()

        bat = device_state["battery"]
        mem = device_state["memory"]
        cpu = device_state["cpu"]
        net = device_state["network"]
        sensors = device_state["sensors"]

        console.print()
        console.print(Panel.fit(
            "[bold cyan]DIGITAL TWIN — SIMULATION SUMMARY REPORT[/bold cyan]",
            border_style="cyan",
            padding=(1, 4),
        ))
        console.print()

        # === DEVICE STATUS ===
        status_table = Table(
            title="📟 DEVICE STATUS",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_blue",
        )
        status_table.add_column("Metric", style="bright_white", min_width=30)
        status_table.add_column("Value", style="bright_green", justify="right", min_width=30)

        total_ticks = device.tick_count
        status_table.add_row("Simulation Duration",
                             f"{duration_hours} hours ({total_ticks:,} ticks @ 1s)")
        status_table.add_row("Sync Strategy", sync_stats["strategy"].upper())
        status_table.add_row("Total Sensor Readings", f"{sensors['total_readings']:,}")
        status_table.add_row("Total Syncs Performed", f"{sync_stats['total_syncs']:,}")
        status_table.add_row("Device Active", "✅ Yes" if device.is_active else "❌ No (depleted)")

        console.print(status_table)
        console.print()

        # === RESOURCE UTILIZATION ===
        res_table = Table(
            title="📊 RESOURCE UTILIZATION",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_magenta",
        )
        res_table.add_column("Resource", style="bright_white", min_width=12)
        res_table.add_column("Average", justify="right", min_width=12)
        res_table.add_column("Peak", justify="right", min_width=12)
        res_table.add_column("Events", justify="right", min_width=15)

        # CPU
        cpu_avg = device.cpu.get_avg_utilization() * 100
        cpu_peak = cpu["peak_utilization"] * 100
        res_table.add_row(
            "CPU",
            f"{cpu_avg:.1f}%",
            f"{cpu_peak:.1f}%",
            f"Overloads: {cpu['overload_events']}",
        )

        # Memory
        mem_avg = device.memory.get_avg_utilization() * 100
        mem_peak = (mem["peak_usage_kb"] / mem["total_kb"]) * 100
        leak_str = f"Leak: {'Yes' if mem['leaked_kb'] > 0.5 else 'No'}"
        res_table.add_row(
            "RAM",
            f"{mem_avg:.1f}%",
            f"{mem_peak:.1f}% ({mem['peak_usage_kb']:.0f} KB)",
            leak_str,
        )

        # Battery
        res_table.add_row(
            "Battery",
            f"—",
            f"Start: {bat['capacity_mah']} mAh",
            f"End: {bat['remaining_mah']:.1f} mAh ({bat['percentage']:.1f}%)",
        )

        # Network
        net_avg = device.network.get_avg_utilization() * 100
        total_kb = net["total_bytes_sent"] / 1024
        res_table.add_row(
            "Network",
            f"{net_avg:.1f}% BW",
            f"{total_kb:.1f} KB sent",
            f"Loss: {net['packet_loss_rate']*100:.1f}%",
        )

        console.print(res_table)
        console.print()

        # === ENERGY BREAKDOWN ===
        energy_table = Table(
            title="⚡ ENERGY BREAKDOWN",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_yellow",
        )
        energy_table.add_column("Component", style="bright_white", min_width=15)
        energy_table.add_column("mAh", justify="right", min_width=10)
        energy_table.add_column("Percentage", justify="right", min_width=12)
        energy_table.add_column("Bar", min_width=20)

        breakdown = bat["energy_breakdown_mah"]
        breakdown_pct = bat["energy_breakdown_pct"]

        colors = {
            "sensing": "green",
            "processing": "blue",
            "transmission": "red",
            "idle": "dim",
        }

        for component in ["sensing", "processing", "transmission", "idle"]:
            mah_val = breakdown.get(component, 0)
            pct_val = breakdown_pct.get(component, 0)
            bar_length = int(pct_val / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            color = colors.get(component, "white")
            energy_table.add_row(
                component.capitalize(),
                f"{mah_val:.3f}",
                f"{pct_val:.1f}%",
                f"[{color}]{bar}[/{color}]",
            )

        energy_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{bat['total_consumed_mah']:.3f}[/bold]",
            "[bold]100%[/bold]",
            "",
        )

        console.print(energy_table)
        console.print()

        # === DIGITAL TWIN ACCURACY ===
        twin_table = Table(
            title="🔗 DIGITAL TWIN ACCURACY",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_cyan",
        )
        twin_table.add_column("Metric", style="bright_white", min_width=25)
        twin_table.add_column("Value", style="bright_green", justify="right", min_width=25)

        twin_table.add_row("Average State Accuracy",
                           f"{twin_state['avg_accuracy']*100:.1f}%")
        twin_table.add_row("Max State Drift",
                           f"{twin_state['max_drift']*100:.1f}% at tick {twin_state['max_drift_tick']:,}")
        twin_table.add_row("Sync Success Rate",
                           f"{twin_state['sync_success_rate']*100:.1f}%")
        twin_table.add_row("Total Syncs", f"{twin_state['total_syncs']:,}")

        console.print(twin_table)
        console.print()

        # === FAULT DETECTION ===
        fault_table = Table(
            title="🚨 FAULT DETECTION",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_red",
        )
        fault_table.add_column("Metric", style="bright_white", min_width=25)
        fault_table.add_column("Value", justify="right", min_width=25)

        fault_table.add_row("Total Alerts",
                           f"{fault_summary['critical_count']} Critical, {fault_summary['warning_count']} Warnings")
        fault_table.add_row("Faults Detected",
                           f"{len(fault_summary['faults_detected'])}")

        for fault in fault_summary["faults_detected"]:
            fault_table.add_row(f"  → {fault['type']}", f"at tick {fault['tick']:,}")

        console.print(fault_table)
        console.print()

        # === ALERT LOG (last 10) ===
        if fault_summary["last_10_alerts"]:
            alert_table = Table(
                title="📋 RECENT ALERTS",
                box=box.SIMPLE,
                title_style="bold white",
                border_style="dim",
            )
            alert_table.add_column("Time", style="dim", min_width=10)
            alert_table.add_column("", min_width=3)
            alert_table.add_column("Component", min_width=12)
            alert_table.add_column("Message", min_width=40)

            for alert in fault_summary["last_10_alerts"]:
                severity_color = (
                    "red" if alert["severity"] == "CRITICAL"
                    else "yellow" if alert["severity"] == "WARNING"
                    else "bright_magenta"
                )
                alert_table.add_row(
                    alert["time"],
                    alert["icon"],
                    f"[{severity_color}]{alert['component']}[/{severity_color}]",
                    alert["message"],
                )

            console.print(alert_table)
            console.print()

        # === PREDICTIVE MAINTENANCE ===
        pred_table = Table(
            title="🔮 PREDICTIVE MAINTENANCE",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_green",
        )
        pred_table.add_column("Prediction", style="bright_white", min_width=25)
        pred_table.add_column("Value", justify="right", min_width=25)
        pred_table.add_column("Confidence", justify="right", min_width=12)

        bat_pred = predictions["battery_depletion"]
        mem_pred = predictions["memory_exhaustion"]
        maint = predictions["maintenance"]

        eta_bat = (f"{bat_pred['eta_hours']:.1f} hours"
                   if bat_pred["eta_hours"] != float("inf") else "N/A")
        pred_table.add_row("Battery Depletion ETA", eta_bat,
                           bat_pred.get("confidence", "—"))

        eta_mem = (f"{mem_pred['eta_hours']:.1f} hours"
                   if mem_pred["eta_hours"] != float("inf") else "N/A")
        pred_table.add_row("Memory Full ETA", eta_mem,
                           mem_pred.get("confidence", "—"))

        if maint["recommended"]:
            pred_table.add_row(
                "⏱️  Maintenance Recommended In",
                f"{maint['maintenance_in_hours']:.1f} hours",
                "—",
            )
        else:
            pred_table.add_row("Maintenance", "Not required", "—")

        console.print(pred_table)
        console.print()

        # === EDGE PROCESSING ===
        edge_table = Table(
            title="🌐 EDGE PROCESSING",
            box=box.ROUNDED,
            title_style="bold white",
            border_style="bright_white",
        )
        edge_table.add_column("Metric", style="bright_white", min_width=30)
        edge_table.add_column("Value", justify="right", min_width=20)

        edge_table.add_row("Edge Processing", "Enabled" if edge_stats["enabled"] else "Disabled")
        edge_table.add_row("Total Readings Processed", f"{edge_stats['total_processed']:,}")
        edge_table.add_row("Data Reduction Ratio",
                           f"{edge_stats['data_reduction_ratio']*100:.1f}%")
        edge_table.add_row("Bytes Saved (Compression)",
                           f"{edge_stats['bytes_saved_by_compression']:,}")
        edge_table.add_row("Anomalies Fast-Tracked",
                           f"{edge_stats['anomalies_fast_tracked']}")

        console.print(edge_table)
        console.print()

    @staticmethod
    def print_whatif_comparison(comparison: dict):
        """Print a What-If comparison table."""

        console.print()
        console.print(Panel.fit(
            "[bold yellow]WHAT-IF ANALYSIS — SCENARIO COMPARISON[/bold yellow]",
            border_style="yellow",
            padding=(1, 4),
        ))
        console.print()

        comp_table = Table(
            box=box.ROUNDED,
            border_style="yellow",
        )
        comp_table.add_column("Metric", style="bright_white", min_width=30)
        comp_table.add_column("Base Config", justify="right", min_width=18,
                              style="bright_blue")
        comp_table.add_column("What-If Config", justify="right", min_width=18,
                              style="bright_green")
        comp_table.add_column("Change", justify="right", min_width=15)

        for key, entry in comparison["comparisons"].items():
            change_str = ""
            if "change_pct" in entry:
                pct = entry["change_pct"]
                direction = entry["change_direction"]
                color = "green" if pct < 0 else "red" if pct > 0 else "dim"
                change_str = f"[{color}]{direction} {abs(pct):.1f}%[/{color}]"

            comp_table.add_row(
                entry["label"],
                str(entry["base"]),
                str(entry["whatif"]),
                change_str,
            )

        console.print(comp_table)
        console.print()

        # Print insights
        if comparison.get("insights"):
            console.print(Panel(
                "\n".join(comparison["insights"]),
                title="💡 Insights",
                border_style="bright_yellow",
            ))
            console.print()

    @staticmethod
    def print_live_tick(tick: int, device_state: dict, alerts: list,
                        twin_drift: float,  interval: int = 60):
        """Print a live status line during simulation (every N ticks)."""
        if tick % interval != 0:
            return

        time_str = f"{tick//3600:02d}:{(tick%3600)//60:02d}:{tick%60:02d}"
        cpu = device_state["cpu"]["utilization"] * 100
        mem = device_state["memory"]["utilization"] * 100
        bat = device_state["battery"]["percentage"]
        bw = device_state["network"]["bandwidth_utilization"] * 100

        status = (
            f"[dim][{time_str}][/dim] "
            f"CPU: [{'red' if cpu > 80 else 'green'}]{cpu:5.1f}%[/] │ "
            f"RAM: [{'red' if mem > 80 else 'green'}]{mem:5.1f}%[/] │ "
            f"BAT: [{'red' if bat < 20 else 'green'}]{bat:5.1f}%[/] │ "
            f"BW: [{'red' if bw > 80 else 'green'}]{bw:5.1f}%[/] │ "
            f"Drift: {twin_drift*100:4.1f}%"
        )

        console.print(status)

        # Print any alerts from this tick
        for alert in alerts:
            severity_color = (
                "red" if alert["severity"] == "CRITICAL"
                else "yellow" if alert["severity"] == "WARNING"
                else "bright_magenta"
            )
            console.print(
                f"  {alert['icon']} [{severity_color}]{alert['severity']}[/{severity_color}] "
                f"[{alert['component']}] {alert['message']}"
            )

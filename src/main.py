"""
Main — CLI entry point for the Digital Twin simulation.

Orchestrates the simulation loop, connecting the device simulator,
digital twin, sync engine, edge processor, and analysis modules.

Usage:
    python -m src.main                          # Default config
    python -m src.main --sync-strategy delta     # Use delta sync
    python -m src.main --what-if --sync-strategy delta  # Compare base vs delta
    python -m src.main --duration 2 --sampling-rate 10  # Custom params
"""

import argparse
import json
import copy
import os
import sys
import numpy as np

from .device.sensor_node import SensorNode
from .twin.digital_twin import DigitalTwin
from .sync.sync_engine import SyncEngine
from .edge.edge_processor import EdgeProcessor
from .analysis.fault_detector import FaultDetector
from .analysis.predictive_maintenance import PredictiveMaintenance
from .analysis.reporter import Reporter
from .analysis.what_if import WhatIfAnalyzer
from .utils.logger import SimulationLogger
from .utils.display import (
    print_banner, print_config_summary, create_progress_bar,
    print_simulation_complete, console,
)


def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        # Default config path relative to project root
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "default_config.json"
        )

    with open(config_path, "r") as f:
        return json.load(f)


def apply_cli_overrides(config: dict, args: argparse.Namespace) -> dict:
    """Apply CLI argument overrides to the config."""
    config = copy.deepcopy(config)

    if args.sync_strategy:
        config["sync"]["default_strategy"] = args.sync_strategy
    if args.duration:
        config["simulation"]["duration_hours"] = args.duration
    if args.sampling_rate:
        config["simulation"]["sampling_rate_seconds"] = args.sampling_rate
    if args.battery_capacity:
        config["device"]["battery"]["capacity_mah"] = args.battery_capacity
    if args.ram_size:
        config["device"]["memory"]["total_ram_kb"] = args.ram_size
    if args.bandwidth:
        config["device"]["network"]["max_bandwidth_kbps"] = args.bandwidth
    if args.seed is not None:
        config["simulation"]["random_seed"] = args.seed
    if args.no_edge:
        config["edge"]["enabled"] = False
    if args.no_leak:
        config["device"]["memory"]["leak_enabled"] = False
    if args.log_format:
        config["simulation"]["log_format"] = args.log_format

    return config


def run_simulation(config: dict, verbose: bool = True, label: str = "Simulation") -> dict:
    """
    Run a single simulation with the given config.
    
    Returns:
        dict with all simulation component references and results
    """
    # Set random seed
    np.random.seed(config["simulation"]["random_seed"])

    # Initialize components
    device = SensorNode(config)
    twin = DigitalTwin(config)
    sync_engine = SyncEngine(config, config["sync"]["default_strategy"])
    edge = EdgeProcessor(config)
    fault_detector = FaultDetector(config)
    predictive = PredictiveMaintenance(config)
    logger = SimulationLogger(config)

    duration_hours = config["simulation"]["duration_hours"]
    time_step_s = config["simulation"]["time_step_seconds"]
    total_ticks = int(duration_hours * 3600 / time_step_s)
    sampling_rate = config["simulation"]["sampling_rate_seconds"]

    log_interval = max(1, total_ticks // 20)  # Log ~20 lines during sim

    if verbose:
        progress = create_progress_bar(total_ticks)
        task_id = None

    # === SIMULATION LOOP ===
    if verbose:
        with progress:
            task_id = progress.add_task(f"[cyan]{label}...", total=total_ticks)
            _run_loop(
                device, twin, sync_engine, edge, fault_detector,
                predictive, logger, config, total_ticks, time_step_s,
                sampling_rate, verbose, log_interval, progress, task_id,
            )
    else:
        _run_loop(
            device, twin, sync_engine, edge, fault_detector,
            predictive, logger, config, total_ticks, time_step_s,
            sampling_rate, verbose, log_interval, None, None,
        )

    # Save log
    logger.save()
    log_filepath = logger.get_filepath()

    return {
        "device": device,
        "twin": twin,
        "sync_engine": sync_engine,
        "edge": edge,
        "fault_detector": fault_detector,
        "predictive": predictive,
        "logger": logger,
        "log_filepath": log_filepath,
        "config": config,
        "duration_hours": duration_hours,
    }


def _run_loop(device, twin, sync_engine, edge, fault_detector,
              predictive, logger, config, total_ticks, time_step_s,
              sampling_rate, verbose, log_interval, progress, task_id):
    """Core simulation loop."""

    expected_sync_interval = config["sync"].get("full_state_interval_s", 10)
    alert_dedup_window = 60  # Don't repeat same alert within 60 ticks
    last_alert_ticks = {}

    for tick in range(1, total_ticks + 1):
        # 1. Advance the device
        device_result = device.tick(time_step_s)
        device_state = device.get_full_state()

        # 2. If there's a new sensor reading, process through edge
        if device_result["new_reading"]:
            edge.process(device_result["new_reading"], device_state)

        # 3. Check if sync should occur
        battery_pct = device_state["battery"]["percentage"] / 100.0
        sync_occurred = False

        if sync_engine.should_sync(tick, device_state, battery_pct):
            # Prepare payload
            payload_info = sync_engine.prepare_payload(device_state)

            # Transmit via device network
            tx_result = device.transmit_data(payload_info["size_bytes"])

            if tx_result.get("success", False):
                # Twin receives the sync
                twin.receive_sync(device_state, tick)
                sync_engine.record_sync(tick, payload_info["size_bytes"], True)
                sync_occurred = True
            else:
                twin.record_sync_failure(tick)
                sync_engine.record_sync(tick, payload_info["size_bytes"], False)
        else:
            # Twin predicts/interpolates when no sync
            twin.tick(tick)

        # 4. Fault detection
        twin_state = twin.get_state()
        new_alerts = []
        raw_alerts = fault_detector.check(
            tick, device_state, twin_state,
            twin_state["last_sync_tick"], expected_sync_interval,
            is_sensing_tick=device_result.get("is_sensing_tick", False),
        )

        # Deduplicate alerts (don't repeat same component alert too often)
        for alert in raw_alerts:
            key = f"{alert['component']}_{alert['severity']}"
            if key not in last_alert_ticks or (tick - last_alert_ticks[key]) >= alert_dedup_window:
                new_alerts.append(alert)
                last_alert_ticks[key] = tick

        # 5. Predictive maintenance (update every 10 ticks)
        if tick % 10 == 0:
            predictive.update(tick, device_state)

        # 6. Log tick data (every N ticks to keep file manageable)
        if tick % max(1, sampling_rate) == 0:
            logger.log_tick(tick, device_state, twin_state, new_alerts, sync_occurred)

        # 7. Live output
        if verbose and new_alerts:
            for alert in new_alerts:
                Reporter.print_live_tick(tick, device_state, [alert], twin.current_drift, 1)

        # Update progress
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

        # Stop if device is depleted
        if not device.is_active:
            if verbose:
                console.print("[bold red]⚡ Device battery depleted — simulation stopped.[/bold red]")
            break


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Digital Twin — Resource-Constrained IoT System Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                                  # Default config (adaptive sync, 6h)
  python -m src.main --sync-strategy delta             # Use delta sync
  python -m src.main --sync-strategy full_state        # Use full-state sync
  python -m src.main --duration 2 --sampling-rate 10   # 2 hour sim, sample every 10s
  python -m src.main --what-if --sync-strategy delta   # Compare base vs. delta
  python -m src.main --battery-capacity 500            # Smaller battery
  python -m src.main --no-edge                         # Disable edge processing
        """,
    )

    parser.add_argument("--config", type=str, default=None,
                        help="Path to config JSON file")
    parser.add_argument("--sync-strategy", type=str, default=None,
                        choices=["full_state", "delta", "event_driven", "adaptive"],
                        help="Sync strategy to use")
    parser.add_argument("--duration", type=float, default=None,
                        help="Simulation duration in hours")
    parser.add_argument("--sampling-rate", type=int, default=None,
                        help="Sensor sampling rate in seconds")
    parser.add_argument("--battery-capacity", type=int, default=None,
                        help="Battery capacity in mAh")
    parser.add_argument("--ram-size", type=int, default=None,
                        help="RAM size in KB")
    parser.add_argument("--bandwidth", type=int, default=None,
                        help="Network bandwidth in kbps")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--no-edge", action="store_true",
                        help="Disable edge processing")
    parser.add_argument("--no-leak", action="store_true",
                        help="Disable memory leak simulation")
    parser.add_argument("--log-format", type=str, default=None,
                        choices=["json", "csv"],
                        help="Log output format")
    parser.add_argument("--what-if", action="store_true",
                        help="Run What-If comparison (base config vs. CLI overrides)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress live output during simulation")

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Load config
    base_config = load_config(args.config)

    if args.what_if:
        # === WHAT-IF MODE ===
        # In what-if mode, shared params (duration, sampling, battery, etc.) 
        # apply to BOTH scenarios. Only sync strategy / edge / leak differ.
        shared_config = copy.deepcopy(base_config)
        if args.duration:
            shared_config["simulation"]["duration_hours"] = args.duration
        if args.sampling_rate:
            shared_config["simulation"]["sampling_rate_seconds"] = args.sampling_rate
        if args.battery_capacity:
            shared_config["device"]["battery"]["capacity_mah"] = args.battery_capacity
        if args.ram_size:
            shared_config["device"]["memory"]["total_ram_kb"] = args.ram_size
        if args.bandwidth:
            shared_config["device"]["network"]["max_bandwidth_kbps"] = args.bandwidth
        if args.seed is not None:
            shared_config["simulation"]["random_seed"] = args.seed
        if args.log_format:
            shared_config["simulation"]["log_format"] = args.log_format

        # What-if config gets the strategy/edge/leak overrides
        whatif_config = copy.deepcopy(shared_config)
        if args.sync_strategy:
            whatif_config["sync"]["default_strategy"] = args.sync_strategy
        if args.no_edge:
            whatif_config["edge"]["enabled"] = False
        if args.no_leak:
            whatif_config["device"]["memory"]["leak_enabled"] = False

        # Run base simulation
        console.print("[bold cyan]═══ Running BASE scenario... ═══[/bold cyan]\n")
        print_config_summary(shared_config)
        base_result = run_simulation(shared_config, verbose=not args.quiet, label="Base Scenario")

        # Run what-if simulation
        console.print("\n[bold yellow]═══ Running WHAT-IF scenario... ═══[/bold yellow]\n")
        print_config_summary(whatif_config)
        whatif_result = run_simulation(whatif_config, verbose=not args.quiet, label="What-If Scenario")

        # Compare
        analyzer = WhatIfAnalyzer()
        analyzer.set_base_results(WhatIfAnalyzer.extract_results(
            base_result["device"], base_result["twin"], base_result["sync_engine"],
            base_result["fault_detector"], base_result["edge"], base_result["predictive"],
        ))
        analyzer.set_whatif_results(WhatIfAnalyzer.extract_results(
            whatif_result["device"], whatif_result["twin"], whatif_result["sync_engine"],
            whatif_result["fault_detector"], whatif_result["edge"], whatif_result["predictive"],
        ))

        comparison = analyzer.compare()

        # Print reports
        console.print("\n[bold cyan]═══ BASE SCENARIO REPORT ═══[/bold cyan]")
        Reporter.print_summary(
            base_result["device"], base_result["twin"], base_result["sync_engine"],
            base_result["fault_detector"], base_result["edge"], base_result["predictive"],
            base_result["duration_hours"],
        )

        console.print("\n[bold yellow]═══ WHAT-IF SCENARIO REPORT ═══[/bold yellow]")
        Reporter.print_summary(
            whatif_result["device"], whatif_result["twin"], whatif_result["sync_engine"],
            whatif_result["fault_detector"], whatif_result["edge"], whatif_result["predictive"],
            whatif_result["duration_hours"],
        )

        Reporter.print_whatif_comparison(comparison)

        print_simulation_complete(base_result["log_filepath"])

    else:
        # === SINGLE SIMULATION MODE ===
        config = apply_cli_overrides(base_config, args)
        print_config_summary(config)

        result = run_simulation(config, verbose=not args.quiet)

        # Print summary report
        Reporter.print_summary(
            result["device"], result["twin"], result["sync_engine"],
            result["fault_detector"], result["edge"], result["predictive"],
            result["duration_hours"],
        )

        print_simulation_complete(result["log_filepath"])


if __name__ == "__main__":
    main()

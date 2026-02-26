"""
Fault Detector — Real-time bottleneck and fault detection engine.

Monitors CPU, memory, battery, network, and sensors for anomalies,
overloads, leaks, and communication failures.
"""

from collections import deque


class FaultDetector:
    """Detects faults, bottlenecks, and anomalies in the device state."""

    def __init__(self, config: dict):
        fd_config = config["fault_detection"]

        # CPU thresholds
        self.cpu_critical = fd_config["cpu_critical_threshold"]
        self.cpu_critical_duration = fd_config["cpu_critical_duration_s"]
        self.cpu_warning = fd_config["cpu_warning_threshold"]
        self.cpu_warning_duration = fd_config["cpu_warning_duration_s"]

        # Memory thresholds
        self.mem_critical = fd_config["memory_critical_threshold"]
        self.mem_warning = fd_config["memory_warning_threshold"]

        # Battery thresholds
        self.bat_critical = fd_config["battery_critical_threshold"]
        self.bat_warning = fd_config["battery_warning_threshold"]

        # Network thresholds
        self.bw_warning = fd_config["bandwidth_warning_threshold"]
        self.pkt_loss_critical = fd_config["packet_loss_critical_threshold"]

        # Twin thresholds
        self.drift_warning = fd_config["state_drift_warning_threshold"]

        # Leak detection
        self.leak_window = fd_config["memory_leak_detection_window_s"]

        # Communication timeout
        self.comm_timeout_mult = fd_config["communication_timeout_multiplier"]

        # Sensor anomaly
        self.sensor_sigma = fd_config["sensor_anomaly_sigma"]

        # Tracking state
        self.cpu_high_ticks = 0
        self.cpu_warning_ticks = 0
        self.alerts = []  # All alerts generated
        self.critical_count = 0
        self.warning_count = 0
        self.faults_detected = []

    def check(self, tick: int, device_state: dict, twin_state: dict = None,
              last_sync_tick: int = 0, expected_sync_interval: int = 10,
              is_sensing_tick: bool = False) -> list:
        """
        Run all fault detection checks for this tick.
        
        Returns:
            List of alert dicts generated this tick
        """
        new_alerts = []

        cpu_state = device_state.get("cpu", {})
        mem_state = device_state.get("memory", {})
        bat_state = device_state.get("battery", {})
        net_state = device_state.get("network", {})
        sensors = device_state.get("sensors", {})

        # --- CPU CHECKS ---
        cpu_util = cpu_state.get("utilization", 0)

        if cpu_util > self.cpu_critical:
            self.cpu_high_ticks += 1
            if self.cpu_high_ticks >= self.cpu_critical_duration:
                alert = self._create_alert(tick, "CRITICAL", "CPU",
                    f"CPU utilization > {self.cpu_critical*100:.0f}% for {self.cpu_high_ticks}s")
                new_alerts.append(alert)
        elif cpu_util > self.cpu_warning:
            self.cpu_warning_ticks += 1
            if self.cpu_warning_ticks >= self.cpu_warning_duration:
                alert = self._create_alert(tick, "WARNING", "CPU",
                    f"CPU utilization > {self.cpu_warning*100:.0f}% for {self.cpu_warning_ticks}s")
                new_alerts.append(alert)
        else:
            self.cpu_high_ticks = 0
            self.cpu_warning_ticks = 0

        # --- MEMORY CHECKS ---
        mem_util = mem_state.get("utilization", 0)

        if mem_util > self.mem_critical:
            alert = self._create_alert(tick, "CRITICAL", "MEMORY",
                f"Memory usage at {mem_util*100:.1f}% — near OOM!")
            new_alerts.append(alert)
            if "memory_oom" not in [f["type"] for f in self.faults_detected]:
                self.faults_detected.append({"type": "memory_oom", "tick": tick})
        elif mem_util > self.mem_warning:
            alert = self._create_alert(tick, "WARNING", "MEMORY",
                f"Memory usage at {mem_util*100:.1f}%")
            new_alerts.append(alert)

        # Memory leak detection
        leaked = mem_state.get("leaked_kb", 0)
        if leaked > 1.0:
            if "memory_leak" not in [f["type"] for f in self.faults_detected]:
                alert = self._create_alert(tick, "FAULT", "MEMORY",
                    f"Memory leak detected! {leaked:.1f} KB leaked")
                new_alerts.append(alert)
                self.faults_detected.append({"type": "memory_leak", "tick": tick})

        # --- BATTERY CHECKS ---
        bat_pct = bat_state.get("percentage", 100) / 100.0

        if bat_pct < self.bat_critical:
            alert = self._create_alert(tick, "CRITICAL", "BATTERY",
                f"Battery at {bat_pct*100:.1f}% — critically low!")
            new_alerts.append(alert)
        elif bat_pct < self.bat_warning:
            alert = self._create_alert(tick, "WARNING", "BATTERY",
                f"Battery at {bat_pct*100:.1f}%")
            new_alerts.append(alert)

        if bat_state.get("depleted", False):
            alert = self._create_alert(tick, "CRITICAL", "BATTERY",
                "Battery depleted! Device shutdown imminent.")
            new_alerts.append(alert)

        # --- NETWORK CHECKS ---
        bw_util = net_state.get("bandwidth_utilization", 0)
        pkt_loss = net_state.get("packet_loss_rate", 0)

        if pkt_loss > self.pkt_loss_critical:
            alert = self._create_alert(tick, "CRITICAL", "NETWORK",
                f"Packet loss rate at {pkt_loss*100:.1f}%!")
            new_alerts.append(alert)

        if bw_util > self.bw_warning:
            alert = self._create_alert(tick, "WARNING", "NETWORK",
                f"Bandwidth utilization at {bw_util*100:.1f}%")
            new_alerts.append(alert)

        # --- COMMUNICATION TIMEOUT ---
        ticks_since_sync = tick - last_sync_tick
        timeout_threshold = expected_sync_interval * self.comm_timeout_mult
        if ticks_since_sync > timeout_threshold and last_sync_tick > 0:
            alert = self._create_alert(tick, "FAULT", "COMMUNICATION",
                f"No sync for {ticks_since_sync}s (expected every {expected_sync_interval}s)")
            new_alerts.append(alert)
            if "comm_timeout" not in [f["type"] for f in self.faults_detected]:
                self.faults_detected.append({"type": "comm_timeout", "tick": tick})

        # --- SENSOR ANOMALY (only check on sensing ticks) ---
        last_reading = sensors.get("last_reading", {})
        if is_sensing_tick and last_reading and last_reading.get("anomalies"):
            for sensor_name in last_reading["anomalies"]:
                alert = self._create_alert(tick, "FAULT", "SENSOR",
                    f"Anomaly detected on {sensor_name} sensor")
                new_alerts.append(alert)
                if f"sensor_{sensor_name}" not in [f["type"] for f in self.faults_detected]:
                    self.faults_detected.append({"type": f"sensor_{sensor_name}", "tick": tick})

        # --- TWIN DRIFT ---
        if twin_state:
            drift = twin_state.get("current_drift", 0)
            if drift > self.drift_warning:
                alert = self._create_alert(tick, "WARNING", "TWIN",
                    f"Digital Twin state drift at {drift*100:.1f}% — twin may be out of sync")
                new_alerts.append(alert)

        self.alerts.extend(new_alerts)
        return new_alerts

    def _create_alert(self, tick: int, severity: str, component: str, message: str) -> dict:
        """Create an alert dict."""
        if severity == "CRITICAL":
            self.critical_count += 1
            icon = "🔴"
        elif severity == "WARNING":
            self.warning_count += 1
            icon = "🟡"
        else:  # FAULT
            icon = "⚠️ "

        return {
            "tick": tick,
            "time": self._tick_to_time(tick),
            "severity": severity,
            "component": component,
            "message": message,
            "icon": icon,
        }

    def _tick_to_time(self, tick: int) -> str:
        """Convert tick (seconds) to HH:MM:SS string."""
        hours = tick // 3600
        minutes = (tick % 3600) // 60
        seconds = tick % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_summary(self) -> dict:
        """Return fault detection summary."""
        return {
            "total_alerts": len(self.alerts),
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "faults_detected": self.faults_detected,
            "last_10_alerts": self.alerts[-10:],
        }

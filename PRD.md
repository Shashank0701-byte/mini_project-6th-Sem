# 📋 Product Requirements Document (PRD)

## Digital Twin of a Resource-Constrained System

**Project Title:** Digital Twin for Resource-Constrained Embedded/IoT Systems  
**Team:** Vertex Club  
**Date:** 2026-02-26  
**Version:** 2.0  

---

## 1. Abstract

A Digital Twin is a virtual representation of a physical system that enables real-time monitoring, simulation, and optimization. This project focuses on developing a Digital Twin for **resource-constrained systems** — such as embedded devices, IoT sensor nodes, or low-power industrial units — where limitations in **memory, processing power, energy, and bandwidth** pose significant challenges.

The proposed model integrates lightweight data acquisition, efficient communication protocols, and optimized simulation algorithms to ensure accurate system representation without excessive computational overhead. By leveraging **edge computing** and **adaptive data synchronization** techniques, the Digital Twin enhances performance analysis, fault detection, and predictive maintenance while maintaining minimal resource consumption.

**Keywords:** Digital Twin, Resource-Constrained Systems, Embedded Systems, IoT, Edge Computing, Energy Efficiency

---

## 2. Problem Statement

Traditional Digital Twin models require high computational resources and continuous data transmission — unsuitable for low-power, resource-limited devices. The challenge is to build a Digital Twin that:

- Operates within strict **memory** constraints (e.g., 64KB–512KB RAM)
- Minimizes **CPU utilization** on the constrained device
- Conserves **battery/energy** through intelligent sync strategies
- Reduces **network bandwidth** usage via differential updates
- Still provides **accurate real-time monitoring**, fault detection, and predictive maintenance

---

## 3. Objectives

1. Design a lightweight Digital Twin model suitable for systems with limited memory, processing power, and energy resources
2. Minimize computational overhead by implementing efficient algorithms and optimized simulation techniques
3. Develop energy-aware data synchronization methods that reduce unnecessary data transmission
4. Integrate edge computing techniques for distributing processing tasks away from constrained devices
5. Ensure real-time monitoring and performance analysis within limited hardware capabilities
6. Implement fault detection and predictive maintenance mechanisms using minimal system resources
7. Evaluate system performance in terms of energy efficiency, latency, accuracy, and resource utilization

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DIGITAL TWIN SYSTEM                             │
│                                                                         │
│  ┌──────────────────┐    Sync     ┌──────────────────────────────────┐  │
│  │  PHYSICAL DEVICE  │◄──────────►│       DIGITAL TWIN (Virtual)     │  │
│  │  (IoT Sensor Node)│  Protocol  │                                  │  │
│  │                    │            │  ┌────────────┐ ┌─────────────┐  │  │
│  │  • Temperature     │            │  │  State      │ │ Prediction  │  │  │
│  │  • Humidity        │            │  │  Mirror     │ │ Engine      │  │  │
│  │  • Battery Level   │            │  └────────────┘ └─────────────┘  │  │
│  │  • CPU Load        │            │  ┌────────────┐ ┌─────────────┐  │  │
│  │  • Memory Usage    │            │  │  Fault      │ │ Performance │  │  │
│  │  • Network Traffic │            │  │  Detector   │ │ Analyzer    │  │  │
│  └──────────────────┘            │  └────────────┘ └─────────────┘  │  │
│           │                        └──────────────────────────────────┘  │
│           │                                     │                        │
│           ▼                                     ▼                        │
│  ┌──────────────────┐              ┌──────────────────────────────────┐  │
│  │   EDGE LAYER      │              │        ANALYSIS ENGINE           │  │
│  │                    │              │                                  │  │
│  │  • Local Filtering │              │  • Bottleneck Detection          │  │
│  │  • Data Compress.  │              │  • Predictive Maintenance        │  │
│  │  • Priority Queue  │              │  • What-If Scenarios             │  │
│  │  • Anomaly Preproc │              │  • Energy Optimization           │  │
│  └──────────────────┘              └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. The Simulated Physical Device

We simulate a **wireless IoT sensor node** deployed for environmental monitoring with the following hardware profile:

| Resource             | Specification                | Constraint Level |
|----------------------|------------------------------|------------------|
| Processor            | ARM Cortex-M4 (80 MHz)      | Limited          |
| RAM                  | 256 KB                       | Severely Limited |
| Flash Storage        | 1 MB                         | Limited          |
| Battery              | 3.7V Li-Po, 1000 mAh        | Critical         |
| Network              | LoRa / BLE (low bandwidth)   | Severely Limited |
| Sensors              | Temperature, Humidity, Light  | —                |
| Sampling Rate        | Configurable (1s – 60s)      | —                |

The device performs:
- **Sensor data acquisition** at configurable intervals
- **Local preprocessing** (filtering, averaging)
- **Data transmission** to the edge/cloud layer
- **Firmware task scheduling** with limited CPU cycles

---

## 6. Tech Stack

| Layer         | Phase 1 (Terminal)           | Phase 2 (Full UI)                    |
|---------------|------------------------------|--------------------------------------|
| Language      | Python 3.10+                 | Python + JavaScript                  |
| Simulation    | Custom discrete-event engine | Same engine, exposed via API         |
| Output        | Terminal / CLI               | Web Dashboard (HTML+JS+Charts)       |
| Visualization | ASCII tables, `rich` library | Chart.js live graphs                 |
| API           | —                            | FastAPI REST API + WebSocket         |
| Data          | In-memory + JSON logs        | In-memory + JSON/SQLite             |

---

---

# 🔵 PHASE 1 — Core Simulation Engine (Terminal-Based)

**Goal:** Build the complete Digital Twin simulation. The physical device is simulated in software. All output is via terminal. No frontend/UI required.

---

## P1.1 — Functional Requirements

### FR-1: Device Simulator (Physical System Model)

Simulate the IoT sensor node with realistic resource behavior:

- **CPU Model:**
  - Each task (sensing, processing, transmitting) consumes CPU cycles
  - CPU has a max clock rate; tasks are queued if CPU is busy
  - CPU utilization tracked as % over time
  - Overload condition when utilization > 90% sustained

- **Memory Model:**
  - Fixed RAM pool (e.g., 256 KB)
  - Each active task/buffer allocates memory
  - Sensor data buffers accumulate if not transmitted
  - Memory leak simulation (gradual increase to test fault detection)
  - Out-of-memory condition when usage > 95%

- **Energy/Battery Model:**
  - Battery starts at full capacity (e.g., 1000 mAh)
  - Each operation drains energy at different rates:
    - Sensing: 0.5 mA
    - Processing: 2.0 mA
    - Transmission: 15.0 mA (most expensive!)
    - Idle/Sleep: 0.01 mA
  - Battery depletion tracked over simulation time
  - Low battery warnings at configurable thresholds (20%, 10%, 5%)

- **Network/Bandwidth Model:**
  - Maximum bandwidth capacity (e.g., 50 kbps for LoRa)
  - Each transmission has a payload size
  - Bandwidth utilization tracked
  - Network congestion when utilization > 80%
  - Packet loss simulation at high congestion

- **Sensor Data Generation:**
  - Temperature: base 25°C ± noise, with occasional spikes (anomalies)
  - Humidity: base 60% ± noise
  - Light: day/night cycle pattern
  - Configurable anomaly injection (sensor faults, sudden spikes)

### FR-2: Digital Twin (Virtual Mirror)

The Digital Twin maintains a **virtual copy** of the device state:

- Receives state updates from the device simulator
- Mirrors: CPU usage, memory usage, battery level, sensor readings, network stats
- Tracks **state drift** — difference between predicted state and actual received state
- Interpolates/predicts device state between sync intervals
- Maintains a **state history log** for trend analysis

### FR-3: Data Synchronization Strategies

Implement and compare multiple sync strategies:

| Strategy               | Description                                              | Energy Cost |
|------------------------|----------------------------------------------------------|-------------|
| **Full-State Sync**    | Transmit entire device state at every interval           | High        |
| **Delta Sync**         | Transmit only changed values (differential updates)       | Medium      |
| **Event-Driven Sync**  | Transmit only when significant change detected           | Low         |
| **Adaptive Sync**      | Adjust sync frequency based on battery level & activity  | Lowest      |

- User can select sync strategy via CLI
- Each strategy's impact on bandwidth, energy, and twin accuracy is measured
- Comparison table printed at end of simulation

### FR-4: Edge Computing Layer

Simulate an edge processing node between device and twin:

- **Local data filtering:** Remove noise/outliers before transmission
- **Data compression:** Reduce payload size (e.g., run-length encoding, averaging)
- **Priority queuing:** Critical data (alarms) sent immediately; routine data batched
- **Anomaly pre-processing:** Detect obvious anomalies locally, flag for immediate sync
- Track: edge processing latency, data reduction ratio, energy savings

### FR-5: Bottleneck & Fault Detection

Real-time detection engine with configurable rules:

```
RESOURCE ALERTS:
  🔴 CRITICAL — CPU utilization > 95% for 30+ seconds
  🔴 CRITICAL — Memory usage > 95% (near OOM)
  🔴 CRITICAL — Battery level < 5%
  🔴 CRITICAL — Network packet loss > 20%
  🟡 WARNING  — CPU utilization > 80% for 60+ seconds
  🟡 WARNING  — Memory usage > 80%
  🟡 WARNING  — Battery level < 20%
  🟡 WARNING  — Bandwidth utilization > 80%
  🟡 WARNING  — State drift > threshold (twin out of sync)

FAULT DETECTION:
  ⚠️  Sensor anomaly — reading outside 3σ range
  ⚠️  Memory leak — memory monotonically increasing over N intervals
  ⚠️  Communication failure — no sync for > 2x expected interval
  ⚠️  CPU deadlock — task queue not draining for > N seconds
```

### FR-6: Predictive Maintenance

Based on historical trends, predict:

- **Battery depletion time:** "Battery will be exhausted in ~4.2 hours at current drain rate"
- **Memory exhaustion time:** "Memory will be full in ~45 minutes (leak detected)"
- **Maintenance window:** "Recommended maintenance in 3 hours before critical thresholds"
- Uses simple **linear regression** or **moving average** on resource consumption trends
- Print predictions in the terminal report

### FR-7: What-If Analysis (CLI Mode)

Allow users to test different configurations:

```bash
# What if we use delta sync instead of full-state sync?
python main.py --what-if --sync-strategy delta

# What if we reduce sampling rate to save energy?
python main.py --what-if --sampling-rate 30

# What if we add edge compression?
python main.py --what-if --edge-compression true

# What if the battery is smaller?
python main.py --what-if --battery-capacity 500
```

Display a **comparison table**:

```
┌──────────────────────────┬──────────────┬──────────────────┐
│ Metric                   │ Base Config  │ What-If Config   │
├──────────────────────────┼──────────────┼──────────────────┤
│ Sync Strategy            │ full-state   │ delta            │
│ Total Energy Consumed    │ 847 mAh      │ 423 mAh         │
│ Battery Life             │ 6.2 hours    │ 12.8 hours       │
│ Bandwidth Used           │ 4.8 MB       │ 1.2 MB          │
│ Twin Accuracy (avg)      │ 99.2%        │ 96.8%           │
│ Faults Detected          │ 5/5          │ 4/5             │
│ Avg Sync Latency         │ 120 ms       │ 85 ms           │
│ Data Packets Sent        │ 3600         │ 892             │
│ ↓ Energy Savings         │ —            │ 50.1% ↓         │
│ ↓ Bandwidth Savings      │ —            │ 75.0% ↓         │
└──────────────────────────┴──────────────┴──────────────────┘
```

### FR-8: Simulation Summary Report

At end of simulation, print a comprehensive report:

```
╔═══════════════════════════════════════════════════════════════════════╗
║           DIGITAL TWIN — SIMULATION SUMMARY REPORT                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  DEVICE STATUS                                                        ║
║  ─────────────────────────────────────────────────                     ║
║  Simulation Duration      : 6 hours (21,600 ticks @ 1s)               ║
║  Sync Strategy            : Adaptive                                  ║
║  Total Sensor Readings    : 21,600                                   ║
║  Total Syncs Performed    : 1,247                                    ║
║                                                                       ║
║  RESOURCE UTILIZATION                                                 ║
║  ─────────────────────────────────────────────────                     ║
║  CPU — Avg: 34.2%  Peak: 91.3%  Overload Events: 2                   ║
║  RAM — Avg: 45.8%  Peak: 87.1%  Leak Detected: Yes                   ║
║  Battery — Start: 1000 mAh  End: 312 mAh  Consumed: 688 mAh         ║
║  Network — Total Sent: 2.1 MB  Avg BW: 12.3 kbps  Pkt Loss: 0.3%   ║
║                                                                       ║
║  ENERGY BREAKDOWN                                                     ║
║  ─────────────────────────────────────────────────                     ║
║  Sensing       : 108 mAh  (15.7%)  ████░░░░░░░░░░░                   ║
║  Processing    : 172 mAh  (25.0%)  ██████░░░░░░░░░                   ║
║  Transmission  : 387 mAh  (56.2%)  ██████████████░                   ║
║  Idle/Sleep    :  21 mAh  ( 3.1%)  █░░░░░░░░░░░░░░                   ║
║                                                                       ║
║  DIGITAL TWIN ACCURACY                                                ║
║  ─────────────────────────────────────────────────                     ║
║  Average State Accuracy   : 97.3%                                    ║
║  Max State Drift          : 4.2% at tick 14,320                      ║
║  Sync Success Rate        : 99.7%                                    ║
║                                                                       ║
║  FAULT DETECTION                                                      ║
║  ─────────────────────────────────────────────────                     ║
║  Total Alerts             : 3 Critical, 7 Warnings                    ║
║  Faults Detected          : 2 (sensor anomaly, memory leak)           ║
║  Detection Latency        : Avg 2.3s                                 ║
║                                                                       ║
║  PREDICTIVE MAINTENANCE                                               ║
║  ─────────────────────────────────────────────────                     ║
║  Battery Depletion ETA    : ~2.7 hours remaining                     ║
║  Memory Full ETA          : ~8.1 hours (if leak continues)            ║
║  Next Maintenance Window  : Recommended in 2.5 hours                  ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### FR-9: Time-Series Data Logging

Log simulation data at every tick to JSON/CSV:

```json
{
  "tick": 1200,
  "timestamp_s": 1200,
  "device": {
    "cpu_utilization": 0.42,
    "memory_used_kb": 128.4,
    "memory_total_kb": 256,
    "battery_remaining_mah": 823.5,
    "battery_percent": 82.35,
    "sensors": {
      "temperature": 26.3,
      "humidity": 58.7,
      "light": 412
    },
    "network": {
      "bytes_sent": 256,
      "bandwidth_utilization": 0.32,
      "packet_loss": false
    }
  },
  "twin": {
    "state_accuracy": 0.984,
    "state_drift": 0.016,
    "last_sync_tick": 1195
  },
  "alerts": ["WARNING: Battery below 20%"],
  "sync_event": false
}
```

---

## P1.2 — Non-Functional Requirements

| Requirement       | Target                                                    |
|-------------------|-----------------------------------------------------------|
| Performance       | Simulate 6 hours of device time in < 5 seconds            |
| Modularity        | Each component is a separate module (device, twin, edge)  |
| Configurability   | All parameters via config file or CLI args                 |
| Reproducibility   | Seed-based RNG for consistent results                      |
| Logging           | Full tick-by-tick log exported as JSON/CSV                  |
| Error Handling    | Graceful handling of invalid configs                        |
| Extensibility     | Easy to add new sensor types or sync strategies             |

---

## P1.3 — Project Structure (Phase 1)

```
mini_project/
├── PRD.md                          # This document
├── config/
│   └── default_config.json         # Device & simulation parameters
├── src/
│   ├── __init__.py
│   ├── main.py                     # Entry point — CLI interface
│   ├── device/
│   │   ├── __init__.py
│   │   ├── sensor_node.py          # Physical device simulator
│   │   ├── cpu_model.py            # CPU utilization model
│   │   ├── memory_model.py         # RAM allocation/deallocation model
│   │   ├── battery_model.py        # Energy consumption & drain model
│   │   ├── network_model.py        # Bandwidth & packet loss model
│   │   └── sensor_data.py          # Sensor data generation (temp, humidity, light)
│   ├── twin/
│   │   ├── __init__.py
│   │   ├── digital_twin.py         # Virtual mirror of the device
│   │   ├── state_manager.py        # State tracking, drift calculation
│   │   └── predictor.py            # State interpolation between syncs
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── sync_engine.py          # Synchronization controller
│   │   ├── full_state_sync.py      # Strategy: full state every interval
│   │   ├── delta_sync.py           # Strategy: differential updates only
│   │   ├── event_driven_sync.py    # Strategy: sync on significant change
│   │   └── adaptive_sync.py        # Strategy: adjust freq by battery/activity
│   ├── edge/
│   │   ├── __init__.py
│   │   ├── edge_processor.py       # Edge computing simulation
│   │   ├── data_filter.py          # Noise removal, outlier filtering
│   │   ├── compressor.py           # Data compression (payload reduction)
│   │   └── priority_queue.py       # Critical vs. routine data queuing
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── fault_detector.py       # Real-time fault & bottleneck detection
│   │   ├── predictive_maintenance.py  # Trend-based predictions (battery, memory)
│   │   ├── reporter.py             # Summary report generator
│   │   └── what_if.py              # What-If comparison engine
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # Tick-by-tick data logger (JSON/CSV)
│       └── display.py              # Rich terminal output formatting
├── logs/                           # Simulation output logs
├── tests/
│   ├── test_device.py
│   ├── test_twin.py
│   ├── test_sync.py
│   ├── test_edge.py
│   ├── test_fault_detector.py
│   └── test_predictive.py
├── requirements.txt
└── README.md
```

---

## P1.4 — Deliverables (Phase 1)

| #  | Deliverable                       | Description                                         |
|----|-----------------------------------|-----------------------------------------------------|
| D1 | Device Simulator                  | Full IoT node simulation (CPU, RAM, battery, network, sensors) |
| D2 | Digital Twin Mirror               | Virtual state mirror with drift tracking             |
| D3 | Sync Strategies (4 types)         | Full-state, delta, event-driven, adaptive            |
| D4 | Edge Computing Layer              | Filtering, compression, priority queuing             |
| D5 | Fault & Bottleneck Detection      | Rule-based real-time alerting                        |
| D6 | Predictive Maintenance            | Battery/memory depletion prediction                  |
| D7 | What-If CLI                       | Compare sync strategies & configurations             |
| D8 | Terminal Summary Report           | Rich formatted comprehensive report                  |
| D9 | Data Logging                      | JSON/CSV tick-by-tick export                         |
| D10| Unit Tests                        | Test coverage for all core modules                   |
| D11| README + Documentation            | Setup instructions, usage guide                      |

---

## P1.5 — Evaluation Criteria (Phase 1)

| Criteria                         | Weight | What Evaluators Look For                                    |
|----------------------------------|--------|-------------------------------------------------------------|
| System Modeling Accuracy         | 20%    | Realistic CPU, memory, battery, network behavior            |
| Digital Twin Synchronization     | 20%    | State mirroring, drift detection, sync strategies work      |
| Edge Computing Integration       | 15%    | Filtering, compression, priority queuing implemented        |
| Fault Detection & Prediction     | 15%    | Meaningful alerts, accurate predictions                     |
| Energy Efficiency Analysis       | 15%    | Clear comparison of sync strategies' energy impact          |
| Code Quality & Modularity        | 15%    | Clean code, proper separation of concerns, tests           |

---

---

# 🟢 PHASE 2 — Full UI + Visualization Dashboard

**Goal:** Add a web-based dashboard with live visualizations, interactive controls, and real-time simulation playback.

---

## P2.1 — Functional Requirements

### FR-10: REST API Layer
- Expose the simulation engine via a REST API (FastAPI):
  - `POST /api/simulation/start` — Start simulation with config
  - `GET /api/simulation/status` — Get current device + twin state
  - `GET /api/simulation/history` — Get tick-by-tick history
  - `POST /api/simulation/what-if` — Run what-if comparison
  - `GET /api/simulation/faults` — Get detected faults & predictions
  - `PUT /api/simulation/config` — Update parameters mid-run
  - `GET /api/simulation/energy-breakdown` — Energy consumption by component

### FR-11: Live Resource Utilization Dashboard
- **Real-time line/area charts** showing:
  - CPU utilization over time (%)
  - Memory usage over time (KB / %)
  - Battery drain curve (mAh remaining)
  - Bandwidth utilization over time
  - Sensor readings (temperature, humidity, light)
  - Twin state accuracy / drift over time
- Charts update live via WebSocket as simulation progresses

### FR-12: Resource Sliders (Interactive Controls)
- Users can adjust simulation parameters via slider controls:
  - Sampling rate (1s → 60s)
  - Battery capacity (200 mAh → 2000 mAh)
  - RAM size (64 KB → 512 KB)
  - Network bandwidth (10 kbps → 100 kbps)
  - Sync strategy selector (dropdown: full/delta/event/adaptive)
  - Edge compression toggle (on/off)

### FR-13: Bottleneck Warning Panel
- Dedicated alert panel:
  - Real-time resource warnings with severity icons
  - Color-coded: 🔴 Critical (red), 🟡 Warning (yellow), 🟢 Normal (green)
  - Clickable alerts that highlight the corresponding point on timeline

### FR-14: Energy Breakdown Visualization
- **Pie chart / stacked bar** showing energy consumption by component:
  - Sensing vs. Processing vs. Transmission vs. Idle
- **Battery life predictor** with live countdown
- Comparison view for different sync strategies

### FR-15: "What-If?" Toggle Mode
- Toggle to enter What-If comparison mode:
  - Side-by-side charts: Base vs. Modified configuration
  - Difference metrics highlighted (e.g., "↓ 50% energy savings")
  - Strategy comparison matrix

### FR-16: Simulation Playback Controls
- ▶️ Play / ⏸️ Pause / ⏩ Speed / ⏪ Rewind
- Timeline scrubber to jump to any simulation tick
- Speed: 1x / 5x / 10x / 50x

### FR-17: Export & Download
- Export as: CSV, JSON, PDF report

---

## P2.2 — Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  🔧 Digital Twin — IoT Resource Monitor                 [⚙️] [📥]  │
├──────────────┬───────────────────────────────────────────────────────┤
│              │              RESOURCE CHARTS                          │
│  DEVICE      │   ┌──────────────────────────────────────────────┐   │
│  CONFIG      │   │  📈 CPU Utilization (%)                       │   │
│              │   │  ████████████░░░░░░░░░░░░░░                  │   │
│ Sampling [━] │   └──────────────────────────────────────────────┘   │
│ Battery  [━] │   ┌──────────────────────────────────────────────┐   │
│ RAM      [━] │   │  📈 Memory Usage (KB)                        │   │
│ BW       [━] │   │  ██████░░░░░░░░░░░░░░░░░░░░░                │   │
│              │   └──────────────────────────────────────────────┘   │
│ Sync: [▼]    │   ┌──────────────────────────────────────────────┐   │
│ Edge: [✓]    │   │  📈 Battery Drain Curve                      │   │
│              │   │  ░░░░░░░░████████████████████                │   │
│ [▶️ Start]   │   └──────────────────────────────────────────────┘   │
│ [⏸️ Pause]   │   ┌──────────────────────────────────────────────┐   │
│ [🔄 Reset]   │   │  📈 Network Bandwidth                        │   │
│              │   │  ███░░░░███░░░░███░░░░░░░░░░                 │   │
│ Speed: [1x]  │   └──────────────────────────────────────────────┘   │
│              ├───────────────────────────────────────────────────────┤
│  LIVE STATS  │   ALERTS & PREDICTIONS                               │
│  ──────────  │   ┌──────────────────────────────────────────────┐   │
│  CPU:  34.2% │   │ [00:45] 🟡 Memory usage > 80%               │   │
│  RAM: 128 KB │   │ [01:12] 🟡 Battery below 20%                 │   │
│  BAT: 823mAh│   │ [01:30] 🔴 CPU overload detected              │   │
│  BW:  12kbps│   │ [01:45] ⚠️ Memory leak pattern detected       │   │
│  Drift: 1.6% │   │                                             │   │
│              │   │ ⏱️ Battery ETA: 2.7 hours                     │   │
│ [What-If?]   │   │ 💾 Memory Full ETA: 8.1 hours                │   │
│              │   └──────────────────────────────────────────────┘   │
├──────────────┴───────────────────────────────────────────────────────┤
│  ⚡ ENERGY BREAKDOWN    │ 🔄 SYNC STRATEGY COMPARISON              │
│  Sensing:    15.7% ████ │ Full-State: 847 mAh │ 4.8 MB │ 99.2%   │
│  Processing: 25.0% █████│ Delta:      423 mAh │ 1.2 MB │ 96.8%   │
│  Transmit:   56.2% █████│ Event:      312 mAh │ 0.8 MB │ 94.1%   │
│  Idle:        3.1% █    │ Adaptive:   298 mAh │ 0.7 MB │ 95.5%   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## P2.3 — Deliverables (Phase 2)

| #   | Deliverable                          | Description                                     |
|-----|--------------------------------------|-------------------------------------------------|
| D12 | REST API                             | FastAPI endpoints for simulation control         |
| D13 | WebSocket Live Feed                  | Real-time data push to frontend                  |
| D14 | Dashboard UI                         | Dark-themed responsive dashboard                 |
| D15 | Resource Charts (5+)                 | CPU, RAM, battery, network, sensors, drift       |
| D16 | Interactive Sliders                  | Parameter controls for device configuration      |
| D17 | Alert Panel                          | Real-time fault detection alerts                 |
| D18 | Energy Breakdown Viz                 | Pie/bar chart of energy by component             |
| D19 | What-If Toggle                       | Side-by-side strategy comparison                 |
| D20 | Playback Controls                    | Play/Pause/Speed/Scrub features                  |
| D21 | Export Feature                       | CSV, JSON, PDF export                            |

---

## P2.4 — Evaluation Criteria (Phase 2)

| Criteria                    | Weight | What Evaluators Look For                                    |
|-----------------------------|--------|-------------------------------------------------------------|
| Visualization               | 25%    | Live charts accurate, smooth, informative                   |
| Interactive Controls        | 20%    | Sliders, sync strategy selector, playback work              |
| What-If & Energy Analysis   | 20%    | Clear comparison with actionable insights                   |
| UI/UX Design                | 15%    | Clean, modern, professional dashboard                       |
| API Design & Integration    | 10%    | RESTful, well-documented, proper error handling             |
| Code Quality                | 10%    | Clean separation, reusable components, tests                |

---

## 7. Milestones & Timeline

| Milestone | Description                                        | Target      |
|-----------|----------------------------------------------------|-------------|
| M1        | Device Simulator (CPU, RAM, Battery, Network)      | Week 1      |
| M2        | Sensor Data + Digital Twin State Mirror             | Week 1      |
| M3        | Sync Strategies (4 types) + Edge Layer              | Week 2      |
| M4        | Fault Detection + Predictive Maintenance            | Week 2      |
| M5        | What-If CLI + Summary Report + Data Logging         | Week 3      |
| M6        | **Phase 1 Complete — Demo Ready**                   | **Week 3**  |
| M7        | REST API + WebSocket                                | Week 4      |
| M8        | Dashboard UI + Charts                               | Week 4-5    |
| M9        | Sliders + What-If Toggle + Energy Viz               | Week 5      |
| M10       | **Phase 2 Complete — Final Demo**                   | **Week 6**  |

---

## 8. Literature References

1. Smith et al. (2021) — Lightweight Digital Twin for IoT with edge-assisted computation
2. Zhang & Lee (2022) — Modular Digital Twin for embedded systems with memory/CPU constraints
3. Kumar et al. (2023) — Energy-aware adaptive simulation framework for battery-powered devices
4. Ali & Hossain (2021) — Delta-based synchronization for bandwidth-efficient Digital Twins in WSNs

---

> **Next Step:** Begin Phase 1 implementation — start with device models (`cpu_model.py`, `memory_model.py`, `battery_model.py`, `network_model.py`) and sensor data generation.

# 🔧 Digital Twin — Resource-Constrained IoT System

A **Digital Twin** for a resource-constrained IoT sensor node that simulates hardware behavior (CPU, memory, battery, network), implements multiple data synchronization strategies, and provides fault detection with predictive maintenance — all within strict resource limits.

## 🎯 What This Does

- Simulates a **wireless IoT sensor node** with realistic hardware constraints (256KB RAM, 1000mAh battery, LoRa network)
- Maintains a **virtual twin** that mirrors device state with drift tracking
- Implements **4 sync strategies**: Full-State, Delta, Event-Driven, Adaptive
- Simulates **edge computing** layer: data filtering, compression, priority queuing
- Detects **faults**: CPU overload, memory leaks, sensor anomalies, communication failures
- **Predicts** battery depletion, memory exhaustion, and maintenance windows
- Supports **What-If?** analysis to compare configurations and sync strategies
- Exports tick-by-tick data as JSON/CSV

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation
```bash
cd mini_project
pip install -r requirements.txt
```

### Run Simulation
```bash
# Run with default config (adaptive sync, 6-hour simulation)
python -m src.main

# Run with specific sync strategy
python -m src.main --sync-strategy delta

# Run with custom device parameters
python -m src.main --battery-capacity 500 --ram-size 128 --sampling-rate 10

# What-If comparison (base vs. modified)
python -m src.main --what-if --sync-strategy delta --battery-capacity 500

# Custom config file
python -m src.main --config config/custom_config.json
```

## 📁 Project Structure

```
mini_project/
├── config/
│   └── default_config.json       # Device & simulation parameters
├── src/
│   ├── main.py                   # CLI entry point
│   ├── device/                   # Physical device simulator
│   │   ├── sensor_node.py        # Orchestrates device behavior
│   │   ├── cpu_model.py          # CPU utilization model
│   │   ├── memory_model.py       # RAM allocation model
│   │   ├── battery_model.py      # Battery drain model
│   │   ├── network_model.py      # Bandwidth & packet loss
│   │   └── sensor_data.py        # Sensor data generation
│   ├── twin/                     # Digital Twin (virtual mirror)
│   │   ├── digital_twin.py       # State mirror + drift tracking
│   │   ├── state_manager.py      # State history management
│   │   └── predictor.py          # State interpolation
│   ├── sync/                     # Synchronization strategies
│   │   ├── sync_engine.py        # Strategy selector
│   │   ├── full_state_sync.py    # Full state every N seconds
│   │   ├── delta_sync.py         # Differential updates
│   │   ├── event_driven_sync.py  # Sync on significant change
│   │   └── adaptive_sync.py      # Battery-aware adaptive
│   ├── edge/                     # Edge computing layer
│   │   ├── edge_processor.py     # Edge orchestrator
│   │   ├── data_filter.py        # Noise removal
│   │   ├── compressor.py         # Payload compression
│   │   └── priority_queue.py     # Critical vs routine data
│   ├── analysis/                 # Analysis engine
│   │   ├── fault_detector.py     # Bottleneck & fault detection
│   │   ├── predictive_maintenance.py  # Trend-based predictions
│   │   ├── reporter.py           # Summary report generator
│   │   └── what_if.py            # What-If comparison engine
│   └── utils/
│       ├── logger.py             # Tick data logger
│       └── display.py            # Terminal formatting
├── logs/                         # Output logs
├── tests/                        # Unit tests
├── requirements.txt
├── PRD.md
└── README.md
```

## 📊 Key Concepts Demonstrated

| Concept | Implementation |
|---------|----------------|
| **System Modeling** | CPU, memory, battery, network as discrete models |
| **Digital Twin** | Virtual state mirror with accuracy tracking |
| **Edge Computing** | Local filtering, compression, priority queuing |
| **Energy Efficiency** | 4 sync strategies with energy impact comparison |
| **Fault Detection** | Rule-based real-time alerting (CPU, memory, sensor) |
| **Predictive Maintenance** | Linear regression on resource trends |
| **State Management** | Tick-by-tick state tracking with history |
| **What-If Analysis** | Configuration comparison with metrics |

## 📋 Phases

- **Phase 1:** Core simulation engine with terminal output ← *current*
- **Phase 2:** Web dashboard with live charts, sliders, and playback controls

## 👥 Team
Vertex Club

## 📄 License
Academic Project — Mini Project Evaluation

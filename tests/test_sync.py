"""Tests for sync strategies."""

import json
import os
import pytest
import copy

TEST_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "default_config.json"
)

with open(TEST_CONFIG_PATH, "r") as f:
    TEST_CONFIG = json.load(f)

SAMPLE_STATE = {
    "cpu": {"utilization": 0.35},
    "memory": {"utilization": 0.18, "used_kb": 46},
    "battery": {"percentage": 95.0, "remaining_mah": 950},
    "network": {"bandwidth_utilization": 0.15},
    "tick": 100,
}


class TestFullStateSync:
    """Test full-state sync strategy."""

    def setup_method(self):
        from src.sync.full_state_sync import FullStateSync
        self.sync = FullStateSync(TEST_CONFIG["sync"])

    def test_should_sync_at_interval(self):
        """Should sync at fixed intervals."""
        interval = self.sync.interval_s
        assert self.sync.should_sync(interval, SAMPLE_STATE) is True

    def test_should_not_sync_before_interval(self):
        """Should not sync before interval."""
        assert self.sync.should_sync(1, SAMPLE_STATE) is False

    def test_payload_is_full_state(self):
        """Payload should contain complete state."""
        payload = self.sync.prepare_payload(SAMPLE_STATE)
        assert payload["type"] == "full_state"
        assert payload["data"] == SAMPLE_STATE


class TestDeltaSync:
    """Test delta sync strategy."""

    def setup_method(self):
        from src.sync.delta_sync import DeltaSync
        self.sync = DeltaSync(TEST_CONFIG["sync"])

    def test_first_sync_is_full(self):
        """First sync should be full state."""
        payload = self.sync.prepare_payload(SAMPLE_STATE)
        assert payload["type"] == "full_state"

    def test_unchanged_state_sends_few_fields(self):
        """Unchanged state should result in small delta."""
        self.sync.prepare_payload(SAMPLE_STATE)
        payload = self.sync.prepare_payload(SAMPLE_STATE)
        assert payload["type"] == "delta"
        assert payload["fields_changed"] <= payload["fields_total"]

    def test_changed_state_sends_delta(self):
        """Changed values should appear in delta."""
        self.sync.prepare_payload(SAMPLE_STATE)
        modified_state = copy.deepcopy(SAMPLE_STATE)
        modified_state["cpu"]["utilization"] = 0.90  # Big change
        payload = self.sync.prepare_payload(modified_state)
        assert payload["type"] == "delta"
        assert payload["fields_changed"] > 0


class TestEventDrivenSync:
    """Test event-driven sync strategy."""

    def setup_method(self):
        from src.sync.event_driven_sync import EventDrivenSync
        self.sync = EventDrivenSync(TEST_CONFIG["sync"])

    def test_first_call_should_sync(self):
        """First call should always sync."""
        assert self.sync.should_sync(1, SAMPLE_STATE) is True

    def test_no_change_no_sync(self):
        """No significant change should not trigger sync."""
        self.sync.prepare_payload(SAMPLE_STATE)
        # Same state
        assert self.sync.should_sync(2, SAMPLE_STATE) is False

    def test_significant_change_triggers_sync(self):
        """Significant change should trigger sync."""
        self.sync.prepare_payload(SAMPLE_STATE)
        modified = copy.deepcopy(SAMPLE_STATE)
        modified["cpu"]["utilization"] = 0.90  # Big change
        assert self.sync.should_sync(2, modified) is True

    def test_heartbeat_sync(self):
        """Should sync after long silence even without changes."""
        self.sync.prepare_payload(SAMPLE_STATE)
        # After prepare_payload, last_sync_tick = 100 (from SAMPLE_STATE tick)
        # So far_future must be relative to that
        far_future = SAMPLE_STATE["tick"] + self.sync.max_silent_interval + 10
        assert self.sync.should_sync(far_future, SAMPLE_STATE) is True


class TestAdaptiveSync:
    """Test adaptive sync strategy."""

    def setup_method(self):
        from src.sync.adaptive_sync import AdaptiveSync
        self.sync = AdaptiveSync(TEST_CONFIG["sync"])

    def test_high_battery_frequent_sync(self):
        """High battery should use shortest interval."""
        self.sync._update_interval(0.90)
        assert self.sync.current_interval == self.sync.high_battery_interval

    def test_low_battery_infrequent_sync(self):
        """Low battery should use longest interval."""
        self.sync._update_interval(0.10)
        assert self.sync.current_interval == self.sync.low_battery_interval

    def test_medium_battery_medium_sync(self):
        """Medium battery should use medium interval."""
        self.sync._update_interval(0.30)
        assert self.sync.current_interval == self.sync.medium_battery_interval


class TestSyncEngine:
    """Test sync engine orchestration."""

    def setup_method(self):
        from src.sync.sync_engine import SyncEngine
        self.engine = SyncEngine(TEST_CONFIG)

    def test_default_strategy(self):
        """Should use default strategy from config."""
        assert self.engine.strategy_name == TEST_CONFIG["sync"]["default_strategy"]

    def test_invalid_strategy_raises(self):
        """Invalid strategy should raise ValueError."""
        from src.sync.sync_engine import SyncEngine
        with pytest.raises(ValueError):
            SyncEngine(TEST_CONFIG, strategy_name="nonexistent")

    def test_prepare_payload_returns_size(self):
        """Payload preparation should return size in bytes."""
        payload = self.engine.prepare_payload(SAMPLE_STATE)
        assert "size_bytes" in payload
        assert payload["size_bytes"] > 0

    def test_record_sync(self):
        """Sync events should be recorded."""
        self.engine.record_sync(100, 256, True)
        stats = self.engine.get_stats()
        assert stats["total_syncs"] == 1
        assert stats["total_bytes_synced"] == 256

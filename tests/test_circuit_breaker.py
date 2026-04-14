import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from src.functools.circuit_breaker import (
    CircuitBreaker, Watcher, CircuitStatus,
    NotValidWatcher, CircuitOpenException
)


# ---------------------------------------------------------------------------
# Watcher unit tests
# ---------------------------------------------------------------------------

class TestWatcher:

    def test_initial_status_is_ok(self):
        w = Watcher("test")
        assert w.status == CircuitStatus.STATUS_OK

    def test_add_failure_increments_attempts(self):
        w = Watcher("test")
        w.add_failure(Exception("err"))
        w.add_failure(Exception("err2"))
        assert w._failure_dict["attempts"] == 2

    def test_refresh_status_opens_circuit_at_max_attempts(self):
        w = Watcher("test", max_attempts=3)
        for _ in range(3):
            w.add_failure(Exception("err"))
        w.refresh_status()
        assert w.status == CircuitStatus.STATUS_KO

    def test_refresh_status_does_not_open_before_max_attempts(self):
        w = Watcher("test", max_attempts=3)
        for _ in range(2):
            w.add_failure(Exception("err"))
        w.refresh_status()
        assert w.status == CircuitStatus.STATUS_OK

    def test_cooldown_resets_circuit(self):
        w = Watcher("test", max_attempts=1, sec_cooldown=60)
        w.add_failure(Exception("err"))
        w.refresh_status()
        assert w.status == CircuitStatus.STATUS_KO

        past = datetime.now() - timedelta(seconds=61)
        w._changedAt = past
        w.refresh_status()
        assert w.status == CircuitStatus.STATUS_OK
        assert w._failure_dict == {}

    def test_cooldown_does_not_reset_before_expiry(self):
        w = Watcher("test", max_attempts=1, sec_cooldown=60)
        w.add_failure(Exception("err"))
        w.refresh_status()
        assert w.status == CircuitStatus.STATUS_KO

        w.refresh_status()  # cooldown not elapsed
        assert w.status == CircuitStatus.STATUS_KO

    def test_eq_with_string(self):
        w = Watcher("my-watcher")
        assert w == "my-watcher"
        assert w != "other"

    def test_eq_with_watcher(self):
        w1 = Watcher("same")
        w2 = Watcher("same")
        w3 = Watcher("different")
        assert w1 == w2
        assert w1 != w3

    def test_eq_with_other_type(self):
        w = Watcher("test")
        assert w != 42
        assert w != None


# ---------------------------------------------------------------------------
# CircuitBreaker unit tests
# ---------------------------------------------------------------------------

class TestCircuitBreaker:

    def test_wire_circuit_anonymous_creates_watcher(self):
        cb = CircuitBreaker()
        cb.wire_circuit(lambda: None)
        assert len(cb._watchers) == 1

    def test_wire_circuit_anonymous_creates_distinct_watchers(self):
        cb = CircuitBreaker()
        cb.wire_circuit(lambda: None)
        cb.wire_circuit(lambda: None)
        assert len(cb._watchers) == 2
        assert cb._watchers[0].name != cb._watchers[1].name

    def test_wire_circuit_named_watcher_not_found_raises(self):
        cb = CircuitBreaker()
        with pytest.raises(NotValidWatcher):
            cb.wire_circuit(lambda: None, watcher_name="ghost")

    def test_wire_circuit_named_uses_existing_watcher(self):
        cb = CircuitBreaker()
        w = Watcher("svc")
        cb.register_watcher(w)
        wrapped = cb.wire_circuit(lambda: 42, watcher_name="svc")
        assert wrapped() == 42

    def test_successful_call_does_not_add_failures(self):
        cb = CircuitBreaker()
        wrapped = cb.wire_circuit(lambda: "ok")
        wrapped()
        watcher = cb._watchers[0]
        assert watcher._failure_dict.get("attempts", 0) == 0

    def test_failed_call_records_failure(self):
        cb = CircuitBreaker()
        def boom():
            raise ValueError("boom")
        wrapped = cb.wire_circuit(boom)
        with pytest.raises(ValueError):
            wrapped()
        assert cb._watchers[0]._failure_dict["attempts"] == 1

    def test_circuit_opens_after_max_attempts(self):
        cb = CircuitBreaker()
        w = Watcher("svc", max_attempts=3)
        cb.register_watcher(w)
        def boom():
            raise ValueError("boom")
        wrapped = cb.wire_circuit(boom, watcher_name="svc")
        for _ in range(3):
            with pytest.raises(ValueError):
                wrapped()
        with pytest.raises(CircuitOpenException):
            wrapped()

    def test_open_circuit_raises_circuit_open_exception(self):
        cb = CircuitBreaker()
        w = Watcher("svc", max_attempts=1)
        cb.register_watcher(w)
        def boom():
            raise ValueError("boom")
        wrapped = cb.wire_circuit(boom, watcher_name="svc")
        with pytest.raises(ValueError):
            wrapped()
        with pytest.raises(CircuitOpenException):
            wrapped()

    def test_exception_propagates_through_wrapper(self):
        cb = CircuitBreaker()
        def boom():
            raise RuntimeError("propagate me")
        wrapped = cb.wire_circuit(boom)
        with pytest.raises(RuntimeError, match="propagate me"):
            wrapped()

    def test_watcher_shared_across_calls(self):
        cb = CircuitBreaker()
        w = Watcher("svc", max_attempts=5)
        cb.register_watcher(w)
        def boom():
            raise ValueError()
        wrapped = cb.wire_circuit(boom, watcher_name="svc")
        for _ in range(3):
            with pytest.raises(ValueError):
                wrapped()
        assert w._failure_dict["attempts"] == 3

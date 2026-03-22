from core.application.capabilities.control_plane import (
    handle_control_plane_status,
    handle_scheduler_command,
)


class DummyStorage:
    def get_stats(self):
        return {"followers_total": 10, "followers_followed": 4, "runs_total": 2, "security_events_total": 9}


class DummyConfig:
    db_engine = "sqlite"
    auth_mode = "pat"


class LockStorage:
    def __init__(self, initial: dict[str, str] | None = None):
        self.values = dict(initial or {})
        self.commits = 0

    def get_setting(self, key: str):
        return self.values.get(key)

    def try_acquire_distributed_lock(self, lock_key: str, lock_until_epoch: int, now_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        current = self.values.get(key)
        if current is not None and int(current) > now_epoch:
            return False
        self.values[key] = str(lock_until_epoch)
        self.commits += 1
        return True

    def release_distributed_lock(self, lock_key: str, expected_lock_until_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        if self.values.get(key) != str(expected_lock_until_epoch):
            return False
        self.values[key] = "0"
        self.commits += 1
        return True


def test_control_plane_status_returns_health_payload():
    status, payload = handle_control_plane_status(DummyStorage(), DummyConfig())
    assert status == 0
    assert payload["service"] == "github_follower_bot_control_plane"
    assert payload["status"] == "ok"
    assert payload["stats"]["followers_total"] == 10
    assert payload["stats"]["followers"] == 10
    assert payload["stats"]["security_events_total"] == 9


def test_scheduler_command_rejects_invalid_params():
    status, payload = handle_scheduler_command(object(), lambda _svc: {}, interval_seconds=0, max_ticks=1)
    assert status == 2
    assert payload["error"] == "invalid_interval"


def test_scheduler_command_runs_expected_ticks_without_sleep():
    class Service:
        pass

    calls = {"count": 0, "slept": 0}

    def run_executor(_service):
        calls["count"] += 1
        return {"run_id": calls["count"]}

    def fake_sleep(_seconds):
        calls["slept"] += 1

    status, payload = handle_scheduler_command(
        Service(),
        run_executor,
        interval_seconds=0.01,
        max_ticks=3,
        sleep_fn=fake_sleep,
    )

    assert status == 0
    assert payload["errors"] == 0
    assert len(payload["ticks"]) == 3
    assert calls["count"] == 3
    assert calls["slept"] == 2


def test_scheduler_command_returns_lock_not_acquired_when_active_lock():
    storage = LockStorage(initial={"scheduler_lock:default": "9999999999"})

    status, payload = handle_scheduler_command(
        object(),
        lambda _svc: {"run_id": 1},
        interval_seconds=1,
        max_ticks=1,
        storage=storage,
    )

    assert status == 2
    assert payload["status"] == "lock_not_acquired"
    assert payload["lock_key"] == "default"


def test_scheduler_command_acquires_and_releases_lock():
    storage = LockStorage()

    status, payload = handle_scheduler_command(
        object(),
        lambda _svc: {"run_id": 1},
        interval_seconds=1,
        max_ticks=1,
        storage=storage,
        lock_key="tenant-a",
        lock_ttl_seconds=60,
        sleep_fn=lambda _s: None,
    )

    assert status == 0
    assert payload["status"] == "completed"
    assert storage.values["scheduler_lock:tenant-a"] == "0"
    assert storage.commits >= 2


def test_scheduler_release_does_not_clear_newer_lock_owner():
    storage = LockStorage()

    def run_executor(_svc):
        # Simulate another process acquiring a new lock value before release.
        storage.values["scheduler_lock:tenant-b"] = "9999999999"
        return {"run_id": 1}

    status, payload = handle_scheduler_command(
        object(),
        run_executor,
        interval_seconds=1,
        max_ticks=1,
        storage=storage,
        lock_key="tenant-b",
        lock_ttl_seconds=60,
        sleep_fn=lambda _s: None,
    )

    assert status == 0
    assert payload["status"] == "completed"
    assert storage.values["scheduler_lock:tenant-b"] == "9999999999"

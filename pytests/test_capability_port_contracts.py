from bot import BotConfig, build_storage
from core.application.capabilities.follow_back import handle_resume_command
from core.domain.contracts import StoragePort


class DummyFollowQueueService:
    def __init__(self):
        self.calls = []

    def process_follow_queue(self, run_id: int, trace_id: str, max_jobs=None):
        self.calls.append((run_id, trace_id, max_jobs))
        return 2


def test_sqlite_storage_implements_storage_port_contract(tmp_path):
    config = BotConfig(github_user="bot", github_token="token", db_path=str(tmp_path / "state.db"))
    storage = build_storage(config)
    try:
        assert isinstance(storage, StoragePort)
    finally:
        storage.close()


def test_resume_capability_contract_with_storage_port(tmp_path):
    config = BotConfig(github_user="bot", github_token="token", db_path=str(tmp_path / "state.db"))
    storage = build_storage(config)
    service = DummyFollowQueueService()

    try:
        run_id = storage.begin_run(trace_id="trace-contract")
        storage.upsert_follow_job(run_id, "alice", "pending")
        storage.commit()

        status, payload = handle_resume_command(storage, service, run_id=run_id, max_jobs=5)

        assert status == 0
        assert payload["run_id"] == run_id
        assert payload["processed"] == 2
        assert payload["queue"]["total"] >= 1
        assert service.calls == [(run_id, "trace-contract", 5)]
    finally:
        storage.close()

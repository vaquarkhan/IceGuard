"""Integration: coordinated multi-participant write (mocked)."""

from unittest.mock import MagicMock

from iceguard.checkpoint_store import CheckpointStore
from iceguard.coordinator import Coordinator
from iceguard.enums import TransactionStatus
from iceguard.metrics import MetricsEmitter


class _Mem:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def put_object(self, **kwargs):
        self.store[kwargs["Key"]] = kwargs["Body"]

    def get_object(self, **kwargs):
        from botocore.exceptions import ClientError

        k = kwargs["Key"]
        if k not in self.store:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "n"}}, "GetObject"
            )
        b = self.store[k]

        class B:
            def read(self_inner):
                return b if isinstance(b, bytes) else b.encode()

        return {"Body": B()}

    def delete_object(self, **kwargs):
        self.store.pop(kwargs["Key"], None)


def _store():
    m = _Mem()
    c = MagicMock()
    c.put_object.side_effect = m.put_object
    c.get_object.side_effect = m.get_object
    c.delete_object.side_effect = m.delete_object
    return CheckpointStore("b", "pfx/", s3_client=c)


class P:
    def __init__(self, pid: str):
        self.participant_id = pid
        self.lambda_function_name = "fn"

    def prepare_vote(self):
        return "YES"

    def commit_phase(self):
        pass

    def abort_phase(self):
        pass


class Slow:
    participant_id = "slow"
    lambda_function_name = "fn"

    def prepare_vote(self):
        import time

        time.sleep(0.3)
        return "YES"


def test_e2e_two_phase_commit_metrics():
    m = MagicMock(spec=MetricsEmitter)
    c = Coordinator([P("a"), P("b")], _store(), timeout_ms=5000, metrics_emitter=m)
    c.prepare()
    c.commit()
    assert m.emit_coordination_outcome.call_count >= 1


def test_recovery_after_timeout_prepare():
    st = _store()
    c = Coordinator([Slow()], st, transaction_id="tid-timeout", timeout_ms=20)
    try:
        c.prepare()
    except Exception:
        pass
    c2 = Coordinator([Slow()], st, transaction_id="tid-timeout", timeout_ms=20)
    st_loaded = c2.recover("tid-timeout")
    assert st_loaded.status in (
        TransactionStatus.ABORTED,
        TransactionStatus.PREPARED,
        TransactionStatus.PREPARING,
    )

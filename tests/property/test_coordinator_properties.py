# Feature: iceguard, Property 9–12: Coordinator
import uuid
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.checkpoint_store import CheckpointStore
from iceguard.coordinator import Coordinator
from iceguard.enums import TransactionStatus


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


class Yes:
    participant_id = "p"
    lambda_function_name = "fn"

    def prepare_vote(self):
        return "YES"

    def commit_phase(self):
        pass

    def abort_phase(self):
        pass


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=1, max_value=6))
def test_property_9_all_yes_reaches_prepared_then_commit(n: int) -> None:
    parts = [Yes() for _ in range(n)]
    for i, p in enumerate(parts):
        p.participant_id = f"p{i}"
    c = Coordinator(parts, _store(), timeout_ms=5000)
    st = c.prepare()
    assert st.status == TransactionStatus.PREPARED
    st2 = c.commit()
    assert st2.status == TransactionStatus.COMMITTED


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=2, max_value=6), st.integers(min_value=0, max_value=5))
def test_property_10_one_no_aborts(n: int, bad_idx: int) -> None:
    bad_idx = bad_idx % n

    class V:
        def __init__(self, i: int):
            self.participant_id = f"v{i}"
            self.lambda_function_name = "fn"
            self._i = i

        def prepare_vote(self):
            return "NO" if self._i == bad_idx else "YES"

    parts = [V(i) for i in range(n)]
    c = Coordinator(parts, _store(), timeout_ms=5000)
    st = c.prepare()
    assert st.status == TransactionStatus.ABORTED


@settings(max_examples=80, deadline=None)
@given(st.integers(min_value=1, max_value=8))
def test_property_11_transaction_state_roundtrip(n: int) -> None:
    parts = [Yes() for _ in range(n)]
    for i, p in enumerate(parts):
        p.participant_id = f"q{i}"
    st_backend = _store()
    tid = str(uuid.uuid4())
    c = Coordinator(parts, st_backend, transaction_id=tid, timeout_ms=5000)
    c.prepare()
    c2 = Coordinator(parts, st_backend, transaction_id=tid, timeout_ms=5000)
    st = c2.recover(tid)
    assert st.status == TransactionStatus.PREPARED


@settings(max_examples=150, deadline=None)
@given(st.integers(min_value=2, max_value=15))
def test_property_12_unique_transaction_ids(n: int) -> None:
    ids = {Coordinator([Yes()], _store(), timeout_ms=2000).transaction_id for _ in range(n)}
    assert len(ids) == n

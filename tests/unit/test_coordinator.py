"""Unit tests for Coordinator."""

from unittest.mock import MagicMock

import pytest

from iceguard.checkpoint_store import CheckpointStore
from iceguard.coordinator import Coordinator
from iceguard.enums import TransactionStatus
from iceguard.exceptions import CoordinatorTimeoutError


class _MemS3:
    def __init__(self):
        self.store: dict[str, bytes] = {}

    def put_object(self, **kwargs):
        self.store[kwargs["Key"]] = kwargs["Body"]

    def get_object(self, **kwargs):
        from botocore.exceptions import ClientError

        key = kwargs["Key"]
        if key not in self.store:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "n"}},
                "GetObject",
            )

        data = self.store[key]

        class B:
            def read(self_inner):
                return data if isinstance(data, bytes) else data.encode("utf-8")

        return {"Body": B()}

    def delete_object(self, **kwargs):
        self.store.pop(kwargs["Key"], None)


def _store():
    mem = _MemS3()
    client = MagicMock()
    client.put_object.side_effect = mem.put_object
    client.get_object.side_effect = mem.get_object
    client.delete_object.side_effect = mem.delete_object
    return CheckpointStore("b", "pfx/", s3_client=client)


class PYes:
    participant_id = "a"
    lambda_function_name = "fn"

    def prepare_vote(self):
        return "YES"

    def commit_phase(self):
        pass

    def abort_phase(self):
        pass


class PNo:
    participant_id = "b"
    lambda_function_name = "fn"

    def prepare_vote(self):
        return "NO"


def test_prepare_commit_happy_path():
    c = Coordinator([PYes(), PYes()], _store(), transaction_id="tid-1", timeout_ms=5000)
    st = c.prepare()
    assert st.status == TransactionStatus.PREPARED
    st2 = c.commit()
    assert st2.status == TransactionStatus.COMMITTED


def test_prepare_any_no_aborts():
    c = Coordinator([PYes(), PNo()], _store(), transaction_id="tid-2", timeout_ms=5000)
    st = c.prepare()
    assert st.status == TransactionStatus.ABORTED


def test_participant_timeout():
    class PSlow:
        participant_id = "s"
        lambda_function_name = "fn"

        def prepare_vote(self):
            import time

            time.sleep(2)
            return "YES"

    c = Coordinator([PSlow()], _store(), transaction_id="tid-3", timeout_ms=50)
    with pytest.raises(CoordinatorTimeoutError):
        c.prepare()


def test_recover_roundtrip():
    st_backend = _store()
    c = Coordinator([PYes()], st_backend, transaction_id="tid-4", timeout_ms=5000)
    c.prepare()
    c2 = Coordinator([PYes()], st_backend, transaction_id="tid-4", timeout_ms=5000)
    recovered = c2.recover("tid-4")
    assert recovered.transaction_id == "tid-4"
    assert recovered.status == TransactionStatus.PREPARED

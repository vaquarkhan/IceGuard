"""S3 leader lock tests."""

from unittest.mock import MagicMock

from iceguard.coordinator_leader import S3LeaderLock


def test_leader_lock_acquire_and_release():
    store = MagicMock()
    stored: dict[str, str] = {}

    def save_doc(key, body, fail_open=True):
        stored[key] = body

    def load_doc(key):
        return stored.get(key)

    store.save_document.side_effect = save_doc
    store.load_document.side_effect = load_doc

    lock = S3LeaderLock(store, "txn-1", "owner-a", lease_seconds=60)
    assert lock.acquire() is True
    lock.release()
    store.delete.assert_called()

"""S3-based leader election for multi-Lambda coordinator."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from botocore.exceptions import ClientError

from iceguard.checkpoint_store import CheckpointStore

logger = logging.getLogger(__name__)


class S3LeaderLock:
    """Acquire a coordinator leader lease via conditional S3 object semantics.

    Uses put-then-verify pattern: writer stores ``owner_id`` and lease expiry epoch.
    If the object exists and lease is valid, acquire fails unless same owner renews.
    """

    def __init__(
        self,
        store: CheckpointStore,
        lock_key: str,
        owner_id: str,
        *,
        lease_seconds: int = 30,
    ) -> None:
        self._store = store
        self._lock_key = f"locks/{lock_key.lstrip('/')}"
        self._owner_id = owner_id
        self._lease_seconds = max(5, lease_seconds)

    def _lease_deadline(self) -> int:
        return int(time.time()) + self._lease_seconds

    def _parse_body(self, body: str) -> tuple[str, int]:
        parts = body.strip().split("|", 1)
        if len(parts) != 2:
            return "", 0
        return parts[0], int(parts[1])

    def acquire(self) -> bool:
        """Try to become leader; return True if this owner holds the lease."""
        now = int(time.time())
        existing = self._store.load_document(self._lock_key)
        if existing:
            owner, expiry = self._parse_body(existing)
            if owner == self._owner_id:
                self._write_lease()
                return True
            if expiry > now:
                return False

        self._write_lease()
        verify = self._store.load_document(self._lock_key)
        if not verify:
            return False
        owner, _ = self._parse_body(verify)
        return owner == self._owner_id

    def _write_lease(self) -> None:
        payload = f"{self._owner_id}|{self._lease_deadline()}"
        self._store.save_document(self._lock_key, payload, fail_open=False)

    def release(self) -> None:
        """Release lock if held by this owner."""
        existing = self._store.load_document(self._lock_key)
        if not existing:
            return
        owner, _ = self._parse_body(existing)
        if owner != self._owner_id:
            return
        try:
            self._store.delete(self._lock_key)
        except Exception as e:
            logger.warning("Leader lock release failed: %s", e)

    def renew(self) -> bool:
        """Extend lease if already leader."""
        return self.acquire()

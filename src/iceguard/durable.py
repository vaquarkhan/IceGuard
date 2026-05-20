"""Bridge IceGuard checkpoints to AWS Lambda Durable Execution checkpoints."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from iceguard.checkpoint_store import CheckpointStore
from iceguard.models import CheckpointData

logger = logging.getLogger(__name__)


class DurableCheckpointBridge:
    """Mirror S3 checkpoints into Lambda durable execution state when available.

    AWS Lambda Durable Functions expose a ``checkpoint()`` API on the execution
    context. This bridge writes the same payload to S3 (for cross-invocation
    resume) and to the durable checkpoint (for in-flight replay semantics).

    If ``durable_context`` does not implement ``checkpoint``, only S3 is used.
    """

    def __init__(
        self,
        checkpoint_store: CheckpointStore,
        durable_context: Optional[Any] = None,
    ) -> None:
        self._store = checkpoint_store
        self._durable = durable_context

    def save(self, idempotency_key: str, data: CheckpointData) -> None:
        self._store.save(idempotency_key, data)
        if self._durable is None:
            return
        checkpoint_fn = getattr(self._durable, "checkpoint", None)
        if not callable(checkpoint_fn):
            return
        try:
            checkpoint_fn(data.to_json().encode("utf-8"))
        except Exception as e:
            logger.warning("Durable checkpoint mirror failed (S3 still saved): %s", e)

    def load(self, idempotency_key: str) -> Optional[CheckpointData]:
        loaded = self._store.load(idempotency_key)
        if loaded is not None:
            return loaded
        if self._durable is None:
            return None
        restore_fn = getattr(self._durable, "restore_checkpoint", None)
        if not callable(restore_fn):
            return None
        try:
            raw = restore_fn()
            if not raw:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            if isinstance(raw, str):
                return CheckpointData.from_json(raw)
            return CheckpointData.from_json(json.dumps(raw))
        except Exception as e:
            logger.warning("Durable checkpoint restore failed: %s", e)
            return None

    def clear_durable_checkpoint(self) -> None:
        """Clear durable execution checkpoint after successful write completion."""
        if self._durable is None:
            return
        for method_name in ("clear_checkpoint", "reset_checkpoint", "checkpoint_reset"):
            fn = getattr(self._durable, method_name, None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    logger.warning("Durable checkpoint clear via %s failed: %s", method_name, e)
                return

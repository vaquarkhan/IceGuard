"""Two-phase commit coordinator for multi-Lambda writes."""

from __future__ import annotations

import concurrent.futures
import logging
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, List, Optional

from iceguard.checkpoint_store import CheckpointStore
from iceguard.enums import TransactionStatus
from iceguard.exceptions import CheckpointCorruptionError, CoordinatorTimeoutError
from iceguard.metrics import MetricsEmitter
from iceguard.models import ParticipantState, TransactionState

logger = logging.getLogger(__name__)


class Coordinator:
    """Coordinates prepare/commit/abort across participants with persisted state."""

    def __init__(
        self,
        participants: List[Any],
        checkpoint_store: CheckpointStore,
        *,
        transaction_id: Optional[str] = None,
        timeout_ms: int = 60000,
        metrics_emitter: Optional[MetricsEmitter] = None,
        coordinator_lambda: str = "coordinator",
        state_key_prefix: str = "coord/",
    ) -> None:
        if not participants:
            raise ValueError("participants must be non-empty")
        self._participants = list(participants)
        self._store = checkpoint_store
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self._timeout_ms = timeout_ms
        self._metrics = metrics_emitter
        self._coordinator_lambda = coordinator_lambda
        self._prefix = state_key_prefix
        self._state: Optional[TransactionState] = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _doc_key(self, tid: Optional[str] = None) -> str:
        tid = tid or self.transaction_id
        return f"{self._prefix}{tid}.json"

    def _persist(self, state: TransactionState) -> None:
        self._store.save_document(self._doc_key(state.transaction_id), state.to_json())
        self._state = state

    def _initial_participants(self) -> List[ParticipantState]:
        return [
            ParticipantState(
                participant_id=str(getattr(p, "participant_id", f"p{i}")),
                lambda_function_name=str(
                    getattr(p, "lambda_function_name", "lambda-unknown")
                ),
                vote=None,
                phase1_complete=False,
                phase2_complete=False,
                last_heartbeat=self._now(),
            )
            for i, p in enumerate(self._participants)
        ]

    def _bootstrap_state(self) -> TransactionState:
        return TransactionState(
            transaction_id=self.transaction_id,
            status=TransactionStatus.INITIATED,
            participants=self._initial_participants(),
            created_at=self._now(),
            updated_at=self._now(),
            coordinator_lambda=self._coordinator_lambda,
            timeout_ms=self._timeout_ms,
        )

    def _load_state(self, tid: str) -> Optional[TransactionState]:
        raw = self._store.load_document(self._doc_key(tid))
        if raw is None:
            return None
        path = f"s3://checkpoint/{self._doc_key(tid)}"
        return TransactionState.from_json(raw, file_path=path)

    def recover(self, transaction_id: str) -> TransactionState:
        """Load persisted coordinator state for recovery."""
        st = self._load_state(transaction_id)
        if st is None:
            raise CheckpointCorruptionError(
                self._doc_key(transaction_id), "missing coordinator transaction document"
            )
        self.transaction_id = transaction_id
        self._state = st
        return st

    def _call_vote(self, participant: Any, participant_id: str) -> str:
        prepare = getattr(participant, "prepare_vote", None)
        if prepare is None:
            prepare = getattr(participant, "prepare", None)
        if prepare is None:
            return "YES"

        timeout_s = max(self._timeout_ms / 1000.0, 0.001)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(prepare)
            try:
                result = fut.result(timeout=timeout_s)
            except concurrent.futures.TimeoutError as e:
                raise CoordinatorTimeoutError(participant_id, self._timeout_ms) from e
        vote = str(result).upper()
        if vote not in ("YES", "NO"):
            return "YES"
        return vote

    def _finalize_abort(self, outcome: str = "aborted") -> TransactionState:
        assert self._state is not None
        state = replace(
            self._state,
            status=TransactionStatus.ABORTING,
            updated_at=self._now(),
        )
        self._persist(state)
        self._notify_abort()
        state = replace(
            state,
            status=TransactionStatus.ABORTED,
            updated_at=self._now(),
        )
        self._persist(state)
        if self._metrics:
            self._metrics.emit_coordination_outcome(
                self.transaction_id, outcome, len(self._participants)
            )
        return state

    def prepare(self) -> TransactionState:
        """Phase 1: collect votes; PREPARED or ABORTED."""
        state = self._load_state(self.transaction_id) or self._bootstrap_state()
        state = replace(
            state,
            status=TransactionStatus.PREPARING,
            updated_at=self._now(),
        )
        self._persist(state)

        updated_parts: List[ParticipantState] = []
        try:
            for p, ps in zip(self._participants, state.participants):
                pid = ps.participant_id
                vote = self._call_vote(p, pid)
                updated_parts.append(
                    replace(
                        ps,
                        vote=vote,
                        phase1_complete=True,
                        last_heartbeat=self._now(),
                    )
                )
                if vote != "YES":
                    state = replace(
                        state,
                        participants=updated_parts
                        + list(state.participants[len(updated_parts) :]),
                        updated_at=self._now(),
                    )
                    self._persist(state)
                    return self._finalize_abort("aborted")
        except CoordinatorTimeoutError:
            state = replace(
                state,
                participants=updated_parts
                + list(state.participants[len(updated_parts) :]),
                updated_at=self._now(),
            )
            self._persist(state)
            self._finalize_abort("aborted_timeout")
            raise

        state = replace(
            state,
            participants=updated_parts,
            status=TransactionStatus.PREPARED,
            updated_at=self._now(),
        )
        self._persist(state)
        return state

    def _notify_abort(self) -> None:
        for p in self._participants:
            fn = getattr(p, "abort_phase", None) or getattr(p, "abort", None)
            if fn is not None:
                try:
                    fn()
                except Exception as e:
                    logger.warning("Participant abort failed: %s", e)

    def commit(self) -> TransactionState:
        """Phase 2: commit all participants."""
        state = self._state or self._load_state(self.transaction_id)
        if state is None:
            state = self._bootstrap_state()
        if state.status != TransactionStatus.PREPARED:
            raise RuntimeError(f"cannot commit from status {state.status}")

        state = replace(
            state,
            status=TransactionStatus.COMMITTING,
            updated_at=self._now(),
        )
        self._persist(state)

        new_parts: List[ParticipantState] = []
        try:
            for p, ps in zip(self._participants, state.participants):
                fn = getattr(p, "commit_phase", None) or getattr(p, "commit", None)
                if fn is not None:
                    timeout_s = max(self._timeout_ms / 1000.0, 0.001)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        fut = pool.submit(fn)
                        try:
                            fut.result(timeout=timeout_s)
                        except concurrent.futures.TimeoutError as e:
                            raise CoordinatorTimeoutError(
                                ps.participant_id, self._timeout_ms
                            ) from e
                new_parts.append(
                    replace(ps, phase2_complete=True, last_heartbeat=self._now())
                )
        except Exception:
            self.abort()
            raise

        state = replace(
            state,
            participants=new_parts,
            status=TransactionStatus.COMMITTED,
            updated_at=self._now(),
        )
        self._persist(state)
        if self._metrics:
            self._metrics.emit_coordination_outcome(
                self.transaction_id, "committed", len(self._participants)
            )
        return state

    def abort(self) -> None:
        """Abort all participants and persist ABORTED when possible."""
        state = self._state or self._load_state(self.transaction_id)
        if state is None:
            state = self._bootstrap_state()
        if state.status in (TransactionStatus.ABORTED, TransactionStatus.COMMITTED):
            return
        state = replace(
            state,
            status=TransactionStatus.ABORTING,
            updated_at=self._now(),
        )
        self._persist(state)
        self._notify_abort()
        state = replace(
            state,
            status=TransactionStatus.ABORTED,
            updated_at=self._now(),
        )
        self._persist(state)
        if self._metrics:
            self._metrics.emit_coordination_outcome(
                self.transaction_id, "aborted", len(self._participants)
            )

# Formal verification: exactly-once semantics

IceGuard targets **effectively-once** visible writes under Lambda failure: readers never observe partial commits, and retries do not double-apply committed data.

## State machine

States: `ARMED`, `WRITING`, `CHECKPOINTED`, `ROLLING_BACK`, `COMPLETE`.

| Transition | Guard | Action |
|------------|-------|--------|
| ARMED → WRITING | time > threshold | start chunk |
| WRITING → CHECKPOINTED | chunk ok | persist offset + manifest |
| WRITING → ROLLING_BACK | rollback event | delete uncommitted paths |
| CHECKPOINTED → WRITING | offset < total | next chunk |
| CHECKPOINTED → COMPLETE | offset == total | delete checkpoint |

## Invariants

1. **Monotonic offset:** `record_offset` in checkpoint never decreases for a fixed `idempotency_key`.
2. **Manifest ⊆ storage:** Every path in `file_manifest` was produced by a completed chunk.
3. **Rollback closure:** On rollback, all paths in manifest ∪ `track_paths` for incomplete chunk are deleted or abort is invoked.
4. **Idempotency:** Re-invocation with same key resumes at `record_offset` without re-writing `[0, offset)`.

## TLA+ sketch

```
VARIABLES offset, rollback, committed

Init == offset = 0 /\ rollback = FALSE /\ committed = FALSE

WriteChunk == /\ ~rollback
              /\ offset' = offset + chunk_size
              /\ UNCHANGED <<rollback, committed>>

Rollback == /\ rollback'
             /\ offset' = offset
             /\ committed' = FALSE

Resume == offset > 0 => WriteChunk starts at offset

Spec == Init /\ [][WriteChunk \/ Rollback]_<<offset, rollback, committed>>
```

Full TLA+ model: contribute under `docs/tla/` if you need machine-checked proofs.

## Test evidence

- Property tests: checkpoint count vs interval (Hypothesis)
- Integration: `tests/integration/test_fault_injection.py` — rollback deletes tracked S3 paths
- Optional: `pytest -m spark` with local PySpark chunking

This is **not** a substitute for your table format's own ACID guarantees; IceGuard coordinates chunking + cleanup around format commits you perform per chunk.

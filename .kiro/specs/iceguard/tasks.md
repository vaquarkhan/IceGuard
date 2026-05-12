# Implementation Plan: IceGuard

## Overview

IceGuard is implemented as a Python library with incremental component development. The plan starts with project scaffolding and configuration, builds core components (watchdog, checkpoint store), then layers on higher-level features (SafeWriter, orphan scanner, coordinator, metrics), and finishes with integration wiring. Property-based tests using Hypothesis validate correctness properties alongside each component.

## Tasks

- [x] 1. Project setup and core data models
  - [x] 1.1 Initialize project structure with pyproject.toml, src layout, and test directories
    - Create `src/iceguard/` package with `__init__.py`
    - Create `pyproject.toml` with dependencies: boto3, hypothesis (dev), pytest (dev)
    - Create `tests/unit/`, `tests/property/`, `tests/integration/` directories with `conftest.py`
    - Configure Python 3.9–3.12 compatibility
    - _Requirements: 2.4, 2.5_

  - [x] 1.2 Implement error hierarchy and enums
    - Create `src/iceguard/exceptions.py` with all exception classes: `IceGuardError`, `IceGuardInitializationError`, `IceGuardContextError`, `IceGuardConfigError`, `IceGuardRollbackError`, `CheckpointCorruptionError`, `CoordinatorTimeoutError`
    - Create `src/iceguard/enums.py` with `TableFormat` and `TransactionStatus` enums
    - _Requirements: 1.7, 2.6, 7.4, 8.2, 8.4_

  - [x] 1.3 Implement IceGuardConfig dataclass with validation
    - Create `src/iceguard/config.py` with `IceGuardConfig` frozen dataclass
    - Implement `__post_init__` validation: rollback_threshold_ms in [5000, 300000], table_format in supported set, all fields validated
    - Raise `IceGuardConfigError` with descriptive messages on invalid values
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x]* 1.4 Write property tests for configuration validation
    - **Property 13: Configuration validation — threshold range**
    - **Property 14: Configuration validation — table format**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

  - [x] 1.5 Implement data models for CheckpointData, FileEntry, TransactionState, ParticipantState, and metric dataclasses
    - Create `src/iceguard/models.py` with all dataclass definitions
    - Include JSON serialization/deserialization methods on `CheckpointData` and `TransactionState`
    - _Requirements: 7.1, 7.2, 7.3, 5.6_

- [x] 2. Checkpoint Store
  - [x] 2.1 Implement CheckpointStore with S3 Express One Zone backend
    - Create `src/iceguard/checkpoint_store.py`
    - Implement `save()`, `load()`, `delete()`, `health_check()` methods
    - Serialize CheckpointData to JSON for persistence
    - Raise `CheckpointCorruptionError` on malformed JSON during deserialization
    - Implement `health_check()` with configurable timeout (default 5000ms)
    - _Requirements: 3.1, 3.5, 7.1, 7.4, 8.5, 8.6_

  - [x]* 2.2 Write property tests for checkpoint serialization
    - **Property 2: Checkpoint serialization round-trip**
    - **Validates: Requirements 7.1, 7.2, 7.3**

  - [x]* 2.3 Write property test for malformed JSON handling
    - **Property 3: Malformed JSON raises CheckpointCorruptionError**
    - **Validates: Requirements 7.4**

  - [x]* 2.4 Write unit tests for CheckpointStore
    - Test save/load/delete operations with mocked S3 client
    - Test health_check timeout behavior
    - Test fail-open behavior when S3 is unreachable during writes
    - _Requirements: 3.5, 3.6, 8.5, 8.6_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Watchdog Thread
  - [x] 4.1 Implement WatchdogThread with daemon thread and rollback signaling
    - Create `src/iceguard/watchdog.py`
    - Implement daemon thread that polls `lambda_context.get_remaining_time_in_millis()` at configurable interval (default 500ms, max 1000ms)
    - Use `threading.Event` for disarm signaling and `threading.Lock` for single-invocation callback guarantee
    - Implement `start()`, `disarm()`, `is_armed()` methods
    - Ensure <100ms overhead on the write path
    - _Requirements: 1.1, 1.2, 1.5, 1.6_

  - [x]* 4.2 Write property test for watchdog rollback trigger
    - **Property 1: Watchdog rollback trigger**
    - **Validates: Requirements 1.2**

  - [x]* 4.3 Write unit tests for WatchdogThread
    - Test watchdog spawns and polls at correct interval
    - Test disarm stops polling within 500ms
    - Test callback invoked exactly once when threshold breached
    - Test daemon thread behavior (auto-cleanup on main thread exit)
    - _Requirements: 1.1, 1.5, 1.6, 1.7_

- [x] 5. Metrics Emitter
  - [x] 5.1 Implement MetricsEmitter with CloudWatch publishing
    - Create `src/iceguard/metrics.py`
    - Implement `emit_write_outcome()`, `emit_near_miss()`, `emit_orphan_scan()`, `emit_checkpoint_resume()`, `emit_coordination_outcome()` methods
    - Use `iceguard` namespace for all CloudWatch metrics
    - Implement fire-and-forget pattern: catch all exceptions internally, log failures, never interrupt write path
    - Include all required dimensions: table name, table format, outcome, function name
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x]* 5.2 Write property tests for metrics emitter
    - **Property 15: Write metric dimensions completeness**
    - **Property 16: Rollback metric records exact remaining time**
    - **Property 17: Resume metric records exact skip count**
    - **Validates: Requirements 6.1, 6.3, 6.5**

  - [x]* 5.3 Write unit tests for MetricsEmitter
    - Test CloudWatch publish failure does not raise exceptions
    - Test correct namespace and dimensions on each metric type
    - _Requirements: 6.6, 6.7_

- [x] 6. Table Format Adapters
  - [x] 6.1 Implement TableFormatAdapter protocol and Iceberg/Delta adapters
    - Create `src/iceguard/adapters.py`
    - Define `TableFormatAdapter` protocol with `abort_transaction()`, `delete_uncommitted_files()`, `list_committed_files()`, `get_table_metadata_path()`
    - Implement `IcebergAdapter` with Iceberg-native transaction abort and file deletion
    - Implement `DeltaLakeAdapter` with Delta-native transaction abort and file deletion
    - _Requirements: 1.3, 1.4, 4.4_

  - [x]* 6.2 Write unit tests for table format adapters
    - Test Iceberg adapter abort and file deletion
    - Test Delta Lake adapter abort and file deletion
    - Test list_committed_files returns correct file sets
    - _Requirements: 1.3, 1.4, 4.4_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Orphan Scanner
  - [x] 8.1 Implement OrphanScanner with batched processing
    - Create `src/iceguard/orphan_scanner.py`
    - Implement `scan()` method: list all Parquet files, compare against committed files via adapter, classify orphans by retention period
    - Implement `delete_orphans()` method with error handling for permission denied (log and continue)
    - Process files in batches of ≤1000 per API call
    - Emit summary metrics via MetricsEmitter after scan completion
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x]* 8.2 Write property tests for orphan scanner
    - **Property 6: Orphan file classification**
    - **Property 7: Orphan scan batch size invariant**
    - **Property 8: Orphan scan metric accuracy**
    - **Validates: Requirements 4.1, 4.2, 4.6, 4.7**

  - [x]* 8.3 Write unit tests for OrphanScanner
    - Test file classification with various ages and committed sets
    - Test permission denied error handling (log and continue)
    - Test batch processing with >1000 files
    - _Requirements: 4.1, 4.2, 4.5, 4.7_

- [x] 9. Coordinator
  - [x] 9.1 Implement Coordinator with two-phase commit protocol
    - Create `src/iceguard/coordinator.py`
    - Implement state machine: INITIATED → PREPARING → PREPARED → COMMITTING → COMMITTED (or ABORTING → ABORTED)
    - Implement `prepare()`: collect votes from all participants, abort on any NO/timeout
    - Implement `commit()`: instruct all participants to commit Phase 2
    - Implement `abort()`: instruct all participants to roll back
    - Implement `recover()`: load transaction state from CheckpointStore for coordinator recovery
    - Assign unique transaction IDs (UUID4) to each coordinated write
    - Persist transaction state to CheckpointStore at each state transition
    - Emit coordination outcome metrics via MetricsEmitter
    - Configurable participant timeout (default 60000ms)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x]* 9.2 Write property tests for coordinator
    - **Property 9: Coordinator all-success triggers commit**
    - **Property 10: Coordinator any-failure triggers global abort**
    - **Property 11: Coordinator transaction state round-trip**
    - **Property 12: Coordinator unique transaction IDs**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6**

  - [x]* 9.3 Write unit tests for Coordinator
    - Test full happy-path state transitions
    - Test participant timeout triggers global abort
    - Test recovery from persisted state
    - Test metrics emission on commit and abort
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. SafeWriter (Core Context Manager)
  - [x] 11.1 Implement SafeWriter context manager with write orchestration
    - Create `src/iceguard/safe_writer.py`
    - Implement `__enter__`: validate config, check Lambda context, query checkpoint store for existing checkpoint, spawn watchdog thread
    - Implement `__exit__`: disarm watchdog, handle exceptions, emit metrics
    - Implement `write()`: execute write with checkpoint persistence at configured intervals, handle rollback signal from watchdog
    - On rollback signal: persist final checkpoint, call adapter's `abort_transaction()` and `delete_uncommitted_files()`, emit near-miss metric, raise `IceGuardRollbackError`
    - On success: disarm watchdog within 500ms, delete checkpoint, emit success metric
    - Raise `IceGuardInitializationError` if watchdog thread fails to spawn
    - Raise `IceGuardContextError` if Lambda context is missing/invalid
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.6, 3.1, 3.2, 3.3, 3.4, 3.6, 3.7_

  - [x]* 11.2 Write property tests for SafeWriter checkpoint behavior
    - **Property 4: Checkpoint resume processes only remaining records**
    - **Property 5: Checkpoint persistence at configured intervals**
    - **Validates: Requirements 3.1, 3.3, 3.4**

  - [x]* 11.3 Write unit tests for SafeWriter
    - Test context manager 2-line integration pattern
    - Test default threshold (30000ms) when not specified
    - Test custom threshold usage
    - Test watchdog disarm within 500ms after successful commit
    - Test checkpoint deletion after successful write
    - Test rollback path: final checkpoint persisted, files deleted, error raised
    - Test fail-open when checkpoint store unreachable
    - Test IceGuardInitializationError when watchdog fails to spawn
    - Test IceGuardContextError when Lambda context is invalid
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 2.1, 2.2, 2.3, 2.6, 3.2, 3.6, 3.7_

- [x] 12. Public API and module-level convenience function
  - [x] 12.1 Implement `iceguard.protect()` convenience function and package exports
    - Update `src/iceguard/__init__.py` with public API: `protect()` function, all exception classes, `IceGuardConfig`, `TableFormat` enum
    - Implement `protect()` function that constructs `SafeWriter` with sensible defaults
    - Ensure 2-line integration: `with iceguard.protect(context):` pattern works
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x]* 12.2 Write unit tests for public API
    - Test `protect()` creates SafeWriter with correct defaults
    - Test all public symbols are importable from `iceguard` package
    - _Requirements: 2.1, 2.4_

- [x] 13. Integration wiring and end-to-end tests
  - [x]* 13.1 Write integration tests for Iceberg rollback flow
    - Test abort transaction + delete uncommitted files with mocked Iceberg catalog
    - _Requirements: 1.3_

  - [x]* 13.2 Write integration tests for Delta Lake rollback flow
    - Test abort transaction + delete uncommitted files with mocked Delta log
    - _Requirements: 1.4_

  - [x]* 13.3 Write integration tests for checkpoint store with mocked S3
    - Test checkpoint read/write/delete cycle
    - Test connectivity health check timeout
    - _Requirements: 3.5, 8.5, 8.6_

  - [x]* 13.4 Write integration tests for coordinated multi-Lambda write
    - Test end-to-end two-phase commit with multiple mock participants
    - Test coordinator recovery after simulated timeout
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical boundaries
- Property tests validate the 17 correctness properties defined in the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.9+ with type hints throughout
- All S3 interactions should be abstracted behind interfaces for testability (use moto or unittest.mock in tests)

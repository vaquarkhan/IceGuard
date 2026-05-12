# Requirements Document

## Introduction

IceGuard is a production-grade Python reliability library that eliminates silent data loss in Spark-on-AWS-Lambda (SoAL) deployments. AWS Lambda can terminate containers with SIGKILL between Phase 1 (data upload to object storage) and Phase 2 (metadata commit to the table catalog), causing 100% silent data loss for open table format writes. IceGuard provides timeout-aware rollback, resumable checkpointing, orphan cleanup, multi-Lambda coordination, and observability to make SoAL safe for enterprise use.

## Glossary

- **SafeWriter**: The core wrapper component that monitors Lambda remaining execution time and triggers format-native rollback before SIGKILL termination occurs.
- **Watchdog_Thread**: A background thread spawned by SafeWriter that monitors `context.get_remaining_time_in_millis()` and arms rollback when remaining time drops below a configurable threshold.
- **Checkpoint_Store**: An S3 Express One Zone-backed persistence layer that stores partial write progress so subsequent Lambda invocations can resume from the last successful checkpoint.
- **Orphan_Scanner**: A background scanner component that detects and removes Parquet files from past failed writes that were never committed to the table metadata.
- **Coordinator**: The component responsible for atomic multi-Lambda commit orchestration using a two-phase commit protocol.
- **Metrics_Emitter**: The component that publishes write reliability metrics, near-miss alerts, orphan counts, and checkpoint status to Amazon CloudWatch.
- **SoAL**: Spark-on-AWS-Lambda — a framework that packages Apache Spark in Docker containers on AWS Lambda for small file processing.
- **Lambda_Context**: The AWS Lambda runtime context object that provides `get_remaining_time_in_millis()` for remaining execution time.
- **Rollback_Threshold**: The configurable time buffer (in milliseconds) before Lambda timeout at which SafeWriter triggers rollback. Default is 30000ms (30 seconds).
- **Table_Format**: An open table format for lakehouse storage; IceGuard supports Apache Iceberg and Delta Lake.
- **Commit_Protocol**: The two-phase write process consisting of Phase 1 (data file upload) and Phase 2 (metadata commit to catalog).
- **Orphan_File**: A Parquet data file that was uploaded during Phase 1 but whose corresponding Phase 2 metadata commit never completed.
- **Two_Phase_Commit**: A distributed coordination protocol where multiple Lambda participants vote to commit or abort, ensuring atomicity across parallel writers.
- **Near_Miss_Event**: An event where SafeWriter triggered rollback successfully, indicating the write would have suffered silent data loss without IceGuard.

## Requirements

### Requirement 1: Timeout-Aware Write Protection

**User Story:** As a data engineer, I want my Spark writes on Lambda to be automatically protected from SIGKILL-induced silent data loss, so that I can trust my data pipeline outputs without manual timeout management.

#### Acceptance Criteria

1. WHEN a write operation is initiated through SafeWriter, THE SafeWriter SHALL spawn a Watchdog_Thread that monitors Lambda_Context remaining execution time at intervals no greater than 1000ms.
2. WHEN the Watchdog_Thread detects that remaining execution time is less than or equal to the configured Rollback_Threshold, THE SafeWriter SHALL initiate format-native rollback for the active write operation.
3. WHEN SafeWriter initiates rollback for an Apache Iceberg write, THE SafeWriter SHALL abort the Iceberg transaction and delete all uncommitted data files uploaded during Phase 1.
4. WHEN SafeWriter initiates rollback for a Delta Lake write, THE SafeWriter SHALL abort the Delta transaction and delete all uncommitted data files uploaded during Phase 1.
5. WHILE a write operation is in progress, THE Watchdog_Thread SHALL add no more than 100ms of latency overhead to the write operation.
6. WHEN SafeWriter completes a write operation successfully (Phase 2 metadata commit finishes), THE SafeWriter SHALL disarm the Watchdog_Thread within 500ms.
7. IF the Watchdog_Thread fails to spawn, THEN THE SafeWriter SHALL raise an IceGuardInitializationError and prevent the write operation from proceeding.

### Requirement 2: Drop-In Integration

**User Story:** As a data engineer, I want to integrate IceGuard with minimal code changes, so that I can protect existing SoAL pipelines without rewriting them.

#### Acceptance Criteria

1. THE SafeWriter SHALL be activatable by wrapping an existing SparkSession write call with a single context manager (`with iceguard.protect(context):`) requiring no more than 2 lines of code change.
2. WHEN no explicit Rollback_Threshold is provided, THE SafeWriter SHALL use a default Rollback_Threshold of 30000ms.
3. WHEN a user provides a custom Rollback_Threshold via configuration, THE SafeWriter SHALL use the user-specified value.
4. THE SafeWriter SHALL be installable via `pip install iceguard` from PyPI.
5. THE SafeWriter SHALL support Python versions 3.9, 3.10, 3.11, and 3.12.
6. WHEN SafeWriter is initialized without a valid Lambda_Context, THE SafeWriter SHALL raise an IceGuardContextError with a descriptive message indicating that a Lambda execution context is required.

### Requirement 3: Resumable Checkpointing

**User Story:** As a data engineer, I want partial write progress to be saved so that the next Lambda invocation can continue where the previous one left off, so that large writes eventually complete even under tight timeout constraints.

#### Acceptance Criteria

1. WHILE a write operation is in progress, THE SafeWriter SHALL persist checkpoint metadata to the Checkpoint_Store at a configurable interval (default: every 5000 records processed).
2. WHEN a rollback is triggered by the Watchdog_Thread, THE SafeWriter SHALL persist a final checkpoint capturing all progress completed before rollback initiation.
3. WHEN a new write operation is initiated for the same logical write (identified by a user-provided idempotency key), THE SafeWriter SHALL query the Checkpoint_Store and resume from the last persisted checkpoint.
4. WHEN resuming from a checkpoint, THE SafeWriter SHALL skip records that were already committed in prior invocations and process only remaining records.
5. THE Checkpoint_Store SHALL use S3 Express One Zone for checkpoint persistence to minimize read/write latency.
6. IF the Checkpoint_Store is unreachable, THEN THE SafeWriter SHALL log a warning and proceed with a full write (no resume), rather than failing the operation.
7. WHEN a write operation completes successfully (Phase 2 commit finishes), THE SafeWriter SHALL delete the associated checkpoint data from the Checkpoint_Store within 60 seconds.

### Requirement 4: Orphan Detection and Cleanup

**User Story:** As a data engineer, I want orphaned data files from past failed writes to be automatically detected and cleaned up, so that I do not accumulate storage costs or risk data inconsistency from stale files.

#### Acceptance Criteria

1. WHEN the Orphan_Scanner is invoked, THE Orphan_Scanner SHALL list all Parquet files in the target table's data directory and compare them against committed file references in the table metadata.
2. WHEN the Orphan_Scanner identifies a file that is not referenced by any committed table snapshot and is older than a configurable retention period (default: 72 hours), THE Orphan_Scanner SHALL classify that file as an Orphan_File.
3. WHEN the Orphan_Scanner classifies a file as an Orphan_File, THE Orphan_Scanner SHALL delete the Orphan_File from object storage.
4. THE Orphan_Scanner SHALL support scanning Apache Iceberg tables and Delta Lake tables.
5. IF the Orphan_Scanner encounters a file that cannot be deleted due to insufficient permissions, THEN THE Orphan_Scanner SHALL log an error with the file path and continue scanning remaining files.
6. WHEN the Orphan_Scanner completes a scan, THE Orphan_Scanner SHALL emit a summary metric to the Metrics_Emitter containing the count of orphan files found and the count of orphan files deleted.
7. THE Orphan_Scanner SHALL process files in batches of no more than 1000 files per API call to avoid Lambda memory exhaustion.

### Requirement 5: Multi-Lambda Coordination

**User Story:** As a data engineer, I want writes fanned out across multiple Lambda functions to commit atomically, so that partial commits from a subset of Lambdas do not leave my table in an inconsistent state.

#### Acceptance Criteria

1. WHEN a coordinated write is initiated, THE Coordinator SHALL assign a unique transaction identifier to all participating Lambda functions.
2. WHEN all participating Lambda functions report Phase 1 completion (data upload success), THE Coordinator SHALL instruct all participants to proceed with Phase 2 (metadata commit).
3. IF any participating Lambda function reports Phase 1 failure or timeout, THEN THE Coordinator SHALL instruct all participants to abort and roll back their uploaded data files.
4. WHEN the Coordinator instructs participants to commit, THE Coordinator SHALL use a Two_Phase_Commit protocol with a prepare phase and a commit phase.
5. IF a participant fails to respond to the Coordinator within a configurable timeout (default: 60 seconds), THEN THE Coordinator SHALL treat the non-responsive participant as failed and initiate a global abort.
6. THE Coordinator SHALL persist transaction state to the Checkpoint_Store so that coordinator recovery is possible if the coordinator Lambda itself times out.
7. WHEN a coordinated transaction completes (commit or abort), THE Coordinator SHALL emit the transaction outcome and participant count to the Metrics_Emitter.

### Requirement 6: Observability and Metrics

**User Story:** As a data engineer, I want real-time visibility into write reliability, near-miss events, and orphan status, so that I can monitor pipeline health and respond to degradation proactively.

#### Acceptance Criteria

1. WHEN a write operation completes (success or rollback), THE Metrics_Emitter SHALL publish a CloudWatch metric with dimensions including table name, table format, outcome (success/rollback), and Lambda function name.
2. WHEN the Watchdog_Thread triggers a rollback, THE Metrics_Emitter SHALL publish a Near_Miss_Event metric indicating that silent data loss was prevented.
3. THE Metrics_Emitter SHALL publish a metric recording the remaining execution time at the moment rollback was triggered, with millisecond precision.
4. WHEN the Orphan_Scanner completes a scan, THE Metrics_Emitter SHALL publish metrics for orphan files found, orphan files deleted, and total orphan file size in bytes.
5. WHEN a checkpoint resume occurs, THE Metrics_Emitter SHALL publish a metric indicating the number of records skipped due to prior checkpoint progress.
6. THE Metrics_Emitter SHALL publish all metrics to Amazon CloudWatch using the `iceguard` namespace.
7. IF the Metrics_Emitter fails to publish a metric to CloudWatch, THEN THE Metrics_Emitter SHALL log the failure and continue operation without interrupting the write path.

### Requirement 7: Serialization Round-Trip Integrity

**User Story:** As a data engineer, I want checkpoint data to be serialized and deserialized without loss, so that resumed writes produce identical results to uninterrupted writes.

#### Acceptance Criteria

1. THE Checkpoint_Store SHALL serialize checkpoint metadata to JSON format.
2. FOR ALL valid checkpoint metadata objects, serializing to JSON then deserializing back SHALL produce an object equivalent to the original (round-trip property).
3. WHEN checkpoint metadata contains record offsets, partition information, and file manifests, THE Checkpoint_Store SHALL preserve all fields with exact values through serialization and deserialization.
4. IF the Checkpoint_Store encounters malformed JSON during deserialization, THEN THE Checkpoint_Store SHALL raise a CheckpointCorruptionError with the file path and a description of the parsing failure.

### Requirement 8: Configuration Validation

**User Story:** As a data engineer, I want IceGuard to validate my configuration at initialization time, so that misconfigurations are caught early rather than causing failures mid-write.

#### Acceptance Criteria

1. WHEN SafeWriter is initialized, THE SafeWriter SHALL validate that the Rollback_Threshold is between 5000ms and 300000ms (inclusive).
2. IF the Rollback_Threshold is outside the valid range, THEN THE SafeWriter SHALL raise an IceGuardConfigError specifying the provided value and the valid range.
3. WHEN SafeWriter is initialized, THE SafeWriter SHALL validate that the specified Table_Format is one of the supported formats (Apache Iceberg, Delta Lake).
4. IF an unsupported Table_Format is specified, THEN THE SafeWriter SHALL raise an IceGuardConfigError listing the supported formats.
5. WHEN the Checkpoint_Store is configured, THE SafeWriter SHALL validate connectivity to the S3 Express One Zone bucket within 5000ms of initialization.
6. IF the S3 Express One Zone bucket is not accessible within 5000ms, THEN THE SafeWriter SHALL raise an IceGuardConfigError indicating the bucket is unreachable.

"""IceGuard enumerations.

Defines the supported table formats and transaction status states
used throughout the library.
"""

from enum import Enum


class TableFormat(Enum):
    """Supported open table formats for lakehouse storage.

    IceGuard provides format-native rollback for each supported format,
    delegating abort and cleanup operations to the format's own APIs.
    """

    ICEBERG = "iceberg"
    DELTA = "delta"
    HUDI = "hudi"


class TransactionStatus(Enum):
    """States in the two-phase commit coordinator state machine.

    State transitions:
        INITIATED → PREPARING → PREPARED → COMMITTING → COMMITTED
        INITIATED → PREPARING → ABORTING → ABORTED
        INITIATED → PREPARING → PREPARED → COMMITTING → ABORTING → ABORTED
    """

    INITIATED = "INITIATED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"

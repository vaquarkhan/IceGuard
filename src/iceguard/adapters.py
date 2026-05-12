"""Table format adapters (Iceberg / Delta Lake)."""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Protocol, Set

logger = logging.getLogger(__name__)


class TableFormatAdapter(Protocol):
    """Protocol for table format-specific rollback and metadata queries."""

    def abort_transaction(self, transaction: Any) -> None:
        ...

    def delete_uncommitted_files(self, file_paths: List[str]) -> None:
        ...

    def list_committed_files(self, table_path: str) -> Set[str]:
        ...

    def get_table_metadata_path(self, table_path: str) -> str:
        ...


class IcebergAdapter:
    """Iceberg-oriented adapter.

    In production, wire ``catalog``/Spark table operations to real Iceberg APIs.
    For tests, ``committed_files`` seeds metadata-derived committed paths.
    """

    def __init__(
        self,
        *,
        committed_files: Optional[Set[str]] = None,
        catalog: Any = None,
    ) -> None:
        self._committed: Set[str] = set(committed_files or ())
        self._catalog = catalog
        self._deleted: List[str] = []
        self._active_transaction: Any = None

    @property
    def deleted_paths(self) -> List[str]:
        """Paths passed to delete_uncommitted_files (test hook)."""
        return list(self._deleted)

    def abort_transaction(self, transaction: Any) -> None:
        """Abort the active Iceberg transaction (format-native in production)."""
        if self._catalog is not None and hasattr(self._catalog, "abort_transaction"):
            self._catalog.abort_transaction(transaction)
        self._active_transaction = None

    def delete_uncommitted_files(self, file_paths: List[str]) -> None:
        """Remove uncommitted data files from storage."""
        if self._catalog is not None and hasattr(self._catalog, "delete_files"):
            self._catalog.delete_files(file_paths)
        self._deleted.extend(file_paths)

    def list_committed_files(self, table_path: str) -> Set[str]:
        """Return object storage paths referenced by committed metadata."""
        if self._catalog is not None and hasattr(self._catalog, "list_committed_files"):
            return set(self._catalog.list_committed_files(table_path))
        return set(self._committed)

    def get_table_metadata_path(self, table_path: str) -> str:
        root = table_path.rstrip("/")
        return f"{root}/metadata"


class DeltaLakeAdapter:
    """Delta Lake-oriented adapter."""

    def __init__(
        self,
        *,
        committed_files: Optional[Set[str]] = None,
        log: Any = None,
    ) -> None:
        self._committed: Set[str] = set(committed_files or ())
        self._log = log
        self._deleted: List[str] = []
        self._active_transaction: Any = None

    @property
    def deleted_paths(self) -> List[str]:
        return list(self._deleted)

    def abort_transaction(self, transaction: Any) -> None:
        if self._log is not None and hasattr(self._log, "abort_transaction"):
            self._log.abort_transaction(transaction)
        self._active_transaction = None

    def delete_uncommitted_files(self, file_paths: List[str]) -> None:
        if self._log is not None and hasattr(self._log, "delete_files"):
            self._log.delete_files(file_paths)
        self._deleted.extend(file_paths)

    def list_committed_files(self, table_path: str) -> Set[str]:
        if self._log is not None and hasattr(self._log, "list_committed_files"):
            return set(self._log.list_committed_files(table_path))
        return set(self._committed)

    def get_table_metadata_path(self, table_path: str) -> str:
        root = table_path.rstrip("/")
        return f"{root}/_delta_log"

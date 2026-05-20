"""Table format adapters (Iceberg / Delta Lake)."""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Protocol, Set

from iceguard.s3_ops import delete_s3_uri

logger = logging.getLogger(__name__)


def iceberg_adapter(
    *,
    catalog: Any = None,
    table_identifier: Optional[str] = None,
    committed_files: Optional[Set[str]] = None,
    s3_client: Any = None,
) -> "IcebergAdapter":
    """Build an :class:`IcebergAdapter` with optional PyIceberg committed-file discovery."""
    return IcebergAdapter(
        catalog=catalog,
        table_identifier=table_identifier,
        committed_files=committed_files,
        s3_client=s3_client,
    )


def delta_adapter(
    *,
    log: Any = None,
    committed_files: Optional[Set[str]] = None,
    s3_client: Any = None,
) -> "DeltaLakeAdapter":
    """Build a :class:`DeltaLakeAdapter` (wire ``log`` for Delta transaction APIs)."""
    return DeltaLakeAdapter(log=log, committed_files=committed_files, s3_client=s3_client)


def hudi_adapter(
    *,
    commit_client: Any = None,
    committed_files: Optional[Set[str]] = None,
    s3_client: Any = None,
) -> "HudiAdapter":
    """Build a :class:`HudiAdapter` (wire Spark Hudi commit client when available)."""
    return HudiAdapter(
        commit_client=commit_client,
        committed_files=committed_files,
        s3_client=s3_client,
    )


def _delete_paths_on_s3(file_paths: List[str], *, s3_client: Any = None) -> None:
    for path in file_paths:
        if not path.startswith("s3://"):
            continue
        try:
            delete_s3_uri(path, s3_client=s3_client)
        except Exception as e:
            logger.warning("S3 delete failed for %s: %s", path, e)


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
        table_identifier: Optional[str] = None,
        s3_client: Any = None,
    ) -> None:
        self._committed: Set[str] = set(committed_files or ())
        self._catalog = catalog
        self._table_identifier = table_identifier
        self._s3_client = s3_client
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
        else:
            _delete_paths_on_s3(file_paths, s3_client=self._s3_client)
        self._deleted.extend(file_paths)

    def list_committed_files(self, table_path: str) -> Set[str]:
        """Return object storage paths referenced by committed metadata."""
        if self._catalog is not None and hasattr(self._catalog, "list_committed_files"):
            return set(self._catalog.list_committed_files(table_path))
        if self._catalog is not None and self._table_identifier:
            try:
                from iceguard.catalog_integrations import pyiceberg_committed_paths

                return pyiceberg_committed_paths(self._catalog, self._table_identifier)
            except ImportError:
                logger.warning(
                    "table_identifier set but pyiceberg not installed; "
                    "orphan scan uses committed_files seed only"
                )
            except Exception as e:
                logger.warning("PyIceberg committed-file listing failed: %s", e)
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
        s3_client: Any = None,
    ) -> None:
        self._committed: Set[str] = set(committed_files or ())
        self._log = log
        self._s3_client = s3_client
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
        else:
            _delete_paths_on_s3(file_paths, s3_client=self._s3_client)
        self._deleted.extend(file_paths)

    def list_committed_files(self, table_path: str) -> Set[str]:
        if self._log is not None and hasattr(self._log, "list_committed_files"):
            return set(self._log.list_committed_files(table_path))
        if table_path.startswith("s3://"):
            try:
                from iceguard.format_metadata import delta_committed_paths_s3

                return delta_committed_paths_s3(table_path, s3_client=self._s3_client)
            except Exception as e:
                logger.warning("Delta S3 metadata read failed: %s", e)
        return set(self._committed)

    def get_table_metadata_path(self, table_path: str) -> str:
        root = table_path.rstrip("/")
        return f"{root}/_delta_log"


class HudiAdapter:
    """Apache Hudi-oriented adapter."""

    def __init__(
        self,
        *,
        committed_files: Optional[Set[str]] = None,
        commit_client: Any = None,
        s3_client: Any = None,
    ) -> None:
        self._committed: Set[str] = set(committed_files or ())
        self._commit_client = commit_client
        self._s3_client = s3_client
        self._deleted: List[str] = []
        self._active_transaction: Any = None

    @property
    def deleted_paths(self) -> List[str]:
        return list(self._deleted)

    def abort_transaction(self, transaction: Any) -> None:
        if self._commit_client is not None and hasattr(
            self._commit_client, "abort_transaction"
        ):
            self._commit_client.abort_transaction(transaction)
        self._active_transaction = None

    def delete_uncommitted_files(self, file_paths: List[str]) -> None:
        if self._commit_client is not None and hasattr(self._commit_client, "delete_files"):
            self._commit_client.delete_files(file_paths)
        else:
            _delete_paths_on_s3(file_paths, s3_client=self._s3_client)
        self._deleted.extend(file_paths)

    def list_committed_files(self, table_path: str) -> Set[str]:
        if self._commit_client is not None and hasattr(
            self._commit_client, "list_committed_files"
        ):
            return set(self._commit_client.list_committed_files(table_path))
        if table_path.startswith("s3://"):
            try:
                from iceguard.format_metadata import hudi_committed_paths_s3

                return hudi_committed_paths_s3(table_path, s3_client=self._s3_client)
            except Exception as e:
                logger.warning("Hudi S3 metadata read failed: %s", e)
        return set(self._committed)

    def get_table_metadata_path(self, table_path: str) -> str:
        root = table_path.rstrip("/")
        return f"{root}/.hoodie"

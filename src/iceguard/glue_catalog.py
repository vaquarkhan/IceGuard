"""AWS Glue Data Catalog integration for Iceberg tables."""

from __future__ import annotations

import logging
from typing import Any, Optional, Set

from iceguard.adapters import IcebergAdapter

logger = logging.getLogger(__name__)


class GlueCatalogAdapter(IcebergAdapter):
    """Iceberg adapter backed by AWS Glue Data Catalog."""

    def __init__(
        self,
        database: str,
        table_name: str,
        *,
        glue_client: Optional[Any] = None,
        catalog: Any = None,
        s3_client: Any = None,
    ) -> None:
        table_identifier = f"{database}.{table_name}"
        super().__init__(
            catalog=catalog,
            table_identifier=table_identifier,
            s3_client=s3_client,
        )
        self._database = database
        self._table_name = table_name
        if glue_client is not None:
            self._glue = glue_client
        else:
            import boto3

            self._glue = boto3.client("glue")
        self._table_location: Optional[str] = None

    def _resolve_table_location(self) -> str:
        if self._table_location:
            return self._table_location
        resp = self._glue.get_table(DatabaseName=self._database, Name=self._table_name)
        table = resp["Table"]
        location = table["StorageDescriptor"]["Location"].rstrip("/")
        params = table.get("Parameters") or {}
        metadata_location = params.get("metadata_location") or params.get(
            "table_type"
        )
        if metadata_location and metadata_location.startswith("s3://"):
            self._table_location = metadata_location.rsplit("/metadata", 1)[0]
        else:
            self._table_location = location
        return self._table_location

    def list_committed_files(self, table_path: str) -> Set[str]:
        if self._catalog is not None and self._table_identifier:
            try:
                return super().list_committed_files(table_path)
            except Exception as e:
                logger.warning("Glue catalog PyIceberg listing failed: %s", e)
        location = self._resolve_table_location()
        return super().list_committed_files(location or table_path)


def glue_adapter(
    database: str,
    table_name: str,
    *,
    catalog: Any = None,
    glue_client: Any = None,
    s3_client: Any = None,
) -> GlueCatalogAdapter:
    """Build a Glue-backed Iceberg adapter."""
    return GlueCatalogAdapter(
        database,
        table_name,
        catalog=catalog,
        glue_client=glue_client,
        s3_client=s3_client,
    )

"""Glue catalog adapter tests."""

from unittest.mock import MagicMock

from iceguard.glue_catalog import glue_adapter


def test_glue_adapter_resolves_table_location():
    glue = MagicMock()
    glue.get_table.return_value = {
        "Table": {
            "StorageDescriptor": {"Location": "s3://lake/db/table/"},
            "Parameters": {
                "table_type": "ICEBERG",
                "metadata_location": "s3://lake/db/table/metadata/00001.metadata.json",
            },
        }
    }
    adapter = glue_adapter("db", "orders", glue_client=glue)
    loc = adapter._resolve_table_location()
    assert loc.startswith("s3://")

"""Spark write_dataframe validation."""

from unittest.mock import MagicMock

import pytest

from iceguard.spark_write import _write_spark_partition, write_dataframe


class _MockDataFrameWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def format(self, fmt: str) -> "_MockDataFrameWriter":
        self.calls.append(("format", fmt))
        return self

    def mode(self, mode: str) -> "_MockDataFrameWriter":
        self.calls.append(("mode", mode))
        return self

    def options(self, **kwargs: object) -> "_MockDataFrameWriter":
        self.calls.append(("options", str(kwargs)))
        return self

    def save(self, target: str) -> None:
        self.calls.append(("save", target))

    def insertInto(self, table: str) -> None:
        self.calls.append(("insertInto", table))


def _part_with_writer() -> MagicMock:
    part = MagicMock()
    part.write = _MockDataFrameWriter()
    return part


def test_write_spark_partition_uses_save_for_path():
    part = _part_with_writer()
    w = part.write
    _write_spark_partition(
        part,
        write_format="iceberg",
        write_mode="append",
        write_options={},
        path="s3://lake/db/table",
        table_identifier=None,
    )
    assert ("save", "s3://lake/db/table") in w.calls
    assert not any(c[0] == "insertInto" for c in w.calls)


def test_write_spark_partition_uses_insert_into_for_catalog():
    part = _part_with_writer()
    w = part.write
    _write_spark_partition(
        part,
        write_format="iceberg",
        write_mode="append",
        write_options={"merge-schema": "true"},
        path=None,
        table_identifier="glue_catalog.db.events",
    )
    assert ("insertInto", "glue_catalog.db.events") in w.calls
    assert not any(c[0] == "save" for c in w.calls)
    assert ("format", "iceberg") in w.calls


def test_write_spark_partition_prefers_insert_into_when_both_set():
    part = _part_with_writer()
    w = part.write
    _write_spark_partition(
        part,
        write_format="delta",
        write_mode="append",
        write_options={},
        path="s3://lake/db/table",
        table_identifier="spark_catalog.db.table",
    )
    assert ("insertInto", "spark_catalog.db.table") in w.calls
    assert not any(c[0] == "save" for c in w.calls)


def test_write_dataframe_requires_path_or_table_identifier():
    with pytest.raises(ValueError, match="path or table_identifier"):
        write_dataframe(
            object(),  # type: ignore[arg-type]
            None,
            path=None,
            table_identifier=None,
        )


def test_write_dataframe_rejects_overwrite_mode():
    with pytest.raises(ValueError, match="only supports write_mode='append'"):
        write_dataframe(
            object(),  # type: ignore[arg-type]
            None,
            "s3://lake/t",
            write_mode="overwrite",
        )

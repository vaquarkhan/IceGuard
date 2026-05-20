"""Spark write_dataframe validation."""

import pytest

from iceguard.spark_write import write_dataframe


def test_write_dataframe_rejects_overwrite_mode():
    writer = object()
    with pytest.raises(ValueError, match="only supports write_mode='append'"):
        write_dataframe(
            writer,  # type: ignore[arg-type]
            None,
            "s3://lake/t",
            write_mode="overwrite",
        )

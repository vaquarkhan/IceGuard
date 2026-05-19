"""Optional integrations with PyIceberg and similar catalog libraries."""

from __future__ import annotations

import logging
from typing import Any, Set

logger = logging.getLogger(__name__)


def pyiceberg_committed_paths(catalog: Any, table_identifier: str) -> Set[str]:
    """Return data file locations from the table's current Iceberg snapshot.

    Requires the ``pyiceberg`` package (``pip install iceguard[iceberg]``).
    """
    try:
        from pyiceberg.manifest import DataFile
    except ImportError as e:
        raise ImportError(
            "pyiceberg is required for committed-file discovery. "
            'Install with: pip install "iceguard[iceberg]"'
        ) from e

    table = catalog.load_table(table_identifier)
    snapshot = table.current_snapshot()
    if snapshot is None:
        return set()

    paths: Set[str] = set()
    io = table.io
    for manifest in snapshot.manifests(io):
        for entry in manifest.fetch_manifest_entry(io):
            data_file = getattr(entry, "data_file", None)
            if data_file is None:
                continue
            if isinstance(data_file, DataFile) or hasattr(data_file, "file_path"):
                loc = getattr(data_file, "file_path", None) or getattr(
                    data_file, "location", None
                )
                if loc:
                    paths.add(str(loc))
    return paths

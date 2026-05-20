"""Automatic S3 path tracking for chunked writes."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Set

from iceguard.s3_ops import list_parquet_candidates


def s3_track_paths_factory(
    table_path: str,
    *,
    s3_client: Optional[Any] = None,
) -> Callable[[int, int], List[str]]:
    """Return a ``track_paths`` callback that diffs Parquet objects before/after each chunk."""
    known: Set[str] = set()
    if table_path.startswith("s3://"):
        known = {uri for uri, _, _ in list_parquet_candidates(table_path, s3_client=s3_client)}

    def track_paths(_start: int, _end: int) -> List[str]:
        if not table_path.startswith("s3://"):
            return []
        current = {uri for uri, _, _ in list_parquet_candidates(table_path, s3_client=s3_client)}
        new_paths = sorted(current - known)
        known.update(current)
        return new_paths

    return track_paths

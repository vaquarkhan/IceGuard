"""Read committed data file paths from Delta / Hudi metadata on S3 (no Spark required)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, Set

from iceguard.s3_ops import parse_s3_uri

logger = logging.getLogger(__name__)


def _get_s3_client(s3_client: Optional[Any]) -> Any:
    if s3_client is not None:
        return s3_client
    import boto3

    return boto3.client("s3")


def _list_keys(bucket: str, prefix: str, *, s3_client: Any) -> list[str]:
    keys: list[str] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents") or []:
            keys.append(obj["Key"])
    return keys


def _read_object_text(bucket: str, key: str, *, s3_client: Any) -> str:
    body = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()
    return body.decode("utf-8", errors="replace")


def delta_committed_paths_s3(table_path: str, *, s3_client: Optional[Any] = None) -> Set[str]:
    """Parse Delta transaction log JSON on S3 and return active data file paths."""
    if not table_path.startswith("s3://"):
        return set()

    client = _get_s3_client(s3_client)
    bucket, table_prefix = parse_s3_uri(table_path.rstrip("/") + "/", directory_prefix=True)
    log_prefix = f"{table_prefix}_delta_log/"
    keys = sorted(k for k in _list_keys(bucket, log_prefix, s3_client=client) if k.endswith(".json"))

    active: Set[str] = set()
    for key in keys:
        try:
            text = _read_object_text(bucket, key, s3_client=client)
        except Exception as e:
            logger.warning("Failed reading delta log %s: %s", key, e)
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                action = json.loads(line)
            except json.JSONDecodeError:
                continue
            add = action.get("add")
            if add and "path" in add:
                path = add["path"]
                if not path.startswith("s3://"):
                    path = f"s3://{bucket}/{path.lstrip('/')}"
                active.add(path)
            remove = action.get("remove")
            if remove and "path" in remove:
                path = remove["path"]
                if not path.startswith("s3://"):
                    path = f"s3://{bucket}/{path.lstrip('/')}"
                active.discard(path)


    return active


def hudi_committed_paths_s3(table_path: str, *, s3_client: Optional[Any] = None) -> Set[str]:
    """Extract committed file paths from Hudi timeline commits on S3."""
    if not table_path.startswith("s3://"):
        return set()

    client = _get_s3_client(s3_client)
    bucket, table_prefix = parse_s3_uri(table_path.rstrip("/") + "/", directory_prefix=True)
    meta_prefix = f"{table_prefix}.hoodie/metadata/"
    commit_keys = [
        k
        for k in _list_keys(bucket, meta_prefix, s3_client=client)
        if k.endswith(".commit") or k.endswith(".deltacommit") or k.endswith(".commit.requested")
    ]

    paths: Set[str] = set()
    for key in commit_keys:
        try:
            raw = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        except Exception as e:
            logger.warning("Failed reading Hudi commit %s: %s", key, e)
            continue
        paths.update(_extract_paths_from_hudi_commit_bytes(raw, bucket))

    if paths:
        return paths

    # Fallback: scan archived timeline JSON (some deployments)
    archive_prefix = f"{table_prefix}.hoodie/archived/"
    for key in _list_keys(bucket, archive_prefix, s3_client=client):
        if not key.endswith(".json"):
            continue
        try:
            data = json.loads(_read_object_text(bucket, key, s3_client=client))
            for entry in data if isinstance(data, list) else [data]:
                if isinstance(entry, dict):
                    for p in entry.get("dataFiles", []) or entry.get("files", []):
                        if isinstance(p, str):
                            paths.add(_normalize_path(p, bucket))
        except Exception:
            continue
    return paths


def _normalize_path(path: str, bucket: str) -> str:
    if path.startswith("s3://"):
        return path
    return f"s3://{bucket}/{path.lstrip('/')}"


def _extract_paths_from_hudi_commit_bytes(raw: bytes, bucket: str) -> Set[str]:
    """Parse Avro commit when fastavro is installed; else heuristic UTF-8 scan."""
    try:
        import io

        import fastavro

        reader = fastavro.reader(io.BytesIO(raw))
        paths: Set[str] = set()
        for record in reader:
            write_stats = record.get("writeStats") or record.get("write_stats") or []
            for stat in write_stats:
                p = stat.get("path") if isinstance(stat, dict) else None
                if p:
                    paths.add(_normalize_path(str(p), bucket))
            for p in record.get("dataFiles", []) or []:
                if isinstance(p, str):
                    paths.add(_normalize_path(p, bucket))
        return paths
    except ImportError:
        pass
    except Exception as e:
        logger.debug("fastavro Hudi parse failed: %s", e)

    text = raw.decode("utf-8", errors="ignore")
    found: Set[str] = set()
    for match in re.finditer(r"s3://[A-Za-z0-9._\-/]+\.parquet", text):
        found.add(match.group(0))
    for match in re.finditer(r"([A-Za-z0-9_\-/]+\.parquet)", text):
        found.add(_normalize_path(match.group(1), bucket))
    return found

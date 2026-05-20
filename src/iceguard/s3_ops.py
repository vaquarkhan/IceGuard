"""S3 helpers for orphan file listing and deletion."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

FileEntryMeta = Tuple[str, float, int]  # uri, age_hours, size_bytes

S3_DELETE_BATCH_LIMIT = 1000


def parse_s3_uri(uri: str, *, directory_prefix: bool = False) -> tuple[str, str]:
    """Return (bucket, key or prefix) for an s3:// URI."""
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"not an s3 URI: {uri!r}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if directory_prefix and key and not key.endswith("/"):
        key = key + "/"
    return bucket, key


def list_parquet_candidates(
    table_path: str,
    *,
    s3_client: Optional[Any] = None,
) -> List[FileEntryMeta]:
    """List .parquet objects under an s3:// table path with age and size."""
    bucket, prefix = parse_s3_uri(table_path, directory_prefix=True)
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")
    now = datetime.now(timezone.utc)
    out: List[FileEntryMeta] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents") or []:
            key = obj["Key"]
            if not key.endswith(".parquet"):
                continue
            uri = f"s3://{bucket}/{key}"
            lm = obj["LastModified"]
            if lm.tzinfo is None:
                lm = lm.replace(tzinfo=timezone.utc)
            age_h = (now - lm).total_seconds() / 3600.0
            out.append((uri, age_h, int(obj.get("Size", 0))))
    return out


def validate_express_one_zone_bucket(
    bucket_name: str,
    *,
    s3_client: Optional[Any] = None,
) -> bool:
    """Return True if the bucket appears to be S3 Express One Zone (directory bucket).

    Directory bucket names end with ``--azid--x-s3``. IceGuard uses standard boto3
    S3 APIs; configure the client with the Express endpoint for your AZ
    (see docs/s3-express-one-zone.md).
    """
    if bucket_name.endswith("--x-s3"):
        return True
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")
    try:
        loc = s3_client.get_bucket_location(Bucket=bucket_name)
        return "express" in str(loc).lower() or "--x-s3" in str(loc.get("LocationConstraint", ""))
    except Exception:
        return False


def delete_s3_uri(uri: str, *, s3_client: Optional[Any] = None) -> None:
    """Delete a single object given an s3:// URI."""
    bucket, key = parse_s3_uri(uri, directory_prefix=False)
    if not key or key.endswith("/"):
        raise ValueError(f"refusing to delete prefix URI: {uri!r}")
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")
    s3_client.delete_object(Bucket=bucket, Key=key)

"""S3-backed checkpoint persistence."""

from __future__ import annotations

import logging
from typing import Any, Optional

from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from iceguard.exceptions import CheckpointCorruptionError
from iceguard.models import CheckpointData

logger = logging.getLogger(__name__)


class CheckpointStore:
    """Persist and load checkpoint JSON objects from S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "iceguard/checkpoints/",
        *,
        s3_client: Optional[Any] = None,
    ) -> None:
        if not bucket or not isinstance(bucket, str):
            raise ValueError("bucket must be a non-empty string")
        self._bucket = bucket
        self._prefix = prefix if prefix.endswith("/") else prefix + "/"
        if s3_client is not None:
            self._client = s3_client
        else:
            import boto3

            self._client = boto3.client("s3")

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}{key.lstrip('/')}"

    def _object_path(self, key: str) -> str:
        return f"s3://{self._bucket}/{self._full_key(key)}"

    def save(self, key: str, checkpoint: CheckpointData) -> None:
        """Serialize checkpoint to JSON and upload; fail-open on S3 errors."""
        body = checkpoint.to_json().encode("utf-8")
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=self._full_key(key),
                Body=body,
                ContentType="application/json",
            )
        except Exception as e:
            logger.warning(
                "Checkpoint save failed (fail-open): %s path=%s",
                e,
                self._object_path(key),
            )

    def load(self, key: str) -> Optional[CheckpointData]:
        """Load checkpoint JSON; return None if missing."""
        path = self._object_path(key)
        try:
            resp = self._client.get_object(
                Bucket=self._bucket, Key=self._full_key(key)
            )
            raw = resp["Body"].read().decode("utf-8")
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NotFound"):
                return None
            logger.warning("Checkpoint load failed: %s path=%s", e, path)
            return None
        except Exception as e:
            logger.warning("Checkpoint load failed: %s path=%s", e, path)
            return None
        try:
            return CheckpointData.from_json(raw, file_path=path)
        except CheckpointCorruptionError:
            raise
        except Exception as e:
            raise CheckpointCorruptionError(path, str(e)) from e

    def delete(self, key: str) -> None:
        """Remove checkpoint object if it exists."""
        try:
            self._client.delete_object(
                Bucket=self._bucket, Key=self._full_key(key)
            )
        except Exception as e:
            logger.warning(
                "Checkpoint delete failed: %s path=%s",
                e,
                self._object_path(key),
            )

    def save_document(self, key: str, body: str, *, fail_open: bool = True) -> None:
        """Persist arbitrary UTF-8 text (e.g. coordinator JSON)."""
        raw = body.encode("utf-8")
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=self._full_key(key),
                Body=raw,
                ContentType="application/json",
            )
        except Exception as e:
            if fail_open:
                logger.warning(
                    "Document save failed (fail-open): %s path=%s",
                    e,
                    self._object_path(key),
                )
            else:
                raise

    def load_document(self, key: str) -> Optional[str]:
        """Load arbitrary UTF-8 text; None if missing."""
        path = self._object_path(key)
        try:
            resp = self._client.get_object(
                Bucket=self._bucket, Key=self._full_key(key)
            )
            return resp["Body"].read().decode("utf-8")
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NotFound"):
                return None
            logger.warning("Document load failed: %s path=%s", e, path)
            return None
        except Exception as e:
            logger.warning("Document load failed: %s path=%s", e, path)
            return None

    def health_check(self, timeout_ms: int = 5000) -> bool:
        """Return True if S3 responds within timeout; False on failure."""
        timeout_s = max(timeout_ms / 1000.0, 0.001)
        cfg = BotoConfig(
            connect_timeout=timeout_s,
            read_timeout=timeout_s,
            retries={"max_attempts": 0, "mode": "standard"},
        )
        import boto3

        client = boto3.client("s3", config=cfg)
        try:
            client.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            try:
                client.list_objects_v2(
                    Bucket=self._bucket, Prefix=self._prefix, MaxKeys=1
                )
                return True
            except Exception as e:
                logger.info("S3 health_check failed: %s", e)
                return False

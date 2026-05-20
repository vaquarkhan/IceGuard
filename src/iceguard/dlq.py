"""Dead-letter queue notifications for failed or rolled-back writes."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def publish_rollback_event(
    queue_url: str,
    *,
    table_path: str,
    remaining_ms: int,
    threshold_ms: int,
    function_name: str,
    idempotency_key: str,
    extra: Optional[Dict[str, Any]] = None,
    sqs_client: Optional[Any] = None,
) -> None:
    """Send a rollback notification to SQS (fail-open on errors)."""
    if sqs_client is None:
        import boto3

        sqs_client = boto3.client("sqs")
    body = {
        "event": "iceguard.rollback",
        "table_path": table_path,
        "remaining_ms": remaining_ms,
        "threshold_ms": threshold_ms,
        "function_name": function_name,
        "idempotency_key": idempotency_key,
    }
    if extra:
        body.update(extra)
    try:
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(body))
    except Exception as e:
        logger.warning("DLQ publish failed (fail-open): %s", e)

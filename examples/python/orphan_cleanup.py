"""Orphan cleanup via library API or CLI."""

from iceguard import iceberg_adapter, scan_orphans

TABLE = "s3://lake/db/orders"
adapter = iceberg_adapter(committed_files=set())  # wire catalog in production

scan = scan_orphans(TABLE, adapter, retention_hours=72)
print(f"Found {len(scan.orphan_files)} orphans")

# Or: iceguard orphans scan s3://lake/db/orders --json

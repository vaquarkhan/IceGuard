"""IceGuard command-line interface for orphan cleanup and diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from iceguard.adapters import (
    DeltaLakeAdapter,
    HudiAdapter,
    IcebergAdapter,
    TableFormatAdapter,
)
from iceguard.enums import TableFormat
from iceguard.orphan_scanner import OrphanScanner


def _adapter_for_format(fmt: str) -> TableFormatAdapter:
    try:
        table_format = TableFormat(fmt.lower())
    except ValueError as e:
        supported = [f.value for f in TableFormat]
        raise SystemExit(f"table-format must be one of {supported}, got {fmt!r}") from e
    if table_format == TableFormat.DELTA:
        return DeltaLakeAdapter()
    if table_format == TableFormat.HUDI:
        return HudiAdapter()
    return IcebergAdapter()


def _cmd_orphans_scan(args: argparse.Namespace) -> int:
    adapter = _adapter_for_format(args.table_format)
    scanner = OrphanScanner(
        adapter,
        retention_hours=args.retention_hours,
        batch_size=args.batch_size,
    )
    result = scanner.scan(args.table_path)
    payload = {
        "orphan_files": result.orphan_files,
        "files_scanned": result.files_scanned,
        "total_orphan_bytes": result.total_orphan_bytes,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Scanned {result.files_scanned} files, found {len(result.orphan_files)} orphans")
        for uri in result.orphan_files:
            print(uri)
    return 0


def _cmd_orphans_delete(args: argparse.Namespace) -> int:
    adapter = _adapter_for_format(args.table_format)
    scanner = OrphanScanner(
        adapter,
        retention_hours=args.retention_hours,
        batch_size=args.batch_size,
    )
    scan = scanner.scan(args.table_path)
    if args.dry_run:
        print(f"dry-run: would delete {len(scan.orphan_files)} files")
        for uri in scan.orphan_files:
            print(uri)
        return 0
    deleted = scanner.delete_orphans(scan.orphan_files)
    payload = {"deleted": deleted.deleted, "failed": deleted.failed}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Deleted {deleted.deleted}, failed {deleted.failed}")
    return 0 if deleted.failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iceguard",
        description="IceGuard: reliability tooling for lakehouse writes on AWS Lambda",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    orphans = sub.add_parser("orphans", help="Orphan Parquet file operations")
    orphans_sub = orphans.add_subparsers(dest="orphans_command", required=True)

    scan = orphans_sub.add_parser("scan", help="List orphan files past retention")
    scan.add_argument("table_path", help="Table root path (e.g. s3://bucket/db/table)")
    scan.add_argument(
        "--table-format",
        default="iceberg",
        choices=[f.value for f in TableFormat],
    )
    scan.add_argument("--retention-hours", type=int, default=72)
    scan.add_argument("--batch-size", type=int, default=1000)
    scan.add_argument("--json", action="store_true")
    scan.set_defaults(func=_cmd_orphans_scan)

    delete = orphans_sub.add_parser("delete", help="Delete orphan files")
    delete.add_argument("table_path")
    delete.add_argument(
        "--table-format",
        default="iceberg",
        choices=[f.value for f in TableFormat],
    )
    delete.add_argument("--retention-hours", type=int, default=72)
    delete.add_argument("--batch-size", type=int, default=1000)
    delete.add_argument("--dry-run", action="store_true")
    delete.add_argument("--json", action="store_true")
    delete.set_defaults(func=_cmd_orphans_delete)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())

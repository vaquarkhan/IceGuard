"""CLI tests."""

from unittest.mock import MagicMock, patch

from iceguard.cli import main


def test_cli_orphans_scan_json(capsys):
    with patch("iceguard.cli.OrphanScanner") as mock_scanner_cls:
        mock_scanner = MagicMock()
        mock_scanner_cls.return_value = mock_scanner
        result = MagicMock()
        result.orphan_files = ["s3://b/t/a.parquet"]
        result.files_scanned = 5
        result.total_orphan_bytes = 100
        mock_scanner.scan.return_value = result
        code = main(
            [
                "orphans",
                "scan",
                "s3://b/t",
                "--table-format",
                "hudi",
                "--json",
            ]
        )
    assert code == 0
    out = capsys.readouterr().out
    assert "orphan_files" in out

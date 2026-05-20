"""S3 path tracker tests with mocked S3 list API."""

from unittest.mock import MagicMock, patch

from iceguard.s3_track import s3_track_paths_factory


def test_s3_track_paths_detects_new_parquet():
    listings = [
        [],
        [("s3://lake/db/t/f1.parquet", 1.0, 10)],
        [],
    ]

    def fake_list(_path, **kwargs):
        return listings.pop(0) if listings else []

    with patch("iceguard.s3_track.list_parquet_candidates", side_effect=fake_list):
        track = s3_track_paths_factory("s3://lake/db/t", s3_client=MagicMock())
        assert track(0, 10) == ["s3://lake/db/t/f1.parquet"]
        assert track(0, 10) == []

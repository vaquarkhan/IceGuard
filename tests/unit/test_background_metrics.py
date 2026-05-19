"""Background metrics emitter."""

import time
from unittest.mock import MagicMock

from iceguard.metrics import BackgroundMetricsEmitter, MetricsEmitter


def test_emit_returns_quickly():
    inner = MagicMock(spec=MetricsEmitter)

    def slow(*a, **k):
        time.sleep(0.4)

    inner.emit_write_outcome.side_effect = slow
    bg = BackgroundMetricsEmitter(inner)
    t0 = time.perf_counter()
    bg.emit_write_outcome("t", "iceberg", "success", "fn")
    assert time.perf_counter() - t0 < 0.15
    bg.close()

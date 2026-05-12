"""Lambda remaining-time watchdog thread."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class WatchdogThread:
    """Daemon thread that polls Lambda remaining time and invokes callback once."""

    def __init__(
        self,
        lambda_context: Any,
        threshold_ms: int,
        callback: Callable[[], None],
        poll_interval_ms: int = 500,
    ) -> None:
        self._ctx = lambda_context
        self._threshold_ms = threshold_ms
        self._callback = callback
        self._poll_interval_ms = max(100, min(1000, poll_interval_ms))
        self._stop = threading.Event()
        self._armed = threading.Event()
        self._armed.set()
        self._callback_lock = threading.Lock()
        self._callback_done = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the daemon watchdog thread."""
        self._thread = threading.Thread(target=self._run, name="iceguard-watchdog", daemon=True)
        self._thread.start()

    def started_ok(self) -> bool:
        """True if the thread was created and is running."""
        return self._thread is not None and self._thread.is_alive()

    def _invoke_callback_once(self) -> None:
        with self._callback_lock:
            if self._callback_done:
                return
            self._callback_done = True
        try:
            self._callback()
        except Exception as e:
            logger.error("Watchdog callback failed: %s", e)

    def _run(self) -> None:
        interval_s = self._poll_interval_ms / 1000.0
        while not self._stop.is_set() and self._armed.is_set():
            try:
                remaining = int(self._ctx.get_remaining_time_in_millis())
            except Exception as e:
                logger.warning("Watchdog could not read remaining time: %s", e)
                time.sleep(interval_s)
                continue
            if remaining <= self._threshold_ms:
                self._invoke_callback_once()
                break
            time.sleep(interval_s)

    def disarm(self) -> None:
        """Stop polling and prevent further callback invocations."""
        self._armed.clear()
        self._stop.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=0.6)

    def is_armed(self) -> bool:
        """True if watchdog is still armed (may still invoke callback)."""
        return self._armed.is_set() and not self._callback_done

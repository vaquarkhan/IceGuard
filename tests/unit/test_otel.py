"""OpenTelemetry emitter tests."""

import builtins
import sys

import pytest


def test_otel_import_error_when_opentelemetry_unavailable(monkeypatch):
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "opentelemetry" or name.startswith("opentelemetry."):
            raise ImportError("forced missing opentelemetry for test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("iceguard.otel", None)
    from iceguard.otel import OpenTelemetryMetricsEmitter

    with pytest.raises(ImportError, match="OpenTelemetry"):
        OpenTelemetryMetricsEmitter()

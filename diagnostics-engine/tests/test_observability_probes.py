"""
Tests for Observability Layer probe: service/log checks (service_probe.py).

Run:
    pytest tests/test_observability_probes.py -v
"""

from unittest.mock import patch

from src.core.config import ProbeConfig
from src.core.models import ProbeStatus
from src.probes.observability import service_probe


def _fake_http_result(reachable=True, status_code=200):
    return {"reachable": reachable, "status_code": status_code, "latency_ms": 12.3}


def test_service_probe_not_configured_is_degraded():
    config = ProbeConfig(target="example.com")
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.DEGRADED
    assert "skipped" in result.message.lower()


@patch("src.probes.observability.service_probe._http_health_check")
def test_service_probe_healthy(mock_http):
    mock_http.return_value = _fake_http_result(reachable=True, status_code=200)
    config = ProbeConfig(target="example.com", service_check_url="https://example.com/health")
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK


@patch("src.probes.observability.service_probe._http_health_check")
def test_service_probe_health_endpoint_down(mock_http):
    mock_http.return_value = _fake_http_result(reachable=False, status_code=None)
    config = ProbeConfig(target="example.com", service_check_url="https://example.com/health")
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED
    assert "Health endpoint failed" in result.message


@patch("src.probes.observability.service_probe._http_health_check")
def test_service_probe_bad_status_code(mock_http):
    mock_http.return_value = _fake_http_result(reachable=True, status_code=503)
    config = ProbeConfig(target="example.com", service_check_url="https://example.com/health")
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED


def test_service_probe_log_scan_finds_errors(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("INFO startup ok\nERROR something broke\nTraceback (most recent call last):\n")

    config = ProbeConfig(target="example.com", log_path=str(log_file))
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.DEGRADED
    assert result.raw["log_scan"]["error_lines_found"] == 2


def test_service_probe_log_scan_clean(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("INFO startup ok\nINFO handling request\n")

    config = ProbeConfig(target="example.com", log_path=str(log_file))
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK


def test_service_probe_log_file_missing(tmp_path):
    missing_path = str(tmp_path / "does_not_exist.log")
    config = ProbeConfig(target="example.com", log_path=missing_path)
    result = service_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.DEGRADED
    assert "log_scan" in result.raw

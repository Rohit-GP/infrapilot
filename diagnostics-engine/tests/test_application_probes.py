"""
Tests for Application Layer probes: HTTP Health, SSL Certificate.

Run:
    pytest tests/test_application_probes.py -v
"""

import socket
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.core.config import ProbeConfig
from src.core.models import ProbeStatus
from src.probes.application import http_probe, ssl_probe


# ---------- HTTP Health Probe ----------

@patch("src.probes.application.http_probe.requests.get")
def test_http_probe_healthy(mock_get):
    mock_get.return_value = MagicMock(status_code=200, content=b"OK", text="OK")
    config = ProbeConfig(target="example.com", http_url="https://example.com")
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK
    assert result.raw["status_code"] == 200


@patch("src.probes.application.http_probe.requests.get")
def test_http_probe_wrong_status(mock_get):
    mock_get.return_value = MagicMock(status_code=500, content=b"err", text="err")
    config = ProbeConfig(target="example.com", http_url="https://example.com", http_expect_status=200)
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED
    assert "500" in result.message


@patch("src.probes.application.http_probe.requests.get")
def test_http_probe_missing_expected_text(mock_get):
    mock_get.return_value = MagicMock(status_code=200, content=b"nope", text="nope")
    config = ProbeConfig(target="example.com", http_url="https://example.com", http_expect_text="healthy")
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED
    assert "healthy" in result.message


@patch("src.probes.application.http_probe.requests.get", side_effect=requests.exceptions.Timeout())
def test_http_probe_timeout(mock_get):
    config = ProbeConfig(target="example.com", http_url="https://example.com", http_timeout_s=1.0)
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.ERROR
    assert result.error is not None


@patch("src.probes.application.http_probe.requests.get", side_effect=requests.exceptions.ConnectionError("refused"))
def test_http_probe_connection_error(mock_get):
    config = ProbeConfig(target="example.com", http_url="https://example.com")
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.ERROR
    assert result.error is not None


def test_http_probe_not_configured_is_degraded_not_error():
    # No http_url set -> this is a skip, not a probe failure, so it must not
    # be ERROR (that would make the CLI's any_failed check trip on every
    # default run even when nothing is actually wrong).
    config = ProbeConfig(target="example.com")
    result = http_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.DEGRADED


# ---------- SSL Certificate Probe ----------

def _fake_cert(days_from_now: int):
    not_after = (datetime.now(timezone.utc) + timedelta(days=days_from_now)).strftime("%b %d %H:%M:%S %Y GMT")
    return {
        "notAfter": not_after,
        "issuer": [[("organizationName", "Test CA")]],
        "subject": [[("commonName", "example.com")]],
    }


@patch("src.probes.application.ssl_probe.socket.create_connection")
@patch("src.probes.application.ssl_probe.ssl.create_default_context")
def test_ssl_probe_valid_cert(mock_ctx, mock_conn):
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = _fake_cert(days_from_now=90)
    mock_ssock.version.return_value = "TLSv1.3"
    mock_ssock.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

    mock_context = MagicMock()
    mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssock
    mock_ctx.return_value = mock_context
    mock_conn.return_value.__enter__.return_value = MagicMock()

    config = ProbeConfig(target="example.com")
    result = ssl_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK
    assert result.raw["days_remaining"] >= 89


@patch("src.probes.application.ssl_probe.socket.create_connection")
@patch("src.probes.application.ssl_probe.ssl.create_default_context")
def test_ssl_probe_expiring_soon(mock_ctx, mock_conn):
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = _fake_cert(days_from_now=5)
    mock_ssock.version.return_value = "TLSv1.3"
    mock_ssock.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

    mock_context = MagicMock()
    mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssock
    mock_ctx.return_value = mock_context
    mock_conn.return_value.__enter__.return_value = MagicMock()

    config = ProbeConfig(target="example.com", ssl_crit_days=7)
    result = ssl_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED
    assert "expires in" in result.message


@patch("src.probes.application.ssl_probe.socket.create_connection", side_effect=socket.timeout())
def test_ssl_probe_connection_timeout(mock_conn):
    config = ProbeConfig(target="example.com", ssl_timeout_s=1.0)
    result = ssl_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.ERROR

"""
Unit tests for individual probes. Port and DNS probes are tested against
real localhost/loopback behavior (no network needed). Ping is tested via
subprocess mocking since CI environments often can't send ICMP.
"""

import socket
import threading
from contextlib import closing

import pytest

from src.core.config import ProbeConfig
from src.core.models import ProbeStatus
from src.probes import port_probe, dns_probe


def _get_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def test_port_probe_detects_open_port():
    port = _get_free_port()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", port))
    server.listen(1)
    server.settimeout(2)

    def accept_once():
        try:
            conn, _ = server.accept()
            conn.close()
        except socket.timeout:
            pass

    t = threading.Thread(target=accept_once, daemon=True)
    t.start()

    config = ProbeConfig(target="localhost", ports=[port])
    evidence = port_probe.run(config)

    assert evidence.status == ProbeStatus.OK
    assert evidence.raw["results"][0]["open"] is True
    server.close()


def test_port_probe_detects_closed_port():
    port = _get_free_port()  # bound briefly then released -> nothing listening
    config = ProbeConfig(target="localhost", ports=[port])
    evidence = port_probe.run(config)

    assert evidence.status == ProbeStatus.FAILED
    assert evidence.raw["results"][0]["open"] is False


def test_dns_probe_resolves_localhost():
    config = ProbeConfig(target="localhost", ports=[])
    evidence = dns_probe.run(config)

    assert evidence.status == ProbeStatus.OK
    assert "127.0.0.1" in evidence.raw["resolved_ips"]


def test_dns_probe_fails_on_bogus_domain():
    config = ProbeConfig(target="this-domain-should-not-exist-12345.invalid", ports=[])
    evidence = dns_probe.run(config)

    assert evidence.status == ProbeStatus.FAILED

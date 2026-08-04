"""
Tests for System Layer probes: CPU, Memory, Disk.

Run:
    pytest tests/test_system_probes.py -v
"""

from unittest.mock import MagicMock, patch

from src.core.config import ProbeConfig
from src.core.models import ProbeStatus
from src.probes.system import cpu_probe, memory_probe, disk_probe


# ---------- CPU Probe ----------

@patch("src.probes.system.cpu_probe.psutil.getloadavg", return_value=(0.1, 0.2, 0.3))
@patch("src.probes.system.cpu_probe.psutil.cpu_count", return_value=4)
@patch("src.probes.system.cpu_probe.psutil.cpu_percent")
def test_cpu_probe_normal(mock_cpu_pct, mock_count, mock_load):
    mock_cpu_pct.side_effect = [20.0, [18.0, 22.0, 19.0, 21.0]]  # overall, then per-core
    config = ProbeConfig(target="localhost", cpu_warn_pct=75, cpu_crit_pct=90)
    result = cpu_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK
    assert result.raw["core_count"] == 4


@patch("src.probes.system.cpu_probe.psutil.getloadavg", return_value=(8.0, 7.5, 6.0))
@patch("src.probes.system.cpu_probe.psutil.cpu_count", return_value=4)
@patch("src.probes.system.cpu_probe.psutil.cpu_percent")
def test_cpu_probe_critical(mock_cpu_pct, mock_count, mock_load):
    mock_cpu_pct.side_effect = [95.0, [96.0, 94.0, 95.0, 95.0]]
    config = ProbeConfig(target="localhost", cpu_warn_pct=75, cpu_crit_pct=90)
    result = cpu_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED


@patch("src.probes.system.cpu_probe.psutil.cpu_percent", side_effect=Exception("psutil failure"))
def test_cpu_probe_execution_error(mock_cpu_pct):
    config = ProbeConfig(target="localhost")
    result = cpu_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.ERROR
    assert result.error is not None


# ---------- Memory Probe ----------

def _fake_vm(percent):
    vm = MagicMock()
    vm.total = 8 * 1024 ** 3
    vm.used = int(8 * 1024 ** 3 * percent / 100)
    vm.available = 8 * 1024 ** 3 - vm.used
    vm.percent = percent
    return vm


def _fake_swap(percent):
    swap = MagicMock()
    swap.total = 2 * 1024 ** 3
    swap.used = int(2 * 1024 ** 3 * percent / 100)
    swap.percent = percent
    return swap


@patch("src.probes.system.memory_probe.psutil.swap_memory", return_value=_fake_swap(0))
@patch("src.probes.system.memory_probe.psutil.virtual_memory", return_value=_fake_vm(40))
def test_memory_probe_normal(mock_vm, mock_swap):
    config = ProbeConfig(target="localhost", memory_warn_pct=80, memory_crit_pct=95)
    result = memory_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK


@patch("src.probes.system.memory_probe.psutil.swap_memory", return_value=_fake_swap(50))
@patch("src.probes.system.memory_probe.psutil.virtual_memory", return_value=_fake_vm(97))
def test_memory_probe_critical(mock_vm, mock_swap):
    config = ProbeConfig(target="localhost", memory_warn_pct=80, memory_crit_pct=95)
    result = memory_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED


# ---------- Disk Probe ----------

def _fake_partition(mountpoint="/"):
    p = MagicMock()
    p.mountpoint = mountpoint
    p.fstype = "ext4"
    return p


def _fake_disk_usage(percent):
    u = MagicMock()
    u.total = 100 * 1024 ** 3
    u.used = int(100 * 1024 ** 3 * percent / 100)
    u.free = 100 * 1024 ** 3 - u.used
    u.percent = percent
    return u


@patch("src.probes.system.disk_probe.psutil.disk_usage", return_value=_fake_disk_usage(40))
@patch("src.probes.system.disk_probe.psutil.disk_partitions", return_value=[_fake_partition("/")])
def test_disk_probe_normal(mock_parts, mock_usage):
    config = ProbeConfig(target="localhost", disk_warn_pct=80, disk_crit_pct=90)
    result = disk_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.OK
    assert result.raw["worst_mount"] == "/"


@patch("src.probes.system.disk_probe.psutil.disk_usage", return_value=_fake_disk_usage(95))
@patch("src.probes.system.disk_probe.psutil.disk_partitions", return_value=[_fake_partition("/")])
def test_disk_probe_critical(mock_parts, mock_usage):
    config = ProbeConfig(target="localhost", disk_warn_pct=80, disk_crit_pct=90)
    result = disk_probe.run(config, job_id="test")
    assert result.status == ProbeStatus.FAILED

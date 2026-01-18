"""
Metrics collection and tracking for simulation analysis.
Tracks latency, loss, throughput, and handover statistics.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import deque
import numpy as np

from .scheduler import TransmissionResult
from .config import PACKET_SIZE_BYTES, THROUGHPUT_WINDOW_MS


@dataclass
class StepMetrics:
    """Metrics for a single simulation step."""
    time_ms: int

    # Traffic
    packets_generated: int = 0
    packets_delivered: int = 0
    packets_dropped_overflow: int = 0
    packets_dropped_radio: int = 0
    packets_dropped_expired: int = 0

    # Latency (ms)
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    latency_samples: List[float] = field(default_factory=list)

    # Throughput (Mbps)
    throughput_mbps: float = 0.0

    # Association
    connected_ues: int = 0
    handovers: int = 0

    # Radio quality
    avg_rsrp_dbm: float = -100.0
    avg_sinr_db: float = 0.0


class MetricsCollector:
    """Collects and aggregates simulation metrics over time."""

    def __init__(self):
        self.step_metrics: List[StepMetrics] = []

        # Rolling window for throughput calculation
        self.delivery_window: deque = deque()  # (time_ms, bytes_delivered)

        # Cumulative counters
        self.total_generated = 0
        self.total_delivered = 0
        self.total_dropped_overflow = 0
        self.total_dropped_radio = 0
        self.total_dropped_expired = 0
        self.total_handovers = 0

        # Latency tracking
        self.all_latencies: List[float] = []

    def record_step(
        self,
        time_ms: int,
        packets_generated: int,
        packets_dropped_overflow: int,
        packets_dropped_expired: int,
        transmission_results: List[TransmissionResult],
        num_handovers: int,
        connected_ues: int,
        avg_rsrp_dbm: float,
        avg_sinr_db: float,
    ):
        """Record metrics for a single simulation step."""
        # Process transmission results
        delivered = [r for r in transmission_results if r.success]
        dropped_radio = [r for r in transmission_results if r.dropped_radio]

        # Latency statistics
        latencies = [r.latency_ms for r in delivered]
        avg_latency = np.mean(latencies) if latencies else 0.0
        min_latency = min(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0

        # Update rolling throughput window
        bytes_delivered = len(delivered) * PACKET_SIZE_BYTES
        self.delivery_window.append((time_ms, bytes_delivered))

        # Remove old entries from window
        cutoff_time = time_ms - THROUGHPUT_WINDOW_MS
        while self.delivery_window and self.delivery_window[0][0] < cutoff_time:
            self.delivery_window.popleft()

        # Calculate throughput over window
        window_bytes = sum(b for _, b in self.delivery_window)
        window_duration_s = THROUGHPUT_WINDOW_MS / 1000.0
        throughput_mbps = (window_bytes * 8) / (window_duration_s * 1e6) if window_duration_s > 0 else 0.0

        # Create step metrics
        metrics = StepMetrics(
            time_ms=time_ms,
            packets_generated=packets_generated,
            packets_delivered=len(delivered),
            packets_dropped_overflow=packets_dropped_overflow,
            packets_dropped_radio=len(dropped_radio),
            packets_dropped_expired=packets_dropped_expired,
            avg_latency_ms=avg_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            latency_samples=latencies,
            throughput_mbps=throughput_mbps,
            connected_ues=connected_ues,
            handovers=num_handovers,
            avg_rsrp_dbm=avg_rsrp_dbm,
            avg_sinr_db=avg_sinr_db,
        )

        self.step_metrics.append(metrics)

        # Update cumulative counters
        self.total_generated += packets_generated
        self.total_delivered += len(delivered)
        self.total_dropped_overflow += packets_dropped_overflow
        self.total_dropped_radio += len(dropped_radio)
        self.total_dropped_expired += packets_dropped_expired
        self.total_handovers += num_handovers
        self.all_latencies.extend(latencies)

    def get_summary(self) -> Dict:
        """Get summary statistics for the entire simulation."""
        total_dropped = (
            self.total_dropped_overflow +
            self.total_dropped_radio +
            self.total_dropped_expired
        )

        total_packets = self.total_delivered + total_dropped
        loss_rate = total_dropped / total_packets if total_packets > 0 else 0.0

        # Latency percentiles
        if self.all_latencies:
            latencies = np.array(self.all_latencies)
            p50 = np.percentile(latencies, 50)
            p95 = np.percentile(latencies, 95)
            p99 = np.percentile(latencies, 99)
            avg_latency = np.mean(latencies)
        else:
            p50 = p95 = p99 = avg_latency = 0.0

        # Average throughput
        throughputs = [m.throughput_mbps for m in self.step_metrics]
        avg_throughput = np.mean(throughputs) if throughputs else 0.0

        return {
            "total_packets_generated": self.total_generated,
            "total_packets_delivered": self.total_delivered,
            "total_packets_dropped": total_dropped,
            "dropped_overflow": self.total_dropped_overflow,
            "dropped_radio": self.total_dropped_radio,
            "dropped_expired": self.total_dropped_expired,
            "loss_rate": loss_rate,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "avg_throughput_mbps": avg_throughput,
            "total_handovers": self.total_handovers,
        }

    def get_time_series(self) -> Dict[str, List]:
        """Get time series data for plotting."""
        return {
            "time_ms": [m.time_ms for m in self.step_metrics],
            "latency_ms": [m.avg_latency_ms for m in self.step_metrics],
            "throughput_mbps": [m.throughput_mbps for m in self.step_metrics],
            "packets_delivered": [m.packets_delivered for m in self.step_metrics],
            "packets_dropped": [
                m.packets_dropped_overflow + m.packets_dropped_radio + m.packets_dropped_expired
                for m in self.step_metrics
            ],
            "connected_ues": [m.connected_ues for m in self.step_metrics],
            "handovers": [m.handovers for m in self.step_metrics],
            "rsrp_dbm": [m.avg_rsrp_dbm for m in self.step_metrics],
            "sinr_db": [m.avg_sinr_db for m in self.step_metrics],
        }

    def print_summary(self):
        """Print human-readable summary."""
        summary = self.get_summary()
        print("\n" + "=" * 50)
        print("SIMULATION SUMMARY")
        print("=" * 50)
        print(f"Packets Generated:    {summary['total_packets_generated']:,}")
        print(f"Packets Delivered:    {summary['total_packets_delivered']:,}")
        print(f"Packets Dropped:      {summary['total_packets_dropped']:,}")
        print(f"  - Buffer Overflow:  {summary['dropped_overflow']:,}")
        print(f"  - Radio Quality:    {summary['dropped_radio']:,}")
        print(f"  - Expired:          {summary['dropped_expired']:,}")
        print(f"Loss Rate:            {summary['loss_rate']:.2%}")
        print("-" * 50)
        print(f"Avg Latency:          {summary['avg_latency_ms']:.2f} ms")
        print(f"P50 Latency:          {summary['p50_latency_ms']:.2f} ms")
        print(f"P95 Latency:          {summary['p95_latency_ms']:.2f} ms")
        print(f"P99 Latency:          {summary['p99_latency_ms']:.2f} ms")
        print("-" * 50)
        print(f"Avg Throughput:       {summary['avg_throughput_mbps']:.2f} Mbps")
        print(f"Total Handovers:      {summary['total_handovers']}")
        print("=" * 50 + "\n")

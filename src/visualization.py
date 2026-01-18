"""
Visualization: network topology and time-series metrics plots.
"""
import os
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

from .entities import UE, GNodeB
from .metrics import MetricsCollector
from .config import AREA_WIDTH, AREA_HEIGHT


def plot_network_topology(
    ues: List[UE],
    gnbs: List[GNodeB],
    output_path: str,
    title: str = "Network Topology",
):
    """
    Plot network topology showing gNodeBs, UEs, and their associations.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot gNodeBs as red triangles
    gnb_x = [g.x for g in gnbs]
    gnb_y = [g.y for g in gnbs]
    ax.scatter(gnb_x, gnb_y, c='red', marker='^', s=200, label='gNodeB', zorder=5)

    # Label gNodeBs
    for gnb in gnbs:
        ax.annotate(f'gNB{gnb.id}', (gnb.x, gnb.y), textcoords="offset points",
                    xytext=(0, 10), ha='center', fontsize=9)

    # Plot UEs as blue dots
    ue_x = [u.x for u in ues]
    ue_y = [u.y for u in ues]
    ax.scatter(ue_x, ue_y, c='blue', marker='o', s=50, label='UE', zorder=4)

    # Draw association lines
    gnb_map = {g.id: g for g in gnbs}
    for ue in ues:
        if ue.serving_gnb_id is not None and ue.serving_gnb_id in gnb_map:
            gnb = gnb_map[ue.serving_gnb_id]
            ax.plot([ue.x, gnb.x], [ue.y, gnb.y], 'g-', alpha=0.3, linewidth=0.5)

    # Set axis limits
    ax.set_xlim(0, AREA_WIDTH)
    ax.set_ylim(0, AREA_HEIGHT)
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_throughput(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot throughput over time."""
    ts = metrics.get_time_series()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ts['time_ms'], ts['throughput_mbps'], 'b-', linewidth=1)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Network Throughput Over Time')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_latency(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot latency over time."""
    ts = metrics.get_time_series()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ts['time_ms'], ts['latency_ms'], 'r-', linewidth=1)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Average Latency (ms)')
    ax.set_title('Packet Latency Over Time')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_latency_histogram(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot latency distribution histogram."""
    if not metrics.all_latencies:
        return

    fig, ax = plt.subplots(figsize=(10, 5))

    latencies = np.array(metrics.all_latencies)
    ax.hist(latencies, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax.axvline(np.mean(latencies), color='red', linestyle='--', label=f'Mean: {np.mean(latencies):.1f} ms')
    ax.axvline(np.percentile(latencies, 95), color='orange', linestyle='--',
               label=f'P95: {np.percentile(latencies, 95):.1f} ms')

    ax.set_xlabel('Latency (ms)')
    ax.set_ylabel('Count')
    ax.set_title('Latency Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_packet_loss(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot packet delivery and loss over time."""
    ts = metrics.get_time_series()

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(ts['time_ms'], ts['packets_delivered'], 'g-', linewidth=1, label='Delivered')
    ax.plot(ts['time_ms'], ts['packets_dropped'], 'r-', linewidth=1, label='Dropped')

    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Packets per Step')
    ax.set_title('Packet Delivery and Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_handovers(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot handover events and connected UEs over time."""
    ts = metrics.get_time_series()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Handovers
    ax1.bar(ts['time_ms'], ts['handovers'], color='orange', width=1.0)
    ax1.set_ylabel('Handovers')
    ax1.set_title('Handover Events')
    ax1.grid(True, alpha=0.3)

    # Connected UEs
    ax2.plot(ts['time_ms'], ts['connected_ues'], 'b-', linewidth=1)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Connected UEs')
    ax2.set_title('Connected UEs Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_radio_quality(
    metrics: MetricsCollector,
    output_path: str,
):
    """Plot average RSRP and SINR over time."""
    ts = metrics.get_time_series()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # RSRP
    ax1.plot(ts['time_ms'], ts['rsrp_dbm'], 'b-', linewidth=1)
    ax1.set_ylabel('RSRP (dBm)')
    ax1.set_title('Average RSRP')
    ax1.grid(True, alpha=0.3)

    # SINR
    ax2.plot(ts['time_ms'], ts['sinr_db'], 'g-', linewidth=1)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('SINR (dB)')
    ax2.set_title('Average SINR')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_summary_dashboard(
    metrics: MetricsCollector,
    output_path: str,
):
    """Create a summary dashboard with multiple metrics."""
    ts = metrics.get_time_series()
    summary = metrics.get_summary()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Throughput
    ax1 = axes[0, 0]
    ax1.plot(ts['time_ms'], ts['throughput_mbps'], 'b-', linewidth=1)
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title(f'Throughput (Avg: {summary["avg_throughput_mbps"]:.1f} Mbps)')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # Latency
    ax2 = axes[0, 1]
    ax2.plot(ts['time_ms'], ts['latency_ms'], 'r-', linewidth=1)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Latency (ms)')
    ax2.set_title(f'Latency (P95: {summary["p95_latency_ms"]:.1f} ms)')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    # Loss
    ax3 = axes[1, 0]
    ax3.plot(ts['time_ms'], ts['packets_delivered'], 'g-', linewidth=1, label='Delivered')
    ax3.plot(ts['time_ms'], ts['packets_dropped'], 'r-', linewidth=1, label='Dropped')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Packets')
    ax3.set_title(f'Packets (Loss Rate: {summary["loss_rate"]:.1%})')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(bottom=0)

    # SINR
    ax4 = axes[1, 1]
    ax4.plot(ts['time_ms'], ts['sinr_db'], 'purple', linewidth=1)
    ax4.set_xlabel('Time (ms)')
    ax4.set_ylabel('SINR (dB)')
    ax4.set_title('Radio Quality (SINR)')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def generate_all_plots(
    ues: List[UE],
    gnbs: List[GNodeB],
    metrics: MetricsCollector,
    output_dir: str,
):
    """Generate all visualization plots."""
    os.makedirs(output_dir, exist_ok=True)

    print("\nGenerating plots...")

    plot_network_topology(
        ues, gnbs,
        os.path.join(output_dir, "network_topology.png"),
        title="Final Network Topology"
    )

    plot_throughput(
        metrics,
        os.path.join(output_dir, "throughput.png")
    )

    plot_latency(
        metrics,
        os.path.join(output_dir, "latency.png")
    )

    plot_latency_histogram(
        metrics,
        os.path.join(output_dir, "latency_histogram.png")
    )

    plot_packet_loss(
        metrics,
        os.path.join(output_dir, "packet_loss.png")
    )

    plot_handovers(
        metrics,
        os.path.join(output_dir, "handovers.png")
    )

    plot_radio_quality(
        metrics,
        os.path.join(output_dir, "radio_quality.png")
    )

    plot_summary_dashboard(
        metrics,
        os.path.join(output_dir, "summary_dashboard.png")
    )

    print(f"\nAll plots saved to: {output_dir}/")

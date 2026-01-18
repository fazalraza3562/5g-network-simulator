"""
Round Robin scheduler for per-gNodeB packet transmission.
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
import numpy as np

from .entities import UE, GNodeB, Packet
from .radio import calculate_achievable_rate, calculate_distance
from .config import (
    PACKET_SIZE_BYTES,
    TIME_STEP_MS,
    SimConfig,
)

# Speed of light for propagation delay
SPEED_OF_LIGHT_M_PER_MS = 299792.458  # m/ms


@dataclass
class TransmissionResult:
    """Result of a packet transmission attempt."""
    packet: Packet
    ue_id: int
    gnb_id: int
    success: bool
    latency_ms: int
    dropped_radio: bool = False


def calculate_total_latency(
    packet: Packet,
    ue: UE,
    gnb: GNodeB,
    current_time_ms: int,
    config: SimConfig,
) -> float:
    """
    Calculate total packet latency including:
    - Queueing delay (time spent waiting in buffer)
    - Propagation delay (distance-based, speed of light)
    - Processing jitter (random component)
    """
    # Queueing delay: time since packet creation
    queueing_delay = current_time_ms - packet.created_at_ms

    # Propagation delay: distance / speed of light
    distance = calculate_distance(ue, gnb)
    propagation_delay = distance / SPEED_OF_LIGHT_M_PER_MS

    # Processing and transmission jitter (0.1 to 2 ms)
    jitter = config.rng.uniform(0.1, 2.0)

    # Total latency
    total_latency = queueing_delay + propagation_delay + jitter

    return total_latency


def calculate_packets_per_slot(sinr_db: float) -> int:
    """
    Calculate how many packets can be transmitted in one time slot
    based on achievable rate and packet size.
    """
    rate_mbps = calculate_achievable_rate(sinr_db)
    rate_bytes_per_ms = (rate_mbps * 1e6) / 8 / 1000  # bytes per ms
    bytes_per_slot = rate_bytes_per_ms * TIME_STEP_MS
    packets = int(bytes_per_slot / PACKET_SIZE_BYTES)
    return max(packets, 0)


def schedule_gnb(
    gnb: GNodeB,
    ue_map: Dict[int, UE],
    current_time_ms: int,
    config: SimConfig,
) -> List[TransmissionResult]:
    """
    Run Round Robin scheduler for one gNodeB.
    Each connected UE gets equal opportunity to transmit.

    Returns:
        List of transmission results.
    """
    results = []

    if not gnb.connected_ues:
        return results

    # Get connected UEs as sorted list for deterministic ordering
    connected_list = sorted(gnb.connected_ues)
    num_ues = len(connected_list)

    if num_ues == 0:
        return results

    # Round Robin: start from where we left off
    start_idx = gnb.rr_index % num_ues

    # Calculate total transmission capacity for this slot
    # We'll divide capacity among UEs in round-robin fashion
    for i in range(num_ues):
        ue_idx = (start_idx + i) % num_ues
        ue_id = connected_list[ue_idx]

        ue = ue_map.get(ue_id)
        if ue is None:
            continue

        # Get buffer for this UE
        buffer = gnb.get_buffer(ue_id)
        if not buffer:
            continue

        # Calculate how many packets this UE can receive based on SINR
        packets_capacity = calculate_packets_per_slot(ue.sinr_db)

        # Fair share: divide capacity
        # Simple model: each UE gets packets_capacity / num_active_ues
        # But we just let each UE transmit up to their capacity
        packets_to_send = min(packets_capacity, len(buffer))

        for _ in range(packets_to_send):
            if not buffer:
                break

            packet = buffer.popleft()

            # Check for radio-quality-based drop
            # Higher probability of drop at low SINR
            drop_prob = calculate_drop_probability(ue.sinr_db)
            dropped = config.rng.random() < drop_prob

            # Calculate total latency
            latency = calculate_total_latency(
                packet, ue, gnb, current_time_ms, config
            )

            results.append(TransmissionResult(
                packet=packet,
                ue_id=ue_id,
                gnb_id=gnb.id,
                success=not dropped,
                latency_ms=latency,
                dropped_radio=dropped,
            ))

    # Update round-robin index for next slot
    gnb.rr_index = (gnb.rr_index + 1) % max(num_ues, 1)

    return results


def calculate_drop_probability(sinr_db: float) -> float:
    """
    Calculate packet drop probability based on SINR.
    Uses a sigmoid-like function:
    - High SINR (>10 dB): near-zero drop rate
    - Low SINR (<-5 dB): high drop rate
    """
    import numpy as np

    # Sigmoid centered around -3 dB with steeper slope
    # At SINR > 5 dB: very low drop rate
    # At SINR < -10 dB: very high drop rate
    prob = 1 / (1 + np.exp((sinr_db + 3) / 4))

    # Cap minimum drop rate at 0.001 (0.1%)
    return max(prob, 0.001)


def run_schedulers(
    gnbs: List[GNodeB],
    ue_map: Dict[int, UE],
    current_time_ms: int,
    config: SimConfig,
) -> List[TransmissionResult]:
    """
    Run Round Robin scheduler for all gNodeBs.

    Returns:
        Combined list of all transmission results.
    """
    all_results = []

    for gnb in gnbs:
        results = schedule_gnb(gnb, ue_map, current_time_ms, config)
        all_results.extend(results)

    return all_results


def get_scheduler_stats(results: List[TransmissionResult]) -> Dict:
    """Get statistics from transmission results."""
    if not results:
        return {
            "packets_transmitted": 0,
            "packets_delivered": 0,
            "packets_dropped_radio": 0,
            "avg_latency_ms": 0.0,
        }

    delivered = [r for r in results if r.success]
    dropped_radio = [r for r in results if r.dropped_radio]

    avg_latency = sum(r.latency_ms for r in delivered) / len(delivered) if delivered else 0.0

    return {
        "packets_transmitted": len(results),
        "packets_delivered": len(delivered),
        "packets_dropped_radio": len(dropped_radio),
        "avg_latency_ms": avg_latency,
    }

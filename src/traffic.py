"""
Traffic generation model: packet creation and queue management.
"""
from typing import List, Dict, Tuple

from .entities import UE, GNodeB, Packet
from .config import (
    PACKET_SIZE_BYTES,
    PACKET_ARRIVAL_RATE,
    MAX_PACKET_DELAY_MS,
    SimConfig,
)


class TrafficGenerator:
    """Generates packets for UEs using Poisson arrival process."""

    def __init__(self, config: SimConfig):
        self.config = config
        self.packet_counter = 0

    def generate_packets(
        self,
        ues: List[UE],
        gnb_map: Dict[int, GNodeB],
        current_time_ms: int,
    ) -> Tuple[int, int]:
        """
        Generate packets for all connected UEs.
        Packets are placed in the serving gNodeB's buffer.

        Returns:
            Tuple of (packets_generated, packets_dropped_overflow)
        """
        rng = self.config.rng
        generated = 0
        dropped_overflow = 0

        for ue in ues:
            if not ue.is_connected():
                continue

            # Poisson arrival: number of packets this time step
            num_packets = rng.poisson(PACKET_ARRIVAL_RATE)

            serving_gnb = gnb_map.get(ue.serving_gnb_id)
            if serving_gnb is None:
                continue

            for _ in range(num_packets):
                packet = Packet(
                    id=self.packet_counter,
                    size_bytes=PACKET_SIZE_BYTES,
                    created_at_ms=current_time_ms,
                    ue_id=ue.id,
                )
                self.packet_counter += 1

                # Try to enqueue
                if serving_gnb.enqueue_packet(packet):
                    generated += 1
                else:
                    dropped_overflow += 1

        return generated, dropped_overflow


def drop_expired_packets(
    gnbs: List[GNodeB],
    current_time_ms: int,
) -> int:
    """
    Remove packets that have exceeded maximum delay.

    Returns:
        Number of packets dropped due to expiry.
    """
    dropped = 0

    for gnb in gnbs:
        for ue_id, buffer in gnb.buffers.items():
            # Count expired packets
            expired = []
            for i, packet in enumerate(buffer):
                if packet.age_ms(current_time_ms) > MAX_PACKET_DELAY_MS:
                    expired.append(i)

            # Remove expired (iterate in reverse to preserve indices)
            for i in reversed(expired):
                del buffer[i]
                dropped += 1

    return dropped


def transfer_packets_on_handover(
    source_gnb: GNodeB,
    target_gnb: GNodeB,
    ue_id: int,
):
    """
    Transfer buffered packets from source to target gNodeB during handover.
    This simulates X2/Xn forwarding.
    """
    source_buffer = source_gnb.get_buffer(ue_id)

    # Transfer all packets to target
    while source_buffer:
        packet = source_buffer.popleft()
        target_gnb.enqueue_packet(packet)

    # Clear source buffer for this UE
    source_gnb.clear_buffer(ue_id)


def get_queue_stats(gnbs: List[GNodeB]) -> Dict[int, Dict[str, int]]:
    """
    Get queue statistics for all gNodeBs.

    Returns:
        Dict mapping gnb_id -> {total_packets, num_ues}
    """
    stats = {}
    for gnb in gnbs:
        total_packets = sum(len(buf) for buf in gnb.buffers.values())
        stats[gnb.id] = {
            "total_packets": total_packets,
            "num_ues": len(gnb.connected_ues),
        }
    return stats

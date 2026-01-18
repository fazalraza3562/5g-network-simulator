"""
Data models for UE (User Equipment) and gNodeB (base station).
"""
from dataclasses import dataclass, field
from typing import Optional
from collections import deque

from .config import (
    GNB_TX_POWER_DBM,
    GNB_HEIGHT_M,
    GNB_BUFFER_SIZE,
    UE_HEIGHT_M,
)


@dataclass
class Packet:
    """A network packet with timing information."""
    id: int
    size_bytes: int
    created_at_ms: int
    ue_id: int

    def age_ms(self, current_time_ms: int) -> int:
        return current_time_ms - self.created_at_ms


@dataclass
class GNodeB:
    """5G Base Station (gNB)."""
    id: int
    x: float  # Position in meters
    y: float
    tx_power_dbm: float = GNB_TX_POWER_DBM
    height_m: float = GNB_HEIGHT_M

    # Connected UE IDs
    connected_ues: set = field(default_factory=set)

    # Per-UE packet queues: ue_id -> deque of Packets
    buffers: dict = field(default_factory=dict)

    # Round-robin state: index into connected UE list
    rr_index: int = 0

    def attach_ue(self, ue_id: int):
        """Attach a UE to this gNB."""
        self.connected_ues.add(ue_id)
        if ue_id not in self.buffers:
            self.buffers[ue_id] = deque(maxlen=GNB_BUFFER_SIZE)

    def detach_ue(self, ue_id: int):
        """Detach a UE from this gNB."""
        self.connected_ues.discard(ue_id)
        # Keep buffer for potential handover (packets transferred)

    def enqueue_packet(self, packet: Packet) -> bool:
        """
        Enqueue a packet for a UE. Returns False if buffer overflow.
        """
        ue_id = packet.ue_id
        if ue_id not in self.buffers:
            self.buffers[ue_id] = deque(maxlen=GNB_BUFFER_SIZE)

        buf = self.buffers[ue_id]
        if len(buf) >= GNB_BUFFER_SIZE:
            return False  # Buffer overflow
        buf.append(packet)
        return True

    def get_buffer(self, ue_id: int) -> deque:
        """Get packet buffer for a UE."""
        if ue_id not in self.buffers:
            self.buffers[ue_id] = deque(maxlen=GNB_BUFFER_SIZE)
        return self.buffers[ue_id]

    def clear_buffer(self, ue_id: int):
        """Clear buffer for a UE."""
        if ue_id in self.buffers:
            self.buffers[ue_id].clear()


@dataclass
class UE:
    """User Equipment (mobile device)."""
    id: int
    x: float  # Position in meters
    y: float
    speed: float  # m/s
    direction: float  # radians
    height_m: float = UE_HEIGHT_M

    # Association state
    serving_gnb_id: Optional[int] = None
    rsrp_dbm: float = -140.0  # Current RSRP from serving cell
    sinr_db: float = -20.0  # Current SINR

    # Handover state (for time-to-trigger)
    handover_target_gnb: Optional[int] = None
    handover_timer_ms: int = 0

    # Measurement reports: gnb_id -> rsrp_dbm
    measurements: dict = field(default_factory=dict)

    def is_connected(self) -> bool:
        return self.serving_gnb_id is not None

    def start_handover_timer(self, target_gnb_id: int):
        """Start TTT for handover to target."""
        self.handover_target_gnb = target_gnb_id
        self.handover_timer_ms = 0

    def reset_handover_timer(self):
        """Reset handover state."""
        self.handover_target_gnb = None
        self.handover_timer_ms = 0

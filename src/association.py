"""
Association and handover logic with hysteresis and time-to-trigger.
Implements A3 event-based handover (neighbor becomes offset better than serving).
"""
from typing import List, Dict, Optional, Tuple

from .entities import UE, GNodeB
from .radio import get_best_cell
from .traffic import transfer_packets_on_handover
from .config import (
    HANDOVER_HYSTERESIS_DB,
    TIME_TO_TRIGGER_MS,
    A3_OFFSET_DB,
    TIME_STEP_MS,
    SINR_THRESHOLD_DB,
)


def initial_attach(
    ue: UE,
    gnbs: List[GNodeB],
    gnb_map: Dict[int, GNodeB],
) -> bool:
    """
    Attach UE to the best available cell.

    Returns:
        True if attached successfully.
    """
    best_gnb_id = get_best_cell(ue)

    if best_gnb_id < 0:
        return False

    # Check if signal is strong enough
    best_rsrp = ue.measurements.get(best_gnb_id, -140)
    if best_rsrp < -130:  # Too weak to connect
        return False

    # Attach to best cell
    gnb = gnb_map[best_gnb_id]
    gnb.attach_ue(ue.id)
    ue.serving_gnb_id = best_gnb_id
    ue.reset_handover_timer()

    return True


def check_a3_event(
    ue: UE,
    serving_rsrp: float,
    neighbor_rsrp: float,
) -> bool:
    """
    Check if A3 event condition is met:
    Neighbor RSRP > Serving RSRP + Offset + Hysteresis

    This means the neighbor cell is significantly better than serving cell.
    """
    threshold = serving_rsrp + A3_OFFSET_DB + HANDOVER_HYSTERESIS_DB
    return neighbor_rsrp > threshold


def find_handover_target(ue: UE) -> Optional[int]:
    """
    Find the best handover target that satisfies A3 event condition.

    Returns:
        Target gNodeB ID or None if no suitable target.
    """
    if ue.serving_gnb_id is None:
        return None

    serving_rsrp = ue.measurements.get(ue.serving_gnb_id, -140)

    best_target = None
    best_rsrp = serving_rsrp  # Must be better than serving

    for gnb_id, rsrp in ue.measurements.items():
        if gnb_id == ue.serving_gnb_id:
            continue

        if check_a3_event(ue, serving_rsrp, rsrp):
            if rsrp > best_rsrp:
                best_rsrp = rsrp
                best_target = gnb_id

    return best_target


def execute_handover(
    ue: UE,
    target_gnb_id: int,
    gnb_map: Dict[int, GNodeB],
) -> bool:
    """
    Execute handover from serving cell to target cell.

    Returns:
        True if handover successful.
    """
    if ue.serving_gnb_id is None:
        return False

    source_gnb = gnb_map.get(ue.serving_gnb_id)
    target_gnb = gnb_map.get(target_gnb_id)

    if source_gnb is None or target_gnb is None:
        return False

    # Transfer packets (X2/Xn forwarding)
    transfer_packets_on_handover(source_gnb, target_gnb, ue.id)

    # Detach from source
    source_gnb.detach_ue(ue.id)

    # Attach to target
    target_gnb.attach_ue(ue.id)
    ue.serving_gnb_id = target_gnb_id
    ue.reset_handover_timer()

    return True


def process_handovers(
    ues: List[UE],
    gnbs: List[GNodeB],
    gnb_map: Dict[int, GNodeB],
) -> int:
    """
    Process handover decisions for all UEs.
    Implements time-to-trigger to avoid ping-pong.

    Returns:
        Number of handovers executed this step.
    """
    handovers = 0

    for ue in ues:
        if not ue.is_connected():
            # Try to attach if not connected
            initial_attach(ue, gnbs, gnb_map)
            continue

        # Find potential handover target
        target_gnb_id = find_handover_target(ue)

        if target_gnb_id is not None:
            # A3 event triggered
            if ue.handover_target_gnb == target_gnb_id:
                # Same target as before, increment timer
                ue.handover_timer_ms += TIME_STEP_MS

                if ue.handover_timer_ms >= TIME_TO_TRIGGER_MS:
                    # TTT expired, execute handover
                    if execute_handover(ue, target_gnb_id, gnb_map):
                        handovers += 1
            else:
                # New target, start timer
                ue.start_handover_timer(target_gnb_id)
                ue.handover_timer_ms = TIME_STEP_MS
        else:
            # No A3 event, reset timer
            ue.reset_handover_timer()

    return handovers


def process_detachments(
    ues: List[UE],
    gnb_map: Dict[int, GNodeB],
) -> int:
    """
    Detach UEs with very poor signal quality (radio link failure).

    Returns:
        Number of detachments.
    """
    detachments = 0

    for ue in ues:
        if not ue.is_connected():
            continue

        # Check if SINR is below threshold for too long
        # Simple model: immediate detach if RSRP very weak
        if ue.rsrp_dbm < -135 or ue.sinr_db < SINR_THRESHOLD_DB - 10:
            gnb = gnb_map.get(ue.serving_gnb_id)
            if gnb:
                gnb.detach_ue(ue.id)
            ue.serving_gnb_id = None
            ue.reset_handover_timer()
            detachments += 1

    return detachments


def get_association_stats(ues: List[UE], gnbs: List[GNodeB]) -> Dict:
    """Get statistics about current associations."""
    connected = sum(1 for ue in ues if ue.is_connected())
    load_per_gnb = {gnb.id: len(gnb.connected_ues) for gnb in gnbs}

    return {
        "connected_ues": connected,
        "disconnected_ues": len(ues) - connected,
        "load_per_gnb": load_per_gnb,
    }

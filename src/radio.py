"""
Radio propagation model: pathloss, RSRP, and SINR calculations.
Uses simplified 3GPP Urban Macro (UMa) model.
"""
import numpy as np
from typing import List, Dict

from .entities import UE, GNodeB
from .config import (
    GNB_FREQUENCY_GHZ,
    GNB_BANDWIDTH_MHZ,
    THERMAL_NOISE_DBM_PER_HZ,
    UE_NOISE_FIGURE_DB,
    MIN_RSRP_DBM,
)


def calculate_distance(ue: UE, gnb: GNodeB) -> float:
    """Calculate 2D distance between UE and gNodeB in meters."""
    return np.sqrt((ue.x - gnb.x) ** 2 + (ue.y - gnb.y) ** 2)


def calculate_distance_3d(ue: UE, gnb: GNodeB) -> float:
    """Calculate 3D distance including height difference."""
    d_2d = calculate_distance(ue, gnb)
    d_h = gnb.height_m - ue.height_m
    return np.sqrt(d_2d ** 2 + d_h ** 2)


def calculate_pathloss_uma(distance_m: float, frequency_ghz: float = GNB_FREQUENCY_GHZ) -> float:
    """
    Simplified pathloss model based on 3GPP UMa LOS.
    PL = 28 + 22*log10(d) + 20*log10(f)

    Args:
        distance_m: Distance in meters (minimum 10m)
        frequency_ghz: Carrier frequency in GHz

    Returns:
        Pathloss in dB
    """
    # Minimum distance to avoid log(0)
    d = max(distance_m, 10.0)
    f = frequency_ghz  # In GHz

    # Simplified LOS model (more appropriate for small-cell simulation)
    pl = 28.0 + 22.0 * np.log10(d) + 20.0 * np.log10(f)

    return pl


def calculate_rsrp(ue: UE, gnb: GNodeB) -> float:
    """
    Calculate Reference Signal Received Power (RSRP) in dBm.

    RSRP = Tx Power - Pathloss
    """
    distance = calculate_distance_3d(ue, gnb)
    pathloss = calculate_pathloss_uma(distance)
    rsrp = gnb.tx_power_dbm - pathloss

    return max(rsrp, MIN_RSRP_DBM)


def calculate_thermal_noise() -> float:
    """
    Calculate thermal noise power for the channel bandwidth.
    N = kTB in dBm
    """
    bandwidth_hz = GNB_BANDWIDTH_MHZ * 1e6
    noise_dbm = THERMAL_NOISE_DBM_PER_HZ + 10 * np.log10(bandwidth_hz) + UE_NOISE_FIGURE_DB
    return noise_dbm


def calculate_sinr(ue: UE, serving_gnb: GNodeB, all_gnbs: List[GNodeB]) -> float:
    """
    Calculate Signal-to-Interference-plus-Noise Ratio (SINR) in dB.

    SINR = S / (I + N)
    where:
        S = received power from serving cell
        I = sum of interference from other cells
        N = thermal noise
    """
    # Signal power from serving cell (in mW)
    signal_dbm = calculate_rsrp(ue, serving_gnb)
    signal_mw = 10 ** (signal_dbm / 10)

    # Interference from other cells (in mW)
    interference_mw = 0.0
    for gnb in all_gnbs:
        if gnb.id != serving_gnb.id:
            interference_dbm = calculate_rsrp(ue, gnb)
            interference_mw += 10 ** (interference_dbm / 10)

    # Thermal noise (in mW)
    noise_dbm = calculate_thermal_noise()
    noise_mw = 10 ** (noise_dbm / 10)

    # SINR
    sinr_linear = signal_mw / (interference_mw + noise_mw)
    sinr_db = 10 * np.log10(sinr_linear)

    return sinr_db


def update_measurements(ue: UE, gnbs: List[GNodeB]):
    """
    Update UE measurement reports for all gNodeBs.
    Stores RSRP from each cell.
    """
    ue.measurements = {}
    for gnb in gnbs:
        rsrp = calculate_rsrp(ue, gnb)
        ue.measurements[gnb.id] = rsrp


def update_serving_cell_metrics(ue: UE, gnbs: List[GNodeB], gnb_map: Dict[int, GNodeB]):
    """
    Update RSRP and SINR for UE's serving cell.
    """
    if ue.serving_gnb_id is not None and ue.serving_gnb_id in gnb_map:
        serving_gnb = gnb_map[ue.serving_gnb_id]
        ue.rsrp_dbm = calculate_rsrp(ue, serving_gnb)
        ue.sinr_db = calculate_sinr(ue, serving_gnb, gnbs)
    else:
        ue.rsrp_dbm = MIN_RSRP_DBM
        ue.sinr_db = -20.0


def get_best_cell(ue: UE) -> int:
    """
    Get the gNodeB ID with strongest RSRP.
    Returns -1 if no measurements available.
    """
    if not ue.measurements:
        return -1
    return max(ue.measurements, key=ue.measurements.get)


def calculate_spectral_efficiency(sinr_db: float) -> float:
    """
    Approximate spectral efficiency using Shannon capacity.
    SE = log2(1 + SINR) [bits/s/Hz]

    Capped at reasonable values for practical systems.
    """
    sinr_linear = 10 ** (sinr_db / 10)
    se = np.log2(1 + max(sinr_linear, 0.001))
    # Cap at ~8 bits/s/Hz (256-QAM theoretical max)
    return min(se, 8.0)


def calculate_achievable_rate(sinr_db: float) -> float:
    """
    Calculate achievable data rate in Mbps.
    Rate = SE * Bandwidth
    """
    se = calculate_spectral_efficiency(sinr_db)
    bandwidth_hz = GNB_BANDWIDTH_MHZ * 1e6
    rate_bps = se * bandwidth_hz
    rate_mbps = rate_bps / 1e6
    return rate_mbps

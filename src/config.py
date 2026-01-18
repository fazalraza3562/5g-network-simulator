"""
Configuration constants and default parameters for 5G simulation.
"""
import numpy as np

# =============================================================================
# Simulation
# =============================================================================
DEFAULT_SEED = 42
TIME_STEP_MS = 1  # Simulation time step in milliseconds
DEFAULT_STEPS = 500  # Number of simulation steps

# =============================================================================
# Area / Topology
# =============================================================================
AREA_WIDTH = 500.0  # meters
AREA_HEIGHT = 500.0  # meters

# =============================================================================
# gNodeB (Base Station) Parameters
# =============================================================================
DEFAULT_NUM_GNB = 4
GNB_TX_POWER_DBM = 46.0  # Transmission power in dBm
GNB_HEIGHT_M = 25.0  # Antenna height in meters
GNB_FREQUENCY_GHZ = 3.5  # Carrier frequency (n78 band)
GNB_BANDWIDTH_MHZ = 100  # Channel bandwidth
GNB_BUFFER_SIZE = 100  # Max packets in queue per UE

# =============================================================================
# UE (User Equipment) Parameters
# =============================================================================
DEFAULT_NUM_UE = 20
UE_HEIGHT_M = 1.5  # UE antenna height
UE_SPEED_MIN = 5.0  # m/s (jogging)
UE_SPEED_MAX = 30.0  # m/s (fast vehicle)
UE_NOISE_FIGURE_DB = 7.0  # Receiver noise figure

# =============================================================================
# Radio / Pathloss Model (3GPP Urban Macro)
# =============================================================================
THERMAL_NOISE_DBM_PER_HZ = -174.0  # dBm/Hz at 290K
MIN_RSRP_DBM = -140.0  # Minimum detectable signal
SINR_THRESHOLD_DB = -6.0  # Minimum SINR for connection

# =============================================================================
# Handover Parameters
# =============================================================================
HANDOVER_HYSTERESIS_DB = 2.0  # dB margin before handover triggered
TIME_TO_TRIGGER_MS = 20  # TTT in milliseconds
A3_OFFSET_DB = 0.5  # A3 event offset

# =============================================================================
# Traffic Model
# =============================================================================
PACKET_SIZE_BYTES = 1500  # Standard MTU
PACKET_ARRIVAL_RATE = 0.5  # Packets per ms per UE (Poisson rate)
MAX_PACKET_DELAY_MS = 100  # Packets older than this are dropped

# =============================================================================
# Scheduler
# =============================================================================
SUBFRAME_DURATION_MS = 1  # LTE/NR subframe
RESOURCE_BLOCKS_PER_SLOT = 100  # Approximate RBs for 100MHz

# =============================================================================
# Metrics
# =============================================================================
THROUGHPUT_WINDOW_MS = 100  # Window for throughput calculation


class SimConfig:
    """Mutable simulation configuration."""

    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        num_ues: int = DEFAULT_NUM_UE,
        num_gnbs: int = DEFAULT_NUM_GNB,
        num_steps: int = DEFAULT_STEPS,
    ):
        self.seed = seed
        self.num_ues = num_ues
        self.num_gnbs = num_gnbs
        self.num_steps = num_steps
        self.rng = np.random.default_rng(seed)

    def reset_rng(self):
        """Reset RNG to initial seed for reproducibility."""
        self.rng = np.random.default_rng(self.seed)

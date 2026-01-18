"""
Main simulation engine that orchestrates all components.
"""
from typing import List, Dict, Tuple
import numpy as np

from .config import SimConfig, TIME_STEP_MS
from .entities import UE, GNodeB
from .mobility import initialize_ue_positions, update_ue_positions, initialize_gnb_positions
from .radio import update_measurements, update_serving_cell_metrics
from .association import process_handovers, process_detachments, initial_attach
from .traffic import TrafficGenerator, drop_expired_packets
from .scheduler import run_schedulers
from .metrics import MetricsCollector


class Simulator:
    """5G Network Simulator engine."""

    def __init__(self, config: SimConfig):
        self.config = config
        self.current_time_ms = 0

        # Initialize entities
        self.ues: List[UE] = []
        self.gnbs: List[GNodeB] = []
        self.ue_map: Dict[int, UE] = {}
        self.gnb_map: Dict[int, GNodeB] = {}

        # Components
        self.traffic_gen = TrafficGenerator(config)
        self.metrics = MetricsCollector()

        # State tracking
        self.initialized = False

    def setup(self):
        """Initialize the simulation state."""
        print(f"Setting up simulation...")
        print(f"  - {self.config.num_gnbs} gNodeBs")
        print(f"  - {self.config.num_ues} UEs")
        print(f"  - {self.config.num_steps} time steps")
        print(f"  - Seed: {self.config.seed}")

        # Create gNodeBs
        gnb_positions = initialize_gnb_positions(self.config, self.config.num_gnbs)
        self.gnbs = [
            GNodeB(id=i, x=pos[0], y=pos[1])
            for i, pos in enumerate(gnb_positions)
        ]
        self.gnb_map = {g.id: g for g in self.gnbs}

        # Create UEs
        self.ues = [UE(id=i, x=0, y=0, speed=0, direction=0) for i in range(self.config.num_ues)]
        self.ue_map = {u.id: u for u in self.ues}

        # Initialize UE positions
        initialize_ue_positions(self.config, self.ues)

        # Initial measurements and attachments
        for ue in self.ues:
            update_measurements(ue, self.gnbs)

        for ue in self.ues:
            initial_attach(ue, self.gnbs, self.gnb_map)

        # Update serving cell metrics
        for ue in self.ues:
            update_serving_cell_metrics(ue, self.gnbs, self.gnb_map)

        self.initialized = True
        print("Setup complete.\n")

    def step(self) -> Dict:
        """
        Execute one simulation time step.

        Returns:
            Dict with step statistics.
        """
        if not self.initialized:
            self.setup()

        # 1. Update UE positions (mobility)
        update_ue_positions(self.config, self.ues)

        # 2. Update radio measurements
        for ue in self.ues:
            update_measurements(ue, self.gnbs)
            update_serving_cell_metrics(ue, self.gnbs, self.gnb_map)

        # 3. Process handovers
        num_handovers = process_handovers(self.ues, self.gnbs, self.gnb_map)

        # 4. Process detachments (radio link failures)
        process_detachments(self.ues, self.gnb_map)

        # 5. Generate traffic
        packets_generated, packets_dropped_overflow = self.traffic_gen.generate_packets(
            self.ues, self.gnb_map, self.current_time_ms
        )

        # 6. Drop expired packets
        packets_dropped_expired = drop_expired_packets(self.gnbs, self.current_time_ms)

        # 7. Run schedulers
        transmission_results = run_schedulers(
            self.gnbs, self.ue_map, self.current_time_ms, self.config
        )

        # 8. Calculate aggregate stats
        connected_ues = sum(1 for ue in self.ues if ue.is_connected())
        connected_ue_list = [ue for ue in self.ues if ue.is_connected()]

        avg_rsrp = np.mean([ue.rsrp_dbm for ue in connected_ue_list]) if connected_ue_list else -140
        avg_sinr = np.mean([ue.sinr_db for ue in connected_ue_list]) if connected_ue_list else -20

        # 9. Record metrics
        self.metrics.record_step(
            time_ms=self.current_time_ms,
            packets_generated=packets_generated,
            packets_dropped_overflow=packets_dropped_overflow,
            packets_dropped_expired=packets_dropped_expired,
            transmission_results=transmission_results,
            num_handovers=num_handovers,
            connected_ues=connected_ues,
            avg_rsrp_dbm=avg_rsrp,
            avg_sinr_db=avg_sinr,
        )

        # Advance time
        self.current_time_ms += TIME_STEP_MS

        return {
            "time_ms": self.current_time_ms,
            "handovers": num_handovers,
            "connected_ues": connected_ues,
            "packets_generated": packets_generated,
            "packets_delivered": sum(1 for r in transmission_results if r.success),
        }

    def run(self, progress_interval: int = 100) -> MetricsCollector:
        """
        Run the full simulation.

        Args:
            progress_interval: Print progress every N steps.

        Returns:
            MetricsCollector with all recorded metrics.
        """
        if not self.initialized:
            self.setup()

        print("Running simulation...")

        for step_num in range(self.config.num_steps):
            self.step()

            # Progress reporting
            if (step_num + 1) % progress_interval == 0:
                progress = (step_num + 1) / self.config.num_steps * 100
                print(f"  Progress: {progress:.0f}% ({step_num + 1}/{self.config.num_steps})")

        print("Simulation complete.")
        return self.metrics

    def get_state(self) -> Dict:
        """Get current simulation state for inspection."""
        return {
            "time_ms": self.current_time_ms,
            "ues": self.ues,
            "gnbs": self.gnbs,
            "metrics": self.metrics,
        }

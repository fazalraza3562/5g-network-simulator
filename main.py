#!/usr/bin/env python3
"""
5G Network Simulator - CLI Entry Point

Simulates a 5G network with gNodeBs, mobile UEs, handovers,
Round Robin scheduling, and generates performance metrics.

Usage:
    python main.py
    python main.py --ues 60 --gnb 5 --steps 300 --seed 42
"""
import argparse
import os
import sys

from src.config import SimConfig, DEFAULT_SEED, DEFAULT_NUM_UE, DEFAULT_NUM_GNB, DEFAULT_STEPS
from src.simulator import Simulator
from src.visualization import generate_all_plots


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="5G Network Simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--ues",
        type=int,
        default=DEFAULT_NUM_UE,
        help="Number of UEs (user equipment)",
    )

    parser.add_argument(
        "--gnb",
        type=int,
        default=DEFAULT_NUM_GNB,
        help="Number of gNodeBs (base stations)",
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_STEPS,
        help="Number of simulation time steps (ms)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output directory for plots",
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating plots",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("5G NETWORK SIMULATOR")
    print("=" * 60)

    # Create configuration
    config = SimConfig(
        seed=args.seed,
        num_ues=args.ues,
        num_gnbs=args.gnb,
        num_steps=args.steps,
    )

    # Create and run simulator
    sim = Simulator(config)
    sim.setup()
    metrics = sim.run(progress_interval=max(1, args.steps // 10))

    # Print summary
    metrics.print_summary()

    # Generate plots
    if not args.no_plots:
        output_dir = os.path.abspath(args.output)
        generate_all_plots(
            ues=sim.ues,
            gnbs=sim.gnbs,
            metrics=metrics,
            output_dir=output_dir,
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

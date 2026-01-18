"""
Mobility models for UE movement.
"""
import numpy as np
from typing import List

from .entities import UE
from .config import (
    AREA_WIDTH,
    AREA_HEIGHT,
    UE_SPEED_MIN,
    UE_SPEED_MAX,
    TIME_STEP_MS,
    SimConfig,
)


def initialize_ue_positions(config: SimConfig, ues: List[UE]):
    """
    Initialize UE positions randomly within the simulation area.
    Also sets initial speed and direction.
    """
    rng = config.rng
    for ue in ues:
        ue.x = rng.uniform(0, AREA_WIDTH)
        ue.y = rng.uniform(0, AREA_HEIGHT)
        ue.speed = rng.uniform(UE_SPEED_MIN, UE_SPEED_MAX)
        ue.direction = rng.uniform(0, 2 * np.pi)


def update_ue_positions(config: SimConfig, ues: List[UE]):
    """
    Update UE positions using Random Walk with reflection at boundaries.
    Each UE moves in its current direction at its speed.
    Direction changes slightly each step (Gaussian perturbation).
    """
    rng = config.rng
    dt_s = TIME_STEP_MS / 1000.0  # Convert ms to seconds

    for ue in ues:
        # Add small random perturbation to direction (smooth turns)
        ue.direction += rng.normal(0, 0.1)

        # Calculate displacement
        dx = ue.speed * dt_s * np.cos(ue.direction)
        dy = ue.speed * dt_s * np.sin(ue.direction)

        # Update position
        new_x = ue.x + dx
        new_y = ue.y + dy

        # Reflect at boundaries
        if new_x < 0:
            new_x = -new_x
            ue.direction = np.pi - ue.direction
        elif new_x > AREA_WIDTH:
            new_x = 2 * AREA_WIDTH - new_x
            ue.direction = np.pi - ue.direction

        if new_y < 0:
            new_y = -new_y
            ue.direction = -ue.direction
        elif new_y > AREA_HEIGHT:
            new_y = 2 * AREA_HEIGHT - new_y
            ue.direction = -ue.direction

        # Clamp to bounds (safety)
        ue.x = np.clip(new_x, 0, AREA_WIDTH)
        ue.y = np.clip(new_y, 0, AREA_HEIGHT)

        # Occasionally change speed slightly
        if rng.random() < 0.01:  # 1% chance per step
            ue.speed = rng.uniform(UE_SPEED_MIN, UE_SPEED_MAX)


def initialize_gnb_positions(config: SimConfig, num_gnbs: int) -> List[tuple]:
    """
    Generate gNodeB positions in a grid-like pattern for coverage.
    Returns list of (x, y) tuples.
    """
    positions = []

    if num_gnbs == 1:
        # Single gNB at center
        positions.append((AREA_WIDTH / 2, AREA_HEIGHT / 2))
    elif num_gnbs <= 4:
        # 2x2 grid pattern
        margin = 0.2  # 20% margin from edges
        x_positions = [
            AREA_WIDTH * margin,
            AREA_WIDTH * (1 - margin),
        ]
        y_positions = [
            AREA_HEIGHT * margin,
            AREA_HEIGHT * (1 - margin),
        ]
        for i in range(num_gnbs):
            x_idx = i % 2
            y_idx = i // 2
            positions.append((x_positions[x_idx], y_positions[y_idx % 2]))
    else:
        # Grid pattern for larger numbers
        cols = int(np.ceil(np.sqrt(num_gnbs)))
        rows = int(np.ceil(num_gnbs / cols))
        x_spacing = AREA_WIDTH / (cols + 1)
        y_spacing = AREA_HEIGHT / (rows + 1)

        count = 0
        for row in range(rows):
            for col in range(cols):
                if count >= num_gnbs:
                    break
                x = x_spacing * (col + 1)
                y = y_spacing * (row + 1)
                positions.append((x, y))
                count += 1

    return positions

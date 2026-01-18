Made by: Muhammad Fazal Raza
Karlskrona, Sweden

# 5G Network Simulator

A simple 5G network simulator I built to understand how base stations, user devices, and handovers work together. Nothing fancy, just the core stuff that actually matters for interviews and learning.

## What it does

Simulates a small 5G network with:
- gNodeBs (base stations) placed in a grid
- UEs (phones/devices) moving around randomly
- Handover when a device gets closer to another tower
- Basic packet scheduling (Round Robin)
- Tracks latency, throughput, packet loss

## Quick start

```
pip install -r requirements.txt
python main.py
```

That's it. Check the `outputs/` folder for the plots.

## CLI options

```
python main.py --ues 40 --gnb 5 --steps 10000 --seed 123
```

- `--ues`: number of user devices (default 20)
- `--gnb`: number of base stations (default 4)
- `--steps`: simulation duration in ms (default 500)
- `--seed`: random seed for reproducibility

## Project structure

```
main.py           <- run this
src/
  config.py       <- all the constants, tweak stuff here
  entities.py     <- UE and gNodeB classes
  mobility.py     <- how devices move around
  radio.py        <- signal strength, pathloss, SINR calc
  association.py  <- handover logic (A3 event + hysteresis)
  scheduler.py    <- round robin packet scheduling
  traffic.py      <- generates fake network traffic
  metrics.py      <- collects all the stats
  visualization.py <- makes the plots
  simulator.py    <- ties everything together
outputs/          <- plots go here
```

## How handover works

Uses the 3GPP A3 event approach:
1. UE constantly measures signal from all nearby towers
2. If neighbor signal > serving signal + hysteresis (2dB), start a timer
3. If condition holds for TTT (20ms), do the handover
4. This prevents ping-pong between cells

## Sample output

```
Packets Generated:    599,976
Packets Delivered:    482,412
Loss Rate:            19.59%
Avg Latency:          1.05 ms
P95 Latency:          1.91 ms
Avg Throughput:       194.57 Mbps
Total Handovers:      8
```

## Things I might add later

- Different scheduler types (proportional fair, etc)
- Uplink traffic
- More realistic mobility (roads, waypoints)
- Multiple carriers

## Dependencies

- Python 3.11+
- numpy
- networkx
- matplotlib

## Notes

The pathloss model is simplified (based on 3GPP UMa LOS). Real networks are way more complicated with fading, interference management, beamforming, etc. This is just meant to show the basic concepts work.

Simulation runs at 1ms time steps. For a 30 second sim with 40 UEs, takes maybe 10-15 seconds on my machine.

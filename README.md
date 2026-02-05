# Routing with ART

Routing with ART is a reinforcement learning--based routing framework
integrated with a P4 programmable network. Each switch runs its own RL
environment, receiving network state via P4 digests and interacting
through P4Runtime.

## Overview

The system consists of: - A **P4 network** that generates packet
digests\
- A **P4Runtime interface** that forwards digests to user space\
- A **reinforcement learning (RL) environment**, running one process per
switch, that learns routing decisions

## Requirements

-   P4 development environment (e.g., BMv2, P4Runtime)
-   Python 3.x

## Project Structure

    Routing_ART/
    ├── p4src/                 # P4 programs and Makefile
    ├── main.py             # Entry point for the RL environment
    ├── README.md
    └── ...

## How to Run

### 1. Start the P4 Network

Navigate to the `p4` folder and start the P4 network:

``` bash
make
```

This compiles the P4 program and launches the network (switches,
topology, etc.).

### 2. Start the RL Environment

From command line, run:

``` bash
python main.py
```

This will: - Initialize the reinforcement learning framework - Spawn
**one RL process per switch** - Connect each process to its
corresponding switch via P4Runtime

### 3. Send Packets

Generate traffic in the network (e.g., using Mininet hosts or traffic
generators).

Packet processing flow: 1. Packets are processed by the P4 data plane\
2. Relevant information is exported as **P4 digests**\
3. Digests are sent to **P4Runtime**\
4. P4Runtime forwards them to the **RL environment**\
5. The RL agent updates routing decisions

## Notes

-   Ensure the P4 network is fully running before starting `main.py`
-   Logs and debug output can help verify digest delivery and RL
    interactions
-   Each switch operates independently but can be extended to support
    coordination

## Future Improvements

-   Centralized training with distributed execution
-   Support for additional reward functions
-   Visualization of routing decisions and learning progress

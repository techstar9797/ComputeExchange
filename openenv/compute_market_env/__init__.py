"""
ComputeMarketEnv - OpenEnv Multi-Agent Compute Marketplace

An OpenEnv environment for training and evaluating agents that orchestrate
compute resource allocation across multiple providers.

Episode: Enterprise workload submission → characterization → negotiation → 
         planning → human approval → execution → learning

This environment supports:
- Multi-agent orchestration (workload, negotiation, planning, execution agents)
- Human-in-the-loop approval workflows
- Shaped rewards for RL training
- Trajectory export for post-training (GRPO, TorchForge)
"""

from .types_export import (
    ComputeMarketAction,
    ComputeMarketObservation,
    ComputeMarketState,
)
from .client import ComputeMarketEnv

__all__ = [
    "ComputeMarketEnv",
    "ComputeMarketAction",
    "ComputeMarketObservation", 
    "ComputeMarketState",
]

__version__ = "0.1.0"

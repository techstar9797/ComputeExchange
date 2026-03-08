# ComputeMarketEnv

An OpenEnv environment for training and evaluating agents that orchestrate compute resource allocation across multiple providers.

## Overview

ComputeMarketEnv simulates a realistic compute resource marketplace where AI agents must:

1. **Characterize Workloads** - Parse and decompose incoming compute workloads into executable stages
2. **Negotiate with Providers** - Request quotes and negotiate pricing with multiple compute providers
3. **Generate Optimized Plans** - Create execution plans balancing cost, performance, reliability, and carbon footprint
4. **Seek Human Approval** - Present plans for human-in-the-loop approval workflow
5. **Execute and Learn** - Simulate execution and learn from outcomes for continuous improvement

## Installation

```bash
# Install the client
pip install git+https://github.com/compute-exchange/compute-market-env

# Or for development
pip install -e ".[dev]"
```

## Quick Start

### Connect to a Running Server

```python
from compute_market_env import ComputeMarketEnv, WorkloadSpec, WorkloadType, OptimizationWeights

# Synchronous usage
with ComputeMarketEnv(base_url="http://localhost:8001").sync() as env:
    # Reset for new episode
    obs = env.reset(scenario_id="llm_training_7b")
    
    # Characterize workload
    workload = WorkloadSpec(
        name="My-Training-Job",
        workload_type=WorkloadType.LLM_TRAINING,
        model_size_gb=30,
        deadline_hours=48,
        budget_usd=3000,
        optimization_weights=OptimizationWeights(cost=0.4, latency=0.2, reliability=0.4),
    )
    obs = env.characterize_workload(workload)
    
    # Request quotes from providers
    obs = env.request_quotes()
    print(f"Received {len(obs.current_offers)} offers")
    
    # Generate execution plan
    obs = env.generate_plan("balanced")
    print(f"Generated {len(obs.plan_candidates)} plans")
    
    # Submit for approval
    best_plan = obs.plan_candidates[0]
    obs = env.submit_for_approval(best_plan.id, "Cost-optimized training plan")
    
    # Approve and execute
    obs = env.approve_plan(best_plan.id)
    obs = env.execute_plan(best_plan.id)
    
    # Finalize and get reward
    result = env.finalize_episode()
    print(f"Episode reward: {result.reward}")
```

### Run the Server Locally

```bash
# Using uvicorn
uvicorn server.app:app --reload --port 8001

# Using Docker
docker build -t compute-market-env .
docker run -p 8001:8001 compute-market-env
```

## Environment API

### Actions

| Action | Description |
|--------|-------------|
| `characterize_workload` | Analyze and decompose a workload specification |
| `request_quotes` | Request pricing quotes from providers |
| `counter_offer` | Counter a provider's offer |
| `switch_strategy` | Change negotiation strategy |
| `generate_plan` | Generate execution plans (cheapest/fastest/balanced/greenest) |
| `submit_for_approval` | Submit plan for human approval |
| `revise_plan` | Revise plan based on feedback |
| `approve_plan` | Human action to approve plan |
| `reject_plan` | Human action to reject plan |
| `execute_plan` | Execute an approved plan |
| `finalize_episode` | Complete episode and get final reward |

### Observation Space

```python
class ComputeMarketObservation:
    done: bool
    reward: float
    episode_id: str
    step_count: int
    workload: WorkloadSpec
    decomposition: WorkloadDecomposition
    current_offers: list[ProviderOffer]
    plan_candidates: list[ExecutionPlan]
    approval_status: ApprovalDecision
    execution_state: ExecutionState
    reward_breakdown: dict[str, float]
    hints: list[str]
```

### Reward Structure

The environment uses **shaped rewards** with both intermediate and delayed components:

**Positive Rewards:**
- Lower cost relative to budget
- Faster execution relative to deadline
- Meeting SLA requirements
- Correct workload-resource matching
- Human approval on first try
- Accurate predictions (estimated vs actual)

**Penalties:**
- Budget overrun
- Deadline miss
- Execution failure
- Excessive negotiation rounds
- Plan rejection
- Poor resource matching

## Scenarios

Pre-built scenarios for demos and benchmarking:

| ID | Name | Difficulty |
|----|------|------------|
| `llm_training_7b` | LLM Training - 7B Parameters | Medium |
| `realtime_inference` | Real-time Inference API | Hard |
| `batch_analytics` | Batch Analytics Pipeline | Easy |
| `multimodal_pipeline` | Multimodal AI Pipeline | Hard |
| `green_training` | Carbon-Neutral Model Training | Medium |

## Training with TorchForge/TRL

```python
from torchforge import GRPO
from compute_market_env import ComputeMarketEnv

# Export trajectories for training
env = ComputeMarketEnv(base_url="http://localhost:8001")
# ... run episodes ...
trajectories = env.get_trajectory()

# Use with TorchForge GRPO
trainer = GRPO(
    model=model,
    tokenizer=tokenizer,
    env=env,
)
trainer.train()
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Enterprise Client                     │
│         (Submits workloads, approves plans)             │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              ComputeMarketEnv (OpenEnv)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Workload     │  Negotiation  │  Planning       │   │
│  │  Characterizer│  Agent        │  Agent          │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Market Simulator  │  Reward Engine              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Provider Agents                         │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │ Nebius │ │  AWS   │ │Lambda  │ │CoreWeave│ │Google │ Azure │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
└─────────────────────────────────────────────────────────┘
```

## License

MIT

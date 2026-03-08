# ComputeExchange

**The Expedia / Airbnb / Uber of Compute Resources**

An OpenEnv-native multi-agent compute marketplace where AI agents orchestrate workload characterization, provider negotiation, plan optimization, and human-in-the-loop approval workflows.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![TorchForge](https://img.shields.io/badge/TorchForge-Ready-orange)](https://github.com/meta-pytorch/torchforge)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

ComputeExchange solves the complex problem of optimal compute resource allocation:

1. **Enterprise submits a workload** with optimization preferences (cost, latency, throughput, energy, reliability)
2. **AI agents characterize the workload** and decompose it into executable stages
3. **Multiple provider agents compete** through negotiation rounds
4. **Planning agent generates optimized execution plans** balancing all constraints
5. **Human reviews and approves** the plan with full transparency
6. **System executes, measures, and learns** from the outcome

This is built as a **real OpenEnv environment** with proper Gymnasium-style APIs (`reset()`, `step()`, `state()`), shaped rewards, and trajectory export for RL post-training. **Phase 7** adds a learning agent that recommends negotiation strategies from episode history; **Phase 8** provides deployment docs and trajectory validation for GRPO/TRL.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Landing   │ │  Workload   │ │Orchestration│ │   Approval  │   │
│  │    Page     │ │ Submission  │ │  Dashboard  │ │   Workflow  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────────┐
│                      API Server (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Session Management & Orchestration              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│               ComputeMarketEnv (OpenEnv Environment)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Workload   │ │ Negotiation  │ │   Planning   │                │
│  │Characterizer │ │    Agent     │ │    Agent     │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Market     │ │   Reward     │ │   Scenario   │                │
│  │  Simulator   │ │   Engine     │ │  Generator   │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       Provider Agents                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ NeoCloud │ │DataCenter│ │HyperScale│ │Edge NPU  │ │  Green   │  │
│  │   GPU    │ │   CPU    │ │  Cloud   │ │ Provider │ │Datacenter│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js >= 18
- Python >= 3.10
- npm or pnpm

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/compute-exchange.git
cd compute-exchange

# Install all dependencies
make install

# Or manually:
npm install
pip install -r apps/api/requirements.txt
cd openenv/compute_market_env && pip install -e .
```

### Running Locally

```bash
# Start everything (frontend + API + OpenEnv server)
make dev

# Or start individually:
make dev-web      # Next.js frontend on http://localhost:3000
make dev-api      # FastAPI backend on http://localhost:8000
make dev-env      # OpenEnv server on http://localhost:8001
```

### Demo Flow

1. Open http://localhost:3000
2. Click "Submit Workload"
3. Configure workload (or use demo defaults)
4. Watch agents negotiate with providers
5. Review and approve generated plans
6. See execution results and rewards

## Project Structure

```
compute-exchange/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/            # App router pages
│   │   │   ├── components/     # React components
│   │   │   └── lib/            # Utilities, API client, store
│   │   └── package.json
│   └── api/                    # FastAPI backend
│       ├── main.py             # API server
│       └── requirements.txt
├── packages/
│   └── shared-types/           # Shared Pydantic models
│       ├── models.py           # All data contracts
│       └── pyproject.toml
├── openenv/
│   └── compute_market_env/     # OpenEnv environment
│       ├── __init__.py
│       ├── client.py           # Environment client
│       ├── models.py           # Environment types
│       ├── openenv.yaml        # OpenEnv manifest
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── server/
│           ├── app.py          # FastAPI server
│           ├── environment.py  # Core environment logic
│           ├── market_simulator.py
│           ├── reward_engine.py
│           └── scenario_generator.py
├── agents/                     # (Phase 2) Agent implementations
├── data/
│   ├── scenarios/              # Demo scenarios
│   ├── provider_profiles/      # Provider configurations
│   └── run_history/            # Episode logs
├── docs/
│   ├── architecture.md
│   └── demo-script.md
├── Makefile
├── package.json
└── README.md
```

## OpenEnv Integration

ComputeExchange is built as a proper OpenEnv environment:

### Episode Flow

```python
from compute_market_env import ComputeMarketEnv, WorkloadSpec

with ComputeMarketEnv(base_url="http://localhost:8001").sync() as env:
    # Start new episode
    obs = env.reset(scenario_id="llm_training_7b")
    
    # Phase 1: Characterize workload
    obs = env.characterize_workload(workload_spec)
    print(f"Decomposed into {len(obs.decomposition.stages)} stages")
    
    # Phase 2: Negotiate with providers
    obs = env.request_quotes()
    print(f"Received {len(obs.current_offers)} offers")
    
    # Phase 3: Generate plans
    obs = env.generate_plan("balanced")
    best_plan = obs.plan_candidates[0]
    
    # Phase 4: Human approval
    obs = env.submit_for_approval(best_plan.id, "Cost-optimized plan")
    obs = env.approve_plan(best_plan.id)
    
    # Phase 5: Execute
    obs = env.execute_plan(best_plan.id)
    
    # Phase 6: Finalize and get reward
    result = env.finalize_episode()
    print(f"Episode reward: {result.reward}")
    
    # Export trajectory for training
    trajectory = env.get_trajectory()
```

### Actions

| Action | Description |
|--------|-------------|
| `characterize_workload` | Analyze and decompose workload |
| `request_quotes` | Get offers from providers |
| `counter_offer` | Counter a provider's offer |
| `switch_strategy` | Change negotiation strategy |
| `generate_plan` | Generate execution plans |
| `submit_for_approval` | Submit plan for human review |
| `approve_plan` / `reject_plan` | Human decision |
| `execute_plan` | Execute approved plan |
| `finalize_episode` | Complete episode, get reward |

### Reward Structure

**Shaped rewards** throughout the episode:
- Characterization quality
- Negotiation efficiency
- Plan optimization score
- Approval likelihood

**Delayed reward** after execution:
- Cost efficiency vs budget
- Time efficiency vs deadline
- SLA compliance
- Prediction accuracy

### Training Ready

Export trajectories for post-training:

```python
# TorchForge GRPO
from torchforge import GRPO
trainer = GRPO(model=model, env=ComputeMarketEnv(...))
trainer.train()

# HuggingFace TRL
from trl import GRPOTrainer
trainer = GRPOTrainer(model=model, tokenizer=tokenizer)
```

## Scenarios

Pre-built scenarios for demos and benchmarks:

| Scenario | Difficulty | Focus |
|----------|------------|-------|
| `llm_training_7b` | Medium | GPU-intensive LLM training |
| `realtime_inference` | Hard | Low-latency, high-reliability |
| `batch_analytics` | Easy | Cost-optimized batch processing |
| `multimodal_pipeline` | Hard | Complex multi-stage pipeline |
| `green_training` | Medium | Carbon-neutral compute |

## Metrics

### Enterprise Metrics
- Predicted vs actual cost
- Predicted vs actual duration
- SLA compliance rate
- Cost savings vs baseline

### Provider Metrics
- Acceptance rate
- Utilization
- Profit margin
- Win rate

### System Metrics
- Approval rate
- Regret vs oracle
- Prediction accuracy
- Negotiation efficiency

### RL Metrics
- Episode reward
- Average reward over N episodes
- Strategy-wise performance
- Learning curve

## Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Zustand
- TanStack Query

**Backend:**
- Python 3.10+
- FastAPI
- Pydantic v2
- WebSockets

**OpenEnv:**
- OpenEnv-compatible server
- Gymnasium-style API
- Docker deployment ready
- HuggingFace Spaces compatible

## Hackathon Positioning

This project demonstrates:

1. **OpenEnv Environment** - Not just a chat app, but a real environment with actions, observations, and rewards
2. **Multi-Agent System** - Multiple specialized agents working together
3. **Human-in-the-Loop** - Meaningful human oversight in the approval workflow
4. **Measurable Outcomes** - Clear metrics and reward signals
5. **Training Ready** - Trajectories exportable for GRPO/TRL post-training
6. **Production Quality** - Full-stack implementation with polished UI

## Development

```bash
# Run tests
make test

# Lint
make lint

# Build Docker image
make docker-build

# Clean
make clean
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for the full guide.

### Docker

```bash
make docker-build
make docker-run
```

### Trajectory Validation (RL Training)

```bash
make validate-trajectory
```

### HuggingFace Spaces

The OpenEnv environment can be deployed to HuggingFace Spaces:

```bash
openenv push --repo-id your-org/compute-market-env
```

## License

MIT

## Acknowledgments

Built for the [OpenEnv Hackathon SF 2026](https://cerebralvalley.ai/e/openenv-hackathon-sf/details).

Powered by:
- [OpenEnv](https://github.com/meta-pytorch/OpenEnv)
- [TorchForge](https://github.com/meta-pytorch/torchforge)

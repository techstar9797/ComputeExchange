# ComputeExchange Architecture

## System Overview

ComputeExchange is a multi-agent compute marketplace built as an OpenEnv environment. It simulates the complete lifecycle of compute resource allocation, from workload submission to execution and learning.

## Core Components

### 1. Frontend (Next.js)

A premium dark-themed dashboard with:
- **Landing Page**: Platform introduction and CTA
- **Workload Submission**: Form to configure workloads
- **Orchestration Dashboard**: Live negotiation and planning
- **Approval Workflow**: Human-in-the-loop decision making
- **Execution View**: Real-time execution tracking
- **Analytics**: Learning metrics and history

**Tech Stack:**
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS + shadcn/ui
- Framer Motion for animations
- Zustand for state management
- TanStack Query for server state

### 2. API Server (FastAPI)

Backend orchestration layer that:
- Manages user sessions
- Proxies requests to OpenEnv environment
- Provides REST and WebSocket endpoints
- Aggregates analytics

**Endpoints:**
- `POST /workload/submit` - Submit new workload
- `POST /session/{id}/negotiate` - Start negotiation
- `POST /plans/generate` - Generate plans
- `POST /plans/approve` - Human approval
- `POST /execution/start` - Execute plan
- `GET /analytics/metrics` - Get metrics

### 3. OpenEnv Environment (ComputeMarketEnv)

The core environment implementing OpenEnv APIs:

```python
class ComputeMarketEnvironment:
    def reset(self, seed, episode_id, scenario_id) -> Observation
    def step(self, action) -> Observation
    @property
    def state(self) -> State
```

**Episode Phases:**
1. Initialization
2. Characterization
3. Negotiation
4. Planning
5. Approval
6. Execution
7. Finalization

### 4. Market Simulator

Simulates realistic market conditions:
- Variable spot pricing
- Provider capacity constraints
- Negotiation dynamics
- Execution variance

### 5. Reward Engine

Computes shaped rewards:

**Intermediate Rewards:**
- Characterization quality
- Negotiation efficiency
- Plan diversity
- Approval likelihood

**Final Reward:**
- Cost efficiency
- Time efficiency
- SLA compliance
- Prediction accuracy

### 6. Provider Agents

Simulated providers with different characteristics:
- **NeoCloud Alpha**: GPU-focused, aggressive negotiation
- **DataCenter Prime**: CPU-focused, defensive, high reliability
- **HyperScale Cloud**: Balanced, global presence
- **Edge Neural**: NPU-focused, low latency
- **Green Compute**: 100% renewable, cooperative

## Data Flow

```
User Input
    │
    ▼
┌─────────────┐
│  Frontend   │
│  (Next.js)  │
└─────┬───────┘
      │ REST/WebSocket
      ▼
┌─────────────┐
│  API Server │
│  (FastAPI)  │
└─────┬───────┘
      │
      ▼
┌─────────────────────────────────┐
│     ComputeMarketEnv            │
│                                 │
│  ┌─────────────────────────┐    │
│  │   Workload Characterizer│    │
│  └───────────┬─────────────┘    │
│              │                  │
│  ┌───────────▼─────────────┐    │
│  │   Negotiation Agent     │◄───┼─── Provider Agents
│  └───────────┬─────────────┘    │
│              │                  │
│  ┌───────────▼─────────────┐    │
│  │   Planning Agent        │    │
│  └───────────┬─────────────┘    │
│              │                  │
│  ┌───────────▼─────────────┐    │
│  │   Human Approval        │◄───┼─── User Decision
│  └───────────┬─────────────┘    │
│              │                  │
│  ┌───────────▼─────────────┐    │
│  │   Execution Simulator   │    │
│  └───────────┬─────────────┘    │
│              │                  │
│  ┌───────────▼─────────────┐    │
│  │   Reward Engine         │    │
│  └───────────┬─────────────┘    │
│              │                  │
│         Trajectory              │
└─────────────────────────────────┘
```

## OpenEnv Alignment

### Gymnasium-Style API

```python
# Reset for new episode
observation = env.reset(scenario_id="llm_training_7b")

# Step through episode
for action in agent_policy(observation):
    observation = env.step(action)
    if observation.done:
        break
```

### Action Space

```python
ActionType = Literal[
    "characterize_workload",
    "request_quotes",
    "counter_offer",
    "switch_strategy",
    "generate_plan",
    "submit_for_approval",
    "revise_plan",
    "approve_plan",
    "reject_plan",
    "execute_plan",
    "finalize_episode",
]
```

### Observation Space

```python
@dataclass
class ComputeMarketObservation:
    done: bool
    reward: float
    episode_id: str
    step_count: int
    workload: WorkloadSpec
    decomposition: WorkloadDecomposition
    current_offers: List[ProviderOffer]
    plan_candidates: List[ExecutionPlan]
    approval_status: ApprovalDecision
    execution_state: ExecutionState
    reward_breakdown: Dict[str, float]
    hints: List[str]
```

### Trajectory Format

```json
{
  "episode_id": "abc123",
  "steps": [
    {
      "step": 1,
      "phase": "characterization",
      "action": {"action_type": "characterize_workload", ...},
      "observation": {...},
      "reward": 0.1,
      "timestamp": "2026-03-07T12:00:00Z"
    },
    ...
  ],
  "total_reward": 0.45,
  "metadata": {...}
}
```

## Training Integration

### TorchForge GRPO

```python
from torchforge import GRPO

trainer = GRPO(
    model=model,
    tokenizer=tokenizer,
    env=ComputeMarketEnv(base_url="http://localhost:8001"),
    reward_model=None,  # Uses environment reward
)
trainer.train(num_episodes=1000)
```

### HuggingFace TRL

```python
from trl import GRPOTrainer, GRPOConfig

config = GRPOConfig(
    output_dir="./compute-exchange-model",
    per_device_train_batch_size=4,
)

trainer = GRPOTrainer(
    model=model,
    args=config,
    tokenizer=tokenizer,
    # Custom environment integration
)
```

## Scalability Considerations

- Session-based environment isolation
- WebSocket for real-time updates
- Docker containerization
- Horizontal scaling via container orchestration
- Trajectory storage for offline training

## Future Enhancements

1. **Phase 1-6**: Complete agent implementations
2. **LLM Integration**: Swap rule-based agents for LLM-backed
3. **Real Provider APIs**: Connect to actual cloud providers
4. **Distributed Execution**: Multi-node training support
5. **Advanced Baselines**: Oracle and heuristic comparisons

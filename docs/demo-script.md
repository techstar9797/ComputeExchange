# ComputeExchange Demo Script

**Duration:** 2-3 minutes

## Opening (15 seconds)

"This is ComputeExchange - the Expedia for compute resources. We're solving the problem of optimal GPU and compute allocation using multi-agent AI orchestration."

## The Problem (20 seconds)

"Today, enterprises waste millions on suboptimal compute allocation:
- Manual provider selection
- No negotiation leverage  
- One-size-fits-all plans
- No learning from past decisions

We fix this with AI agents that characterize your workload, negotiate with providers, and generate optimal plans."

## Live Demo (90 seconds)

### 1. Submit Workload (20s)

*Navigate to Submit Workload page*

"Let's train a 7B parameter LLM. I specify my deadline, budget, and optimization preferences - I want to balance cost and performance."

*Click Submit*

### 2. Watch Agents Work (30s)

*Show Orchestration Dashboard*

"Watch what happens:
1. Our characterization agent decomposes the workload into stages - data loading, training, checkpointing
2. The negotiation agent requests quotes from 5 different providers
3. Each provider responds with pricing based on their capacity and strategy
4. Our planning agent combines these into optimized execution plans"

*Point to the different panels*

### 3. Human Approval (20s)

*Show Approval Page*

"Here's the human-in-the-loop. I see:
- Total cost: $2,400 - that's 52% under my budget
- Duration: 68 hours - within my 72-hour deadline
- Clear risk assessment
- Why this plan was chosen

I approve."

### 4. Execution & Results (20s)

*Show Execution Page*

"The system executes, compares predicted vs actual metrics, and generates a reward signal. This entire interaction becomes a training trajectory we can use for GRPO post-training."

### 5. Learning & Analytics (Optional)

*Show Analytics → Learning tab*

"Our learning agent analyzes episode history and recommends negotiation strategies by workload type. You can see trends, confidence scores, and actionable tips."

## OpenEnv Alignment (30 seconds)

"This is built as a real OpenEnv environment:
- Gymnasium-style reset/step/state API
- Typed actions and observations
- Shaped rewards throughout
- Trajectories export to TorchForge or TRL

Every episode makes the system smarter."

## Closing (15 seconds)

"ComputeExchange: AI agents that save you 40-60% on compute while meeting your SLAs. Built on OpenEnv for continuous improvement."

---

## Key Points to Emphasize

1. **Multi-Agent**: Not one model - multiple specialized agents
2. **Human-in-the-Loop**: Real approval workflow, not just automation
3. **Measurable**: Clear rewards and metrics
4. **Trainable**: OpenEnv compatible for GRPO training
5. **Production Quality**: Full-stack implementation

## Demo Preparation Checklist

- [ ] API server running on localhost:8000
- [ ] OpenEnv server running on localhost:8001
- [ ] Frontend running on localhost:3000
- [ ] `make dev` or `make demo` to start all services
- [ ] Demo scenario pre-loaded
- [ ] Browser in dark mode
- [ ] Screen recording ready if needed

## Quick Start

```bash
make install && make dev
# Open http://localhost:3000
```

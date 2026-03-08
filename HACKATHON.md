# OpenEnv Hackathon (March 2026) – ComputeExchange

**Submissions due:** Sunday, March 8th, 1:00 PM  
**Rules:** All work must be original · Team size: up to 3 · Respect the Space

## Prizes

| Place   | Amount   |
|--------|----------|
| First  | $15,000 USD |
| Second | $9,000 USD  |
| Third  | $6,000 USD  |

Partner sub-theme prizes: **$10,000 USD each** (judged separately). Projects that match partner sub-problem statements are eligible.

---

## Hackathon themes (from Opening Slides)

### 1. Multi-Agent Interactions
Multiple agents competing/collaborating; cooperation, competition, negotiation, coalition formation.  
**Expected outcome:** Environment to train multi-agent task handling in an LLM.  
**Examples:** Market simulations, **compute-allocation negotiations**, collaborative puzzle worlds, strategy games.

### 2. Long-Horizon Planning & Instruction Following
Deep multi-step reasoning, sparse/delayed rewards; decompose goals, track state, recover from mistakes.  
**Expected outcome:** Improve LLM behaviour on long-horizon tasks beyond context limits.  
**Examples:** Research-planning simulators, codebase refactoring, **strategic resource management worlds**, long-horizon logistics.

### 3.1 World Modeling – Professional Tasks
Real interaction with tools/APIs; consistent internal state, multi-step workflows.  
**Examples:** Dynamic browser/API ecosystems, **enterprise applications**, scientific workflow loops.

### 3.2 World Modeling – Personalized Tasks
Personal assistant–style tasks: calendar, email, messages, conflicts, delegations.  
**Examples:** Meeting planner, email/message replying.

### 4. Self-Improvement
Agents generate new challenges, escalate difficulty, self-play, adaptive curricula.  
**Examples:** Self-play negotiation arenas, auto-generated tasks, adaptive RL curricula.

### 5. Wild Card – Impress us!

---

## Partner sub-themes ($10k each)

| Partner       | Theme              | Bonus sub-theme |
|---------------|--------------------|------------------|
| **Fleet AI**  | Multi-Agent        | Scalable Oversight: train oversight agents to monitor, analyze, explain other AI agents in complex multi-agent settings. |
| **Mercor**    | Long-Horizon       | Capped/uncapped rewards; frontier model rewards scale with token output. |
| **Mercer**    | Long-Horizon       | Long-horizon workflows for non-code use cases: Sales, Project management, or HR & IT. |
| **Scaler AI Labs** | World (Professional) | Multi-App RL Environment for Enterprise: complex workflows, business-rule nuances. |
| **Patronus AI**    | World (Personalized) | Consumer workflows with schema drift: multi-step workflows where data schemas, API contracts, policies change. |
| **Halluminate AI** | Multi-Agent        | Multi-Actor: agent interacts with and manages multiple actors to discover and achieve the task. |
| **Snorkel AI**     | Self-Improvement   | Simulated Experts-in-the-Loop: environment that simulates interactions with subject-matter experts, changing requirements/preferences. |

---

## How ComputeExchange fits

- **Theme 1 (Multi-Agent):** Market simulations, **compute-allocation negotiations**, multiple provider agents + orchestration agents.
- **Theme 2 (Long-Horizon):** Multi-step episodes (characterize → negotiate → plan → approve → execute), **strategic resource management**, delayed/shaped rewards.
- **Theme 3.1 (World – Professional):** **Enterprise** workload submission, APIs, multi-step workflows, tool/API-style interaction.
- **Theme 4 (Self-Improvement):** Learning agent from episode history; trajectory export for GRPO/TRL and adaptive training.
- **Partner alignment:** Fleet AI (oversight in multi-agent), Mercor/Mercer (long-horizon + rewards), Scaler (enterprise workflows), Halluminate (multi-actor), Snorkel (experts-in-the-loop / human-in-the-loop approval).

---

## References (from Opening Slides & Technical content)

- **OpenEnv Opening Slides:** [PDF (Google Drive)](https://drive.google.com/file/d/1Ip-NnoIAnpTH7Mup5LKhriNhqriglpKr/view)
- **OpenEnv Core:** https://github.com/meta-pytorch/OpenEnv
- **OpenEnv PyTorch Doc:** https://meta-pytorch.org/OpenEnv/
- **OpenEnv HF:** https://huggingface.co/openenv
- **OpenEnv HF Spaces:** https://huggingface.co/openenv/spaces
- **Tutorials:** https://github.com/meta-pytorch/OpenEnv/tree/main/tutorial
- **Training examples:** https://github.com/meta-pytorch/OpenEnv/tree/main/tutorial/examples
- **Envs examples:** https://github.com/meta-pytorch/OpenEnv/tree/main/envs
- **TRL OpenEnv:** https://huggingface.co/docs/trl/en/openenv
- **TRL examples (Sudoku, Wordle, scripts):** https://github.com/huggingface/trl/tree/main/examples/scripts/openenv
- **Unsloth 2048 example:** https://github.com/meta-pytorch/OpenEnv/blob/main/tutorial/examples/unsloth_2048.ipynb
- **Infra (Northflank, GPU request):** https://northflank.notion.site/Deploy-AI-projects-with-Northflank-1a76d14c7851805f8a0ecc780fa33547 · [GPU request form](https://docs.google.com/forms/d/e/1FAIpQLSd2bxx5jAXE8D3FjF7OVekSxwpDVMf1LWE3Z-g4FZoDJ4W6xg/viewform)

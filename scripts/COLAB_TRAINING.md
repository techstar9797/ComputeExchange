# ComputeExchange – Training Script in Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/techstar9797/ComputeExchange/blob/main/scripts/train_colab.ipynb)

> **If Colab says "Could not find..."**: push this repo to GitHub first (`git push origin main`). The badge opens the notebook; run Cell 1 (clone + install) then Cell 2 (training).

Minimal training script (Unsloth or HF TRL) for **judging criteria**: Environment Innovation, Storytelling, **Training Script Showing Improvement in Rewards**, **Reward and Training Pipeline Setup**. The env also runs as an [OpenEnv Space](https://huggingface.co/spaces/mavericks97/ComputeExchange1); see [OpenEnv Spaces](https://huggingface.co/spaces?q=OpenEnv) and the reference [openenv/echo_env](https://huggingface.co/spaces/openenv/echo_env).

## Option A: Run in Colab (recommended)

### 1. Open Colab and clone the repo

```python
# Cell 1: Clone and install
!git clone https://github.com/techstar9797/ComputeExchange.git
%cd ComputeExchange
!pip install -q transformers trl datasets torch accelerate matplotlib
!pip install -q -e ./packages/shared-types
!pip install -q -e ./openenv/compute_market_env
```

### 2. Run the training script

```python
# Cell 2: Run training (episodes + reward curves + TRL)
%run scripts/train_colab.py
```

This will:

- **Run 25 episodes** in the ComputeMarket environment (characterize → negotiate → plan → approve → execute → finalize).
- **Plot reward curves**: per-episode rewards and moving average (shows variance and trend).
- **Export trajectories** to `trajectories/episodes.jsonl` (reward pipeline).
- **Train with TRL**: reward-weighted SFT on (state, action) pairs using `distilgpt2` (small model for Colab).

### 3. Optional: Use Unsloth for efficient fine-tuning

```python
# Cell 3 (optional): Unsloth for 4-bit QLoRA
!pip install -q unsloth
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset

# Load exported trajectories
dataset = load_dataset("json", data_files="trajectories/episodes.jsonl", split="train")
# Build prompts from trajectory state/action; then:
# model, tokenizer = FastLanguageModel.from_pretrained("unsloth/distilgpt2-sft", load_in_4bit=True)
# model = FastLanguageModel.get_peft_model(model, r=8, target_modules=["q_proj","v_proj"])
# ... train on high-reward episodes
```

## Option B: Local run (from repo root)

```bash
cd ComputeExchange
pip install transformers trl datasets torch accelerate matplotlib
pip install -e ./packages/shared-types
pip install -e ./openenv/compute_market_env
python scripts/train_colab.py
```

## Outputs

| Output | Description |
|--------|-------------|
| `compute_exchange_reward_curves.png` | Episode rewards + moving average + distribution |
| `trajectories/episodes.jsonl` | One JSON object per episode (steps, total_reward, strategy) |
| `compute_exchange_trl_out/` | TRL-trained model (e.g. distilgpt2) from reward-weighted data |

## Reward pipeline (judging)

- **Reward logic**: Implemented in `openenv/compute_market_env/server/reward_engine.py` (characterization, negotiation, planning, final).
- **Trajectory export**: Script writes `episodes.jsonl`; API also exposes `GET /trajectory/export` for full history.
- **Improvement**: Reward curve (and optional TRL/Unsloth training) shows the pipeline and that rewards are usable for training.

## Troubleshooting

- **ImportError**: Run from repo root or Colab after `%cd ComputeExchange`.
- **CUDA out of memory**: In the script, reduce `num_episodes` or use `per_device_train_batch_size=1` in TRL.
- **Env errors**: Ensure `openenv/compute_market_env` is installed (`pip install -e ./openenv/compute_market_env`).

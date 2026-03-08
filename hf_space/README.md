---
title: ComputeExchange (OpenEnv)
emoji: 🖥️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# ComputeExchange – OpenEnv Space

**OpenEnv environment** for the compute marketplace. This Space runs the **ComputeMarketEnv** HTTP server so you can connect from TRL, notebooks, or any OpenEnv client. Part of the [OpenEnv Spaces](https://huggingface.co/spaces?q=OpenEnv) ecosystem (reference: [openenv/echo_env](https://huggingface.co/spaces/openenv/echo_env)).

Per the [OpenEnv Hackathon Technical content](https://drive.google.com/file/d/1Ip-NnoIAnpTH7Mup5LKhriNhqriglpKr/view), every HF OpenEnv Space provides **three components**:
1. **Server** — Running environment endpoint (e.g. `curl https://mavericks97-ComputeExchange1.hf.space/health` → `{"status":"healthy"}`).
2. **Repository** — Installable Python package (clone [ComputeExchange](https://github.com/techstar9797/ComputeExchange) and `pip install -e ./openenv/compute_market_env`).
3. **Registry** — Docker image: `registry.hf.space/mavericks97-computeexchange1:latest`.

## Connect

**From Python (use main repo for client, point to this Space):**
```python
# Install: pip install -e ./openenv/compute_market_env from github.com/techstar9797/ComputeExchange
from compute_market_env import ComputeMarketEnv

env = ComputeMarketEnv(base_url="https://mavericks97-ComputeExchange1.hf.space")
# env.reset(), env.step(...), etc.
```

**Run locally via Docker:**
```bash
docker run -p 8000:8000 registry.hf.space/mavericks97-computeexchange1:latest
# then: ComputeMarketEnv(base_url="http://localhost:8000")
```

## Links

- **Repo:** [github.com/techstar9797/ComputeExchange](https://github.com/techstar9797/ComputeExchange)
- **OpenEnv Spaces:** [huggingface.co/spaces?q=OpenEnv](https://huggingface.co/spaces?q=OpenEnv) · [openenv/spaces](https://huggingface.co/openenv/spaces) · [openenv/echo_env](https://huggingface.co/spaces/openenv/echo_env) (reference)
- **OpenEnv (more details):** [Opening Slides (PDF)](https://drive.google.com/file/d/1Ip-NnoIAnpTH7Mup5LKhriNhqriglpKr/view)
- **OpenEnv:** [github.com/meta-pytorch/OpenEnv](https://github.com/meta-pytorch/OpenEnv) · [Tutorials & examples](https://github.com/meta-pytorch/OpenEnv/tree/main/tutorial) · [Environment Hub](https://huggingface.co/collections/openenv)
- **TRL OpenEnv:** [docs](https://huggingface.co/docs/trl/en/openenv) · [examples](https://github.com/huggingface/trl/tree/main/examples/scripts/openenv)
- **Training:** [train_colab.py](https://github.com/techstar9797/ComputeExchange/blob/main/scripts/train_colab.py) · [COLAB_TRAINING.md](https://github.com/techstar9797/ComputeExchange/blob/main/scripts/COLAB_TRAINING.md) · [HACKATHON.md](https://github.com/techstar9797/ComputeExchange/blob/main/HACKATHON.md)

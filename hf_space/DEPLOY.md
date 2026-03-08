# Deploy ComputeExchange as an OpenEnv Space

Hackathon requirement: use **OpenEnv Spaces** so the environment is available on the [Environment Hub](https://huggingface.co/collections/openenv) and connectable via TRL/OpenEnv clients.

## 1. Clone your Space (use a token with write: https://huggingface.co/settings/tokens)

```bash
git clone https://huggingface.co/spaces/mavericks97/ComputeExchange1
cd ComputeExchange1
```

## 2. Copy OpenEnv Space files into the Space repo

From this repo, copy into the Space root:

- `hf_space/Dockerfile`
- `hf_space/README.md`

(Remove any existing `app.py` or Gradio files so the Space uses Docker only.)

## 3. Commit and push

```bash
git add Dockerfile README.md
git commit -m "OpenEnv Space: ComputeMarketEnv server"
git push
```

The Space will build the Docker image (clones ComputeExchange, installs env, runs uvicorn on port 8000). After it’s running, clients can use:

- **Remote:** `ComputeMarketEnv(base_url="https://mavericks97-ComputeExchange1.hf.space")`
- **Install:** `pip install git+https://huggingface.co/spaces/mavericks97/ComputeExchange1`

## References

- [OpenEnv](https://github.com/meta-pytorch/OpenEnv) · [Environment Hub](https://huggingface.co/collections/openenv) · [TRL OpenEnv](https://huggingface.co/docs/trl/openenv) · [Scaling experiments](https://github.com/burtenshaw/openenv-scaling)
- [Hugging Face Docker Spaces](https://huggingface.co/docs/hub/en/spaces-sdks-docker)

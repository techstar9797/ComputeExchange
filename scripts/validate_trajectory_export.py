#!/usr/bin/env python3
"""
Validate trajectory export format for RL training (GRPO/TRL/OpenEnv compatibility).

Run against a running API (default http://localhost:8000):
  python scripts/validate_trajectory_export.py
  python scripts/validate_trajectory_export.py --base-url http://host:8000

Validates:
- GET /trajectory/export (all episodes, jsonl/json)
- GET /trajectory/{session_id}/export (single session RL format)
- Schema: required fields for TorchForge/TRL compatibility
"""

import argparse
import json
import sys
from typing import Any


REQUIRED_BULK_KEYS = {"episode_id", "workload_type", "negotiation_strategy", "total_reward", "sla_met", "metrics"}
REQUIRED_RL_STEP_KEYS = {"step", "phase", "action", "reward", "done"}


def validate_bulk_trajectory(traj: dict) -> list[str]:
    """Validate a single trajectory from /trajectory/export."""
    errors = []
    missing = REQUIRED_BULK_KEYS - set(traj.keys())
    if missing:
        errors.append(f"Missing keys: {missing}")
    if "metrics" in traj:
        m = traj["metrics"]
        for k in ("predicted_cost", "actual_cost", "predicted_duration", "actual_duration", "cost_error", "duration_error"):
            if k not in m:
                errors.append(f"metrics missing key: {k}")
    return errors


def validate_rl_trajectory(response: dict) -> list[str]:
    """Validate single-session RL trajectory from /trajectory/{id}/export."""
    errors = []
    if "trajectory" not in response:
        return ["Missing 'trajectory' key"]
    traj = response["trajectory"]
    if not isinstance(traj, list):
        return ["trajectory must be a list"]
    for i, step in enumerate(traj):
        missing = REQUIRED_RL_STEP_KEYS - set(step.keys())
        if missing:
            errors.append(f"Step {i}: missing keys {missing}")
    return errors


def validate_jsonl(content: str) -> list[str]:
    """Validate jsonl content from bulk export."""
    errors = []
    for i, line in enumerate(content.strip().split("\n")):
        if not line:
            continue
        try:
            obj = json.loads(line)
            errs = validate_bulk_trajectory(obj)
            errors.extend(f"Line {i+1}: {e}" for e in errs)
        except json.JSONDecodeError as e:
            errors.append(f"Line {i+1}: invalid JSON - {e}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate trajectory export for RL training")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--no-http", action="store_true", help="Skip HTTP checks, validate schema only")
    args = parser.parse_args()

    if args.no_http:
        # Schema-only check with mock data
        mock_bulk = {
            "episode_id": "ep-1",
            "workload_type": "llm_training",
            "optimization_weights": {},
            "negotiation_strategy": "balanced",
            "total_reward": 0.85,
            "sla_met": True,
            "metrics": {
                "predicted_cost": 100,
                "actual_cost": 95,
                "predicted_duration": 10,
                "actual_duration": 9.5,
                "cost_error": 0.05,
                "duration_error": 0.05,
            },
        }
        mock_rl = {
            "session_id": "s1",
            "episode_id": "ep-1",
            "trajectory_length": 2,
            "trajectory": [
                {"step": 1, "phase": "characterization", "action": {}, "reward": 0.1, "done": False, "info": {}},
                {"step": 2, "phase": "finalization", "action": {}, "reward": 0.9, "done": True, "info": {}},
            ],
        }
        errs = validate_bulk_trajectory(mock_bulk) + validate_rl_trajectory(mock_rl)
        if errs:
            for e in errs:
                print(f"Schema error: {e}", file=sys.stderr)
            return 1
        print("Schema validation passed (mock data)")
        return 0

    try:
        import urllib.request
        base = args.base_url.rstrip("/")
        # Bulk export
        with urllib.request.urlopen(f"{base}/trajectory/export?format=jsonl") as resp:
            data = json.loads(resp.read().decode())
        if data.get("format") != "jsonl":
            print("Expected format=jsonl", file=sys.stderr)
            return 1
        content = data.get("data", "")
        errs = validate_jsonl(content)
        if errs:
            for e in errs:
                print(e, file=sys.stderr)
            return 1
        print(f"Bulk export OK: {data.get('count', 0)} trajectories")
        # Single-session (use a dummy id; may return empty trajectory)
        with urllib.request.urlopen(f"{base}/trajectory/dummy-session/export") as resp:
            rl_data = json.loads(resp.read().decode())
        errs = validate_rl_trajectory(rl_data)
        if errs:
            for e in errs:
                print(e, file=sys.stderr)
            return 1
        print(f"RL export OK: trajectory_length={rl_data.get('trajectory_length', 0)}")
        print("All trajectory export validations passed.")
        return 0
    except urllib.error.URLError as e:
        print(f"Cannot reach API at {args.base_url}: {e}", file=sys.stderr)
        print("Run with --no-http to validate schema only.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
ComputeMarketEnv FastAPI Server

OpenEnv-compatible server that exposes the ComputeMarket environment
via HTTP/WebSocket endpoints.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .environment import ComputeMarketEnvironment

from .shared_models import ComputeMarketObservation, ComputeMarketState


# Global environment instance
_env: Optional[ComputeMarketEnvironment] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage environment lifecycle."""
    global _env
    _env = ComputeMarketEnvironment()
    yield
    _env = None


app = FastAPI(
    title="ComputeMarket Environment",
    description="OpenEnv environment for compute resource marketplace orchestration",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================


class ResetRequest(BaseModel):
    """Request body for environment reset."""
    seed: Optional[int] = None
    episode_id: Optional[str] = None
    scenario_id: Optional[str] = None


class StepRequest(BaseModel):
    """Request body for environment step."""
    action: dict[str, Any]
    timeout_s: Optional[float] = None


class ResetResponse(BaseModel):
    """Response for environment reset."""
    observation: dict[str, Any]
    reward: float
    done: bool


class StepResponse(BaseModel):
    """Response for environment step."""
    observation: dict[str, Any]
    reward: float
    done: bool


class StateResponse(BaseModel):
    """Response for state query."""
    state: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    version: str


class SchemaResponse(BaseModel):
    """Environment schema response."""
    action: dict[str, Any]
    observation: dict[str, Any]
    state: dict[str, Any]


class ScenarioListResponse(BaseModel):
    """List of available scenarios."""
    scenarios: list[dict[str, Any]]


class TrajectoryResponse(BaseModel):
    """Episode trajectory for training."""
    episode_id: str
    steps: list[dict[str, Any]]


# =============================================================================
# REST Endpoints
# =============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        environment="ComputeMarketEnv",
        version="0.1.0",
    )


@app.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """Get environment action/observation schemas."""
    from .shared_models import ComputeMarketAction, ComputeMarketObservation, ComputeMarketState
    
    return SchemaResponse(
        action=ComputeMarketAction.model_json_schema(),
        observation=ComputeMarketObservation.model_json_schema(),
        state=ComputeMarketState.model_json_schema(),
    )


@app.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios():
    """List available demo scenarios."""
    from .scenario_generator import ScenarioGenerator
    
    gen = ScenarioGenerator()
    return ScenarioListResponse(scenarios=gen.list_scenarios())


@app.post("/reset", response_model=ResetResponse)
async def reset_environment(request: ResetRequest):
    """Reset the environment for a new episode."""
    if _env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    
    obs = _env.reset(
        seed=request.seed,
        episode_id=request.episode_id,
        scenario_id=request.scenario_id,
    )
    
    return ResetResponse(
        observation=obs.model_dump() if hasattr(obs, 'model_dump') else {},
        reward=obs.reward if hasattr(obs, 'reward') else 0.0,
        done=obs.done if hasattr(obs, 'done') else False,
    )


@app.post("/step", response_model=StepResponse)
async def step_environment(request: StepRequest):
    """Execute an action in the environment."""
    if _env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    
    # Create action from dict
    from .shared_models import ComputeMarketAction
    
    class DynamicAction(ComputeMarketAction):
        class Config:
            extra = "allow"
    
    action = DynamicAction(**request.action)
    
    obs = _env.step(action, timeout_s=request.timeout_s)
    
    return StepResponse(
        observation=obs.model_dump() if hasattr(obs, 'model_dump') else {},
        reward=obs.reward if hasattr(obs, 'reward') else 0.0,
        done=obs.done if hasattr(obs, 'done') else False,
    )


@app.get("/state", response_model=StateResponse)
async def get_state():
    """Get current environment state."""
    if _env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    
    state = _env.state
    return StateResponse(
        state=state.model_dump() if hasattr(state, 'model_dump') else {}
    )


@app.get("/trajectory", response_model=TrajectoryResponse)
async def get_trajectory():
    """Get the current episode trajectory for training."""
    if _env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    
    return TrajectoryResponse(
        episode_id=_env.state.episode_id if _env.state else "",
        steps=_env.get_trajectory(),
    )


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time environment interaction.
    
    Message types:
    - reset: Reset environment
    - step: Execute action
    - state: Get current state
    - close: Close connection
    """
    await websocket.accept()
    
    if _env is None:
        await websocket.send_json({"type": "error", "data": {"message": "Environment not initialized"}})
        await websocket.close()
        return
    
    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type", "unknown")
            data = message.get("data", {})
            
            if msg_type == "reset":
                obs = _env.reset(
                    seed=data.get("seed"),
                    episode_id=data.get("episode_id"),
                    scenario_id=data.get("scenario_id"),
                )
                await websocket.send_json({
                    "type": "observation",
                    "data": obs.model_dump() if hasattr(obs, 'model_dump') else {},
                })
            
            elif msg_type == "step":
                from .shared_models import ComputeMarketAction
                
                class DynamicAction(ComputeMarketAction):
                    class Config:
                        extra = "allow"
                
                action = DynamicAction(**data)
                obs = _env.step(action)
                
                await websocket.send_json({
                    "type": "observation",
                    "data": obs.model_dump() if hasattr(obs, 'model_dump') else {},
                })
            
            elif msg_type == "state":
                state = _env.state
                await websocket.send_json({
                    "type": "state",
                    "data": state.model_dump() if hasattr(state, 'model_dump') else {},
                })
            
            elif msg_type == "close":
                await websocket.close()
                break
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"},
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)},
        })


# =============================================================================
# Run Server
# =============================================================================


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

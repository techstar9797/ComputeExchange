"""
ComputeExchange API Server

Main backend API that orchestrates the ComputeMarket environment
and provides endpoints for the frontend dashboard.
"""

import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
from pathlib import Path

# Add shared types to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "shared-types"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "openenv" / "compute_market_env"))

from models import (
    WorkloadSpec,
    WorkloadType,
    OptimizationWeights,
    ProviderProfile,
    ExecutionPlan,
    NegotiationStrategy,
    ApprovalDecision,
    EpisodeResult,
)

from server.environment import ComputeMarketEnvironment
from server.scenario_generator import ScenarioGenerator


# =============================================================================
# State Management
# =============================================================================

class AppState:
    """Application state container."""
    
    def __init__(self):
        self.environments: dict[str, ComputeMarketEnvironment] = {}
        self.scenario_gen = ScenarioGenerator()
        self.episode_history: list[EpisodeResult] = []
        self.active_websockets: list[WebSocket] = []
    
    def get_or_create_env(self, session_id: str) -> ComputeMarketEnvironment:
        """Get or create an environment for a session."""
        if session_id not in self.environments:
            self.environments[session_id] = ComputeMarketEnvironment()
        return self.environments[session_id]
    
    def remove_env(self, session_id: str) -> None:
        """Remove an environment."""
        if session_id in self.environments:
            del self.environments[session_id]


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    yield
    # Cleanup on shutdown
    app_state.environments.clear()


app = FastAPI(
    title="ComputeExchange API",
    description="Backend API for the ComputeExchange multi-agent compute marketplace",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class SessionResponse(BaseModel):
    """Response with session information."""
    session_id: str
    status: str


class WorkloadSubmissionRequest(BaseModel):
    """Request to submit a new workload."""
    name: str
    workload_type: WorkloadType
    model_size_gb: Optional[float] = None
    data_size_gb: Optional[float] = None
    batch_size: Optional[int] = None
    deadline_hours: float
    budget_usd: float
    preferred_regions: list[str] = Field(default_factory=list)
    compliance_requirements: list[str] = Field(default_factory=list)
    cost_weight: float = 0.3
    latency_weight: float = 0.25
    throughput_weight: float = 0.15
    energy_weight: float = 0.1
    reliability_weight: float = 0.2
    allow_spot_instances: bool = True
    allow_heterogeneous_plan: bool = True
    min_reliability_score: float = 0.95


class NegotiationConfig(BaseModel):
    """Configuration for negotiation phase."""
    strategy: NegotiationStrategy = NegotiationStrategy.BALANCED
    max_rounds: int = 5
    target_providers: list[str] = Field(default_factory=list)


class PlanGenerationRequest(BaseModel):
    """Request to generate execution plans."""
    session_id: str
    plan_types: list[str] = Field(default=["balanced", "cheapest", "fastest", "greenest"])


class ApprovalRequest(BaseModel):
    """Request for plan approval/rejection."""
    session_id: str
    plan_id: str
    decision: ApprovalDecision
    feedback: str = ""


class ExecutionRequest(BaseModel):
    """Request to execute a plan."""
    session_id: str
    plan_id: str


class EnvironmentStateResponse(BaseModel):
    """Full environment state response."""
    session_id: str
    phase: str
    step_count: int
    workload: Optional[dict] = None
    decomposition: Optional[dict] = None
    providers: list[dict] = Field(default_factory=list)
    offers: list[dict] = Field(default_factory=list)
    plans: list[dict] = Field(default_factory=list)
    selected_plan: Optional[dict] = None
    execution: Optional[dict] = None
    episode_reward: float = 0.0


class MetricsResponse(BaseModel):
    """Analytics metrics response."""
    total_episodes: int
    avg_reward: float
    avg_cost_savings: float
    avg_time_savings: float
    sla_success_rate: float
    strategy_performance: dict[str, dict]
    provider_stats: dict[str, dict]


# =============================================================================
# REST Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "compute-exchange-api",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session():
    """Create a new session with an environment."""
    session_id = str(uuid4())
    app_state.get_or_create_env(session_id)
    return SessionResponse(session_id=session_id, status="created")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its environment."""
    app_state.remove_env(session_id)
    return {"status": "deleted"}


@app.get("/scenarios")
async def list_scenarios():
    """List available demo scenarios."""
    return {"scenarios": app_state.scenario_gen.list_scenarios()}


@app.post("/session/{session_id}/reset")
async def reset_session(session_id: str, scenario_id: Optional[str] = None, seed: Optional[int] = None):
    """Reset the environment for a new episode."""
    env = app_state.get_or_create_env(session_id)
    obs = env.reset(scenario_id=scenario_id, seed=seed)
    
    return {
        "status": "reset",
        "episode_id": obs.episode_id,
        "phase": env.state.phase,
        "providers": [p.model_dump() for p in env.state.providers],
        "hints": obs.hints,
    }


@app.post("/workload/submit")
async def submit_workload(request: WorkloadSubmissionRequest, background_tasks: BackgroundTasks):
    """Submit a new workload and start orchestration."""
    session_id = str(uuid4())
    env = app_state.get_or_create_env(session_id)
    
    # Reset environment
    env.reset()
    
    # Create workload spec
    workload = WorkloadSpec(
        name=request.name,
        workload_type=request.workload_type,
        model_size_gb=request.model_size_gb,
        data_size_gb=request.data_size_gb,
        batch_size=request.batch_size,
        deadline_hours=request.deadline_hours,
        budget_usd=request.budget_usd,
        preferred_regions=request.preferred_regions,
        compliance_requirements=request.compliance_requirements,
        optimization_weights=OptimizationWeights(
            cost=request.cost_weight,
            latency=request.latency_weight,
            throughput=request.throughput_weight,
            energy=request.energy_weight,
            reliability=request.reliability_weight,
        ).normalize(),
        allow_spot_instances=request.allow_spot_instances,
        allow_heterogeneous_plan=request.allow_heterogeneous_plan,
        min_reliability_score=request.min_reliability_score,
    )
    
    # Execute characterization action
    from models import CharacterizeWorkloadAction
    action = CharacterizeWorkloadAction(workload=workload)
    obs = env.step(action)
    
    return {
        "session_id": session_id,
        "status": "submitted",
        "workload_id": workload.id,
        "phase": env.state.phase,
        "decomposition": env.state.decomposition.model_dump() if env.state.decomposition else None,
        "reward": obs.reward,
        "hints": obs.hints,
    }


@app.post("/session/{session_id}/negotiate")
async def start_negotiation(session_id: str, config: NegotiationConfig):
    """Start negotiation with providers."""
    env = app_state.get_or_create_env(session_id)
    
    if env.state.phase not in ["characterization", "negotiation"]:
        raise HTTPException(status_code=400, detail=f"Cannot negotiate in phase: {env.state.phase}")
    
    # Request quotes
    from models import RequestQuotesAction, SwitchStrategyAction
    
    # Set strategy if different
    if env.state.negotiation is None or env.state.negotiation.strategy != config.strategy:
        switch_action = SwitchStrategyAction(new_strategy=config.strategy)
        env.step(switch_action)
    
    # Request quotes
    action = RequestQuotesAction(
        decomposition=env.state.decomposition,
        target_providers=config.target_providers,
    )
    obs = env.step(action)
    
    return {
        "status": "negotiating",
        "phase": env.state.phase,
        "strategy": config.strategy.value,
        "round": env.state.negotiation.current_round if env.state.negotiation else 0,
        "offers": [o.model_dump() for o in obs.current_offers],
        "reward": obs.reward,
        "hints": obs.hints,
    }


@app.post("/session/{session_id}/counter-offer")
async def send_counter_offer(session_id: str, offer_id: str, counter_price: float):
    """Send a counter-offer to a provider."""
    env = app_state.get_or_create_env(session_id)
    
    from models import CounterOfferAction
    action = CounterOfferAction(offer_id=offer_id, counter_price_usd=counter_price)
    obs = env.step(action)
    
    return {
        "status": "counter_sent",
        "offers": [o.model_dump() for o in obs.current_offers],
        "reward": obs.reward,
    }


@app.post("/plans/generate", response_model=dict)
async def generate_plans(request: PlanGenerationRequest):
    """Generate execution plans from current offers."""
    env = app_state.get_or_create_env(request.session_id)
    
    from models import GeneratePlanAction
    
    # Generate plans for each type
    for plan_type in request.plan_types:
        action = GeneratePlanAction(plan_type=plan_type)
        obs = env.step(action)
    
    return {
        "status": "plans_generated",
        "phase": env.state.phase,
        "plans": [p.model_dump() for p in env.state.plans],
        "reward": obs.reward,
        "hints": obs.hints,
    }


@app.post("/plans/submit-approval")
async def submit_plan_for_approval(session_id: str, plan_id: str, summary: str = ""):
    """Submit a plan for human approval."""
    env = app_state.get_or_create_env(session_id)
    
    from models import SubmitForApprovalAction
    action = SubmitForApprovalAction(plan_id=plan_id, summary=summary)
    obs = env.step(action)
    
    # Find the plan
    plan = next((p for p in env.state.plans if p.id == plan_id), None)
    
    return {
        "status": "pending_approval",
        "phase": env.state.phase,
        "plan": plan.model_dump() if plan else None,
        "hints": obs.hints,
    }


@app.post("/plans/approve")
async def approve_plan(request: ApprovalRequest):
    """Approve or reject a plan."""
    env = app_state.get_or_create_env(request.session_id)
    
    if request.decision == ApprovalDecision.APPROVE:
        from models import ApprovePlanAction
        action = ApprovePlanAction(plan_id=request.plan_id)
    else:
        from models import RejectPlanAction
        action = RejectPlanAction(plan_id=request.plan_id, reason=request.feedback, feedback=request.feedback)
    
    obs = env.step(action)
    
    return {
        "status": request.decision.value,
        "phase": env.state.phase,
        "reward": obs.reward,
        "hints": obs.hints,
    }


@app.post("/execution/start")
async def start_execution(request: ExecutionRequest):
    """Start executing an approved plan."""
    env = app_state.get_or_create_env(request.session_id)
    
    from models import ExecutePlanAction
    action = ExecutePlanAction(plan_id=request.plan_id)
    obs = env.step(action)
    
    return {
        "status": "executing",
        "phase": env.state.phase,
        "execution": env.state.execution.model_dump() if env.state.execution else None,
        "reward": obs.reward,
        "hints": obs.hints,
    }


@app.post("/session/{session_id}/finalize")
async def finalize_episode(session_id: str):
    """Finalize the episode and get final results."""
    env = app_state.get_or_create_env(session_id)
    
    from models import FinalizeEpisodeAction
    action = FinalizeEpisodeAction()
    obs = env.step(action)
    
    # Create episode result for history
    result = EpisodeResult(
        episode_id=env.state.episode_id,
        workload_id=env.state.workload.id if env.state.workload else "",
        plan_id=env.state.selected_plan_id or "",
        workload_type=env.state.workload.workload_type if env.state.workload else WorkloadType.ETL_ANALYTICS,
        optimization_objective=env.state.workload.optimization_weights if env.state.workload else OptimizationWeights(),
        negotiation_strategy=env.state.negotiation.strategy if env.state.negotiation else NegotiationStrategy.BALANCED,
        negotiation_rounds=env.state.negotiation.current_round if env.state.negotiation else 0,
        predicted_cost=env.state.execution.predicted_cost_usd if env.state.execution else 0,
        actual_cost=env.state.execution.actual_total_cost_usd if env.state.execution else 0,
        predicted_duration=env.state.execution.predicted_duration_hours if env.state.execution else 0,
        actual_duration=env.state.execution.actual_total_duration_hours if env.state.execution else 0,
        sla_met=obs.reward > 0,
        within_budget=True,
        total_reward=obs.reward,
        provider_ids=[a.provider_id for a in (next((p for p in env.state.plans if p.id == env.state.selected_plan_id), None) or ExecutionPlan(workload_id="", allocations=[], total_cost_usd=0, total_duration_hours=0, plan_type="")).allocations],
        human_approved=env.state.approval_decision == ApprovalDecision.APPROVE,
    )
    app_state.episode_history.append(result)
    
    return {
        "status": "completed",
        "done": obs.done,
        "total_reward": obs.reward,
        "reward_breakdown": obs.reward_breakdown,
        "execution": env.state.execution.model_dump() if env.state.execution else None,
        "trajectory": env.get_trajectory(),
    }


@app.get("/session/{session_id}/state", response_model=EnvironmentStateResponse)
async def get_session_state(session_id: str):
    """Get the full state of a session."""
    env = app_state.get_or_create_env(session_id)
    state = env.state
    
    return EnvironmentStateResponse(
        session_id=session_id,
        phase=state.phase,
        step_count=state.step_count,
        workload=state.workload.model_dump() if state.workload else None,
        decomposition=state.decomposition.model_dump() if state.decomposition else None,
        providers=[p.model_dump() for p in state.providers],
        offers=[o.model_dump() for o in (state.negotiation.offers if state.negotiation else [])],
        plans=[p.model_dump() for p in state.plans],
        selected_plan=next((p.model_dump() for p in state.plans if p.id == state.selected_plan_id), None),
        execution=state.execution.model_dump() if state.execution else None,
        episode_reward=state.episode_reward,
    )


@app.get("/session/{session_id}/trajectory")
async def get_trajectory(session_id: str):
    """Get the episode trajectory for training."""
    env = app_state.get_or_create_env(session_id)
    return {"trajectory": env.get_trajectory()}


@app.get("/analytics/metrics", response_model=MetricsResponse)
async def get_analytics_metrics():
    """Get aggregate analytics metrics."""
    history = app_state.episode_history
    
    if not history:
        return MetricsResponse(
            total_episodes=0,
            avg_reward=0.0,
            avg_cost_savings=0.0,
            avg_time_savings=0.0,
            sla_success_rate=0.0,
            strategy_performance={},
            provider_stats={},
        )
    
    total = len(history)
    avg_reward = sum(e.total_reward for e in history) / total
    
    # Calculate savings
    cost_savings = []
    time_savings = []
    for e in history:
        if e.predicted_cost > 0:
            cost_savings.append((e.predicted_cost - e.actual_cost) / e.predicted_cost)
        if e.predicted_duration > 0:
            time_savings.append((e.predicted_duration - e.actual_duration) / e.predicted_duration)
    
    avg_cost_savings = sum(cost_savings) / len(cost_savings) if cost_savings else 0
    avg_time_savings = sum(time_savings) / len(time_savings) if time_savings else 0
    
    sla_success = sum(1 for e in history if e.sla_met) / total
    
    # Strategy performance
    strategy_perf: dict[str, dict] = {}
    for e in history:
        strat = e.negotiation_strategy.value
        if strat not in strategy_perf:
            strategy_perf[strat] = {"count": 0, "total_reward": 0, "sla_met": 0}
        strategy_perf[strat]["count"] += 1
        strategy_perf[strat]["total_reward"] += e.total_reward
        if e.sla_met:
            strategy_perf[strat]["sla_met"] += 1
    
    for strat in strategy_perf:
        count = strategy_perf[strat]["count"]
        strategy_perf[strat]["avg_reward"] = strategy_perf[strat]["total_reward"] / count
        strategy_perf[strat]["sla_rate"] = strategy_perf[strat]["sla_met"] / count
    
    return MetricsResponse(
        total_episodes=total,
        avg_reward=avg_reward,
        avg_cost_savings=avg_cost_savings,
        avg_time_savings=avg_time_savings,
        sla_success_rate=sla_success,
        strategy_performance=strategy_perf,
        provider_stats={},
    )


@app.get("/analytics/history")
async def get_episode_history(limit: int = 50):
    """Get recent episode history."""
    history = app_state.episode_history[-limit:]
    return {"episodes": [e.model_dump() for e in history]}


# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time environment updates."""
    await websocket.accept()
    app_state.active_websockets.append(websocket)
    
    env = app_state.get_or_create_env(session_id)
    
    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type", "unknown")
            data = message.get("data", {})
            
            response = {"type": "error", "data": {"message": f"Unknown type: {msg_type}"}}
            
            if msg_type == "reset":
                obs = env.reset(
                    scenario_id=data.get("scenario_id"),
                    seed=data.get("seed"),
                )
                response = {
                    "type": "reset",
                    "data": {
                        "episode_id": obs.episode_id,
                        "phase": env.state.phase,
                        "providers": [p.model_dump() for p in env.state.providers],
                    },
                }
            
            elif msg_type == "step":
                from models import ComputeMarketAction
                
                class DynamicAction(ComputeMarketAction):
                    class Config:
                        extra = "allow"
                
                action = DynamicAction(**data.get("action", {}))
                obs = env.step(action)
                
                response = {
                    "type": "observation",
                    "data": {
                        "phase": env.state.phase,
                        "step_count": env.state.step_count,
                        "reward": obs.reward,
                        "done": obs.done,
                        "hints": obs.hints,
                        "observation": obs.model_dump(),
                    },
                }
            
            elif msg_type == "state":
                response = {
                    "type": "state",
                    "data": env.state.model_dump(),
                }
            
            await websocket.send_json(response)
    
    except WebSocketDisconnect:
        app_state.active_websockets.remove(websocket)
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
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)

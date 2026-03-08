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
import importlib.util

# Load shared models using importlib to avoid naming collisions
_models_path = Path(__file__).parent.parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_types_models", _models_path)
_shared_models = importlib.util.module_from_spec(_spec)
_shared_models.__dict__['Optional'] = Optional
_shared_models.__dict__['Any'] = Any
_shared_models.__dict__['datetime'] = datetime
from uuid import uuid4 as _uuid4
_shared_models.__dict__['uuid4'] = _uuid4
_spec.loader.exec_module(_shared_models)

# Rebuild models to resolve forward references
for _name in dir(_shared_models):
    _obj = getattr(_shared_models, _name)
    if hasattr(_obj, 'model_rebuild'):
        try:
            _obj.model_rebuild()
        except Exception:
            pass

# Import models from the loaded module
WorkloadSpec = _shared_models.WorkloadSpec
WorkloadType = _shared_models.WorkloadType
OptimizationWeights = _shared_models.OptimizationWeights
ProviderProfile = _shared_models.ProviderProfile
ExecutionPlan = _shared_models.ExecutionPlan
NegotiationStrategy = _shared_models.NegotiationStrategy
ApprovalDecision = _shared_models.ApprovalDecision
EpisodeResult = _shared_models.EpisodeResult
CharacterizeWorkloadAction = _shared_models.CharacterizeWorkloadAction
RequestQuotesAction = _shared_models.RequestQuotesAction
GeneratePlanAction = _shared_models.GeneratePlanAction
SubmitForApprovalAction = _shared_models.SubmitForApprovalAction
ApprovePlanAction = _shared_models.ApprovePlanAction
ExecutePlanAction = _shared_models.ExecutePlanAction
FinalizeEpisodeAction = _shared_models.FinalizeEpisodeAction
SwitchStrategyAction = _shared_models.SwitchStrategyAction
CounterOfferAction = _shared_models.CounterOfferAction
WorkloadDecomposition = _shared_models.WorkloadDecomposition
TaskStage = _shared_models.TaskStage
TaskStageType = _shared_models.TaskStageType
ResourceType = _shared_models.ResourceType

# Add openenv path for importing server modules
_openenv_server_path = str(Path(__file__).parent.parent.parent / "openenv" / "compute_market_env")
if _openenv_server_path not in sys.path:
    sys.path.insert(0, _openenv_server_path)

from server.environment import ComputeMarketEnvironment
from server.scenario_generator import ScenarioGenerator

# Add agents path
_agents_path = str(Path(__file__).parent.parent.parent / "agents")
if _agents_path not in sys.path:
    sys.path.insert(0, _agents_path)

from workload_characterizer import WorkloadCharacterizer
from planner import PlanningAgent
from negotiator import NegotiationAgent
from learning_agent import LearningAgent


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
        self.session_websockets: dict[str, list[WebSocket]] = {}
        
        self.characterizer = WorkloadCharacterizer()
        self.planner = PlanningAgent()
        self.learning_agent = LearningAgent()
        self.negotiators: dict[str, NegotiationAgent] = {}
        
        self.characterization_cache: dict[str, dict] = {}
        self.plan_cache: dict[str, list] = {}
    
    def get_or_create_env(self, session_id: str) -> ComputeMarketEnvironment:
        """Get or create an environment for a session."""
        if session_id not in self.environments:
            self.environments[session_id] = ComputeMarketEnvironment()
        return self.environments[session_id]
    
    def get_or_create_negotiator(self, session_id: str, strategy: NegotiationStrategy = NegotiationStrategy.BALANCED) -> NegotiationAgent:
        """Get or create a negotiation agent for a session."""
        if session_id not in self.negotiators:
            self.negotiators[session_id] = NegotiationAgent(strategy=strategy)
        return self.negotiators[session_id]
    
    def remove_env(self, session_id: str) -> None:
        """Remove an environment and associated state."""
        if session_id in self.environments:
            del self.environments[session_id]
        if session_id in self.negotiators:
            del self.negotiators[session_id]
        if session_id in self.characterization_cache:
            del self.characterization_cache[session_id]
        if session_id in self.plan_cache:
            del self.plan_cache[session_id]
        if session_id in self.session_websockets:
            del self.session_websockets[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict) -> None:
        """Push a message to all WebSocket clients subscribed to this session."""
        sockets = self.session_websockets.get(session_id, [])
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if session_id in self.session_websockets:
                self.session_websockets[session_id] = [
                    s for s in self.session_websockets[session_id] if s != ws
                ]


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
    
    # Use agent for detailed characterization
    char_result = app_state.characterizer.characterize(workload)
    app_state.characterization_cache[session_id] = {
        "workload": workload,
        "result": char_result,
    }
    
    # Also execute characterization in environment
    action = CharacterizeWorkloadAction(workload=workload)
    obs = env.step(action)
    
    return {
        "session_id": session_id,
        "status": "submitted",
        "workload_id": workload.id,
        "phase": env.state.phase,
        "decomposition": char_result.decomposition.model_dump(),
        "characterization": {
            "confidence": char_result.confidence,
            "analysis_notes": char_result.analysis_notes,
            "suggested_providers": char_result.suggested_providers,
            "total_stages": len(char_result.decomposition.stages),
            "total_estimated_hours": char_result.decomposition.total_estimated_hours,
            "total_estimated_cost_usd": char_result.decomposition.total_estimated_cost_usd,
        },
        "stages": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.stage_type.value,
                "resources": [r.value for r in s.required_resource_types],
                "duration_hours": s.estimated_duration_hours,
                "memory_gb": s.estimated_memory_gb,
                "parallelizable": s.parallelizable,
            }
            for s in char_result.decomposition.stages
        ],
        "reward": obs.reward,
        "hints": obs.hints,
    }

    await app_state.broadcast_to_session(session_id, {
        "type": "state",
        "data": env.state.model_dump(),
    })


@app.post("/session/{session_id}/negotiate")
async def start_negotiation(session_id: str, config: NegotiationConfig):
    """Start negotiation with providers."""
    env = app_state.get_or_create_env(session_id)
    
    if env.state.phase not in ["characterization", "negotiation"]:
        raise HTTPException(status_code=400, detail=f"Cannot negotiate in phase: {env.state.phase}")
    
    # Set strategy if different
    if env.state.negotiation is None or env.state.negotiation.strategy != config.strategy:
        switch_action = SwitchStrategyAction(new_strategy=config.strategy)
        env.step(switch_action)
    
    # Convert decomposition to ensure consistent Pydantic model type
    decomp_dict = env.state.decomposition.model_dump() if hasattr(env.state.decomposition, 'model_dump') else env.state.decomposition
    decomp = WorkloadDecomposition(**decomp_dict)
    
    # Request quotes
    action = RequestQuotesAction(
        decomposition=decomp,
        target_providers=config.target_providers,
    )
    obs = env.step(action)
    
    result = {
        "status": "negotiating",
        "phase": env.state.phase,
        "strategy": config.strategy.value,
        "round": env.state.negotiation.current_round if env.state.negotiation else 0,
        "offers": [o.model_dump() for o in obs.current_offers],
        "reward": obs.reward,
        "hints": obs.hints,
    }
    await app_state.broadcast_to_session(session_id, {
        "type": "state",
        "data": env.state.model_dump(),
    })
    return result


@app.post("/session/{session_id}/counter-offer")
async def send_counter_offer(session_id: str, offer_id: str, counter_price: float):
    """Send a counter-offer to a provider."""
    env = app_state.get_or_create_env(session_id)
    
    action = CounterOfferAction(offer_id=offer_id, counter_price_usd=counter_price)
    obs = env.step(action)
    
    return {
        "status": "counter_sent",
        "offers": [o.model_dump() for o in obs.current_offers],
        "reward": obs.reward,
    }


@app.post("/plans/generate", response_model=dict)
async def generate_plans(request: PlanGenerationRequest):
    """Generate execution plans from current offers using planning agent."""
    env = app_state.get_or_create_env(request.session_id)
    
    # Get characterization data
    char_data = app_state.characterization_cache.get(request.session_id)
    if not char_data:
        raise HTTPException(status_code=400, detail="No workload characterized for this session")
    
    workload = char_data["workload"]
    decomposition = char_data["result"].decomposition
    
    # Get offers from environment negotiation state
    offers = []
    if env.state.negotiation and hasattr(env.state.negotiation, 'offers'):
        offers = env.state.negotiation.offers
    
    providers = env.state.providers if hasattr(env.state, 'providers') else []
    
    # Use planning agent to generate plans
    plan_candidates = app_state.planner.generate_plans(
        workload=workload,
        decomposition=decomposition,
        offers=offers,
        providers=providers,
    )
    
    # Cache plans
    app_state.plan_cache[request.session_id] = plan_candidates

    # Store plans directly in environment state instead of using GeneratePlanAction
    # This ensures the plan IDs match between API and environment
    # Convert to dicts and back to ensure type compatibility with environment's model classes
    from server.shared_models import ExecutionPlan as EnvExecutionPlan
    env.state.plans = [EnvExecutionPlan(**pc.plan.model_dump()) for pc in plan_candidates]
    env.state.phase = "planning"
    
    # Compute planning reward
    reward = 0.15  # Base reward for generating plans
    
    # Generate comparison data
    comparison = app_state.planner.compare_plans(plan_candidates, workload)

    await app_state.broadcast_to_session(request.session_id, {
        "type": "state",
        "data": env.state.model_dump(),
    })
    
    return {
        "status": "plans_generated",
        "phase": env.state.phase,
        "plans": [
            {
                "id": pc.plan.id,
                "name": f"{pc.plan.plan_type.title()} Plan",
                "strategy": pc.strategy,
                "score": pc.score,
                "cost": pc.plan.total_cost_usd,
                "duration": pc.plan.total_duration_hours,
                "reliability": pc.plan.reliability_score,
                "carbon_kg": pc.plan.carbon_footprint_kg,
                "pros": pc.pros,
                "cons": pc.cons,
                "risks": pc.risk_factors,
                "allocations": [a.model_dump() for a in pc.plan.allocations],
            }
            for pc in plan_candidates
        ],
        "comparison": comparison,
        "recommendation": comparison.get("recommendation") if comparison else None,
        "reward": reward,
        "hints": ["Submit a plan for approval using submit_for_approval"],
    }


@app.post("/plans/submit-approval")
async def submit_plan_for_approval(session_id: str, plan_id: str, summary: str = ""):
    """Submit a plan for human approval."""
    env = app_state.get_or_create_env(session_id)
    
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
        action = ApprovePlanAction(plan_id=request.plan_id, feedback=request.feedback)
    else:
        RejectPlanAction = _shared_models.RejectPlanAction
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
    
    action = FinalizeEpisodeAction()
    obs = env.step(action)
    
    # Create episode result for history
    # Convert optimization_weights to dict and back to ensure type compatibility
    opt_weights_data = (
        env.state.workload.optimization_weights.model_dump() 
        if env.state.workload and hasattr(env.state.workload.optimization_weights, 'model_dump')
        else {}
    )
    
    selected_plan = next((p for p in env.state.plans if p.id == env.state.selected_plan_id), None)
    provider_ids = [a.provider_id for a in selected_plan.allocations] if selected_plan else []
    
    result = EpisodeResult(
        episode_id=env.state.episode_id,
        workload_id=env.state.workload.id if env.state.workload else "",
        plan_id=env.state.selected_plan_id or "",
        workload_type=env.state.workload.workload_type if env.state.workload else WorkloadType.ETL_ANALYTICS,
        optimization_objective=OptimizationWeights(**opt_weights_data) if opt_weights_data else OptimizationWeights(),
        negotiation_strategy=env.state.negotiation.strategy if env.state.negotiation else NegotiationStrategy.BALANCED,
        negotiation_rounds=env.state.negotiation.current_round if env.state.negotiation else 0,
        predicted_cost=env.state.execution.predicted_cost_usd if env.state.execution else 0,
        actual_cost=env.state.execution.actual_total_cost_usd if env.state.execution else 0,
        predicted_duration=env.state.execution.predicted_duration_hours if env.state.execution else 0,
        actual_duration=env.state.execution.actual_total_duration_hours if env.state.execution else 0,
        sla_met=obs.reward > 0,
        within_budget=True,
        total_reward=obs.reward,
        provider_ids=provider_ids,
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


@app.get("/learning/recommend")
async def get_strategy_recommendation(workload_type: Optional[str] = None):
    """Get recommended negotiation strategy based on episode history."""
    wt = None
    if workload_type:
        try:
            wt = WorkloadType(workload_type)
        except ValueError:
            wt = WorkloadType.LLM_TRAINING
    rec = app_state.learning_agent.recommend_strategy(wt, app_state.episode_history)
    return {
        "strategy": rec.strategy.value,
        "confidence": rec.confidence,
        "reasoning": rec.reasoning,
        "alternative": rec.alternative.value if rec.alternative else None,
    }


@app.get("/learning/insights")
async def get_learning_insights(workload_type: Optional[str] = None):
    """Get learning insights including strategy recommendation and tips."""
    wt = None
    if workload_type:
        try:
            wt = WorkloadType(workload_type)
        except ValueError:
            wt = WorkloadType.LLM_TRAINING
    insights = app_state.learning_agent.get_insights(wt, app_state.episode_history)
    return {
        "recommended_strategy": insights.recommended_strategy.strategy.value,
        "confidence": insights.recommended_strategy.confidence,
        "reasoning": insights.recommended_strategy.reasoning,
        "alternative": insights.recommended_strategy.alternative.value if insights.recommended_strategy.alternative else None,
        "avg_reward_trend": insights.avg_reward_trend,
        "best_workload_type": insights.best_workload_type,
        "tips": insights.tips,
    }


@app.get("/trajectory/export")
async def export_all_trajectories(format: str = "jsonl"):
    """
    Export all episode trajectories for RL training.
    
    Compatible with:
    - TorchForge GRPO training
    - HuggingFace TRL
    - OpenEnv training loops
    """
    trajectories = []
    
    for result in app_state.episode_history:
        # Get env if it still exists, otherwise create placeholder trajectory
        traj_data = {
            "episode_id": result.episode_id,
            "workload_type": result.workload_type.value if hasattr(result.workload_type, 'value') else str(result.workload_type),
            "optimization_weights": result.optimization_objective.model_dump() if hasattr(result.optimization_objective, 'model_dump') else {},
            "negotiation_strategy": result.negotiation_strategy.value if hasattr(result.negotiation_strategy, 'value') else str(result.negotiation_strategy),
            "total_reward": result.total_reward,
            "sla_met": result.sla_met,
            "metrics": {
                "predicted_cost": result.predicted_cost,
                "actual_cost": result.actual_cost,
                "predicted_duration": result.predicted_duration,
                "actual_duration": result.actual_duration,
                "cost_error": abs(result.actual_cost - result.predicted_cost) / max(result.predicted_cost, 0.01),
                "duration_error": abs(result.actual_duration - result.predicted_duration) / max(result.predicted_duration, 0.01),
            },
        }
        trajectories.append(traj_data)
    
    if format == "jsonl":
        import json
        content = "\n".join(json.dumps(t) for t in trajectories)
        return {"format": "jsonl", "count": len(trajectories), "data": content}
    
    return {"format": "json", "count": len(trajectories), "trajectories": trajectories}


@app.get("/trajectory/{session_id}/export")
async def export_session_trajectory(session_id: str):
    """Export a single session's trajectory in RL-compatible format."""
    env = app_state.get_or_create_env(session_id)
    trajectory = env.get_trajectory()
    
    # Convert to standard RL format: (state, action, reward, next_state, done)
    rl_trajectory = []
    for i, step in enumerate(trajectory):
        rl_step = {
            "step": step.get("step", i),
            "phase": step.get("phase"),
            "action": step.get("action"),
            "reward": step.get("reward", step.get("final_reward", 0)),
            "done": step.get("phase") == "finalization",
            "info": {
                "timestamp": step.get("timestamp"),
            }
        }
        rl_trajectory.append(rl_step)
    
    return {
        "session_id": session_id,
        "episode_id": env.state.episode_id if env.state else None,
        "trajectory_length": len(rl_trajectory),
        "trajectory": rl_trajectory,
    }


# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time environment updates."""
    await websocket.accept()
    app_state.active_websockets.append(websocket)
    if session_id not in app_state.session_websockets:
        app_state.session_websockets[session_id] = []
    app_state.session_websockets[session_id].append(websocket)

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
                ComputeMarketAction = _shared_models.ComputeMarketAction
                
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
        if session_id in app_state.session_websockets:
            app_state.session_websockets[session_id] = [
                s for s in app_state.session_websockets[session_id] if s != websocket
            ]
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

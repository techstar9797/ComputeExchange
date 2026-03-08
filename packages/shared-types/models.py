"""
ComputeExchange Shared Data Models

These Pydantic models define the data contracts between all components:
- Frontend ↔ API
- API ↔ OpenEnv Environment
- Agents ↔ Environment
- Training ↔ Trajectory storage
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class WorkloadType(str, Enum):
    """Types of compute workloads."""
    LLM_TRAINING = "llm_training"
    BATCH_INFERENCE = "batch_inference"
    REALTIME_INFERENCE = "realtime_inference"
    ETL_ANALYTICS = "etl_analytics"
    RENDERING_SIMULATION = "rendering_simulation"
    MULTIMODAL_PIPELINE = "multimodal_pipeline"


class OptimizationObjective(str, Enum):
    """Optimization objectives for workload planning."""
    COST = "cost"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ENERGY = "energy"
    RELIABILITY = "reliability"
    BALANCED = "balanced"


class ResourceType(str, Enum):
    """Types of compute resources."""
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"
    TPU = "tpu"
    FPGA = "fpga"
    MEMORY = "memory"


class ProviderType(str, Enum):
    """Types of compute providers."""
    NEOCLOUD_GPU = "neocloud_gpu"
    DATACENTER_CPU = "datacenter_cpu"
    HYPERSCALER = "hyperscaler"
    EDGE_NPU = "edge_npu"
    GREEN_DATACENTER = "green_datacenter"


class NegotiationStrategy(str, Enum):
    """Strategies for price negotiation."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    GREEDY = "greedy"
    COOPERATIVE = "cooperative"
    BLUFFING = "bluffing"
    BALANCED = "balanced"


class PlanStatus(str, Enum):
    """Status of an execution plan."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalDecision(str, Enum):
    """Human approval decisions."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REPLAN = "request_replan"


class TaskStageType(str, Enum):
    """Types of task stages in a workload."""
    PREPROCESSING = "preprocessing"
    DATA_LOADING = "data_loading"
    COMPUTE_INTENSIVE = "compute_intensive"
    MEMORY_INTENSIVE = "memory_intensive"
    IO_HEAVY = "io_heavy"
    POSTPROCESSING = "postprocessing"
    COMMUNICATION = "communication"


# =============================================================================
# Core Models
# =============================================================================


class WorkloadSpec(BaseModel):
    """Specification of a compute workload submitted by an enterprise."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    workload_type: WorkloadType
    
    model_size_gb: Optional[float] = Field(None, description="Size of model in GB")
    data_size_gb: Optional[float] = Field(None, description="Size of data in GB")
    batch_size: Optional[int] = None
    
    deadline_hours: float = Field(..., gt=0, description="Deadline in hours")
    budget_usd: float = Field(..., gt=0, description="Maximum budget in USD")
    
    preferred_regions: list[str] = Field(default_factory=list)
    compliance_requirements: list[str] = Field(default_factory=list)
    
    optimization_weights: OptimizationWeights
    
    allow_spot_instances: bool = True
    allow_heterogeneous_plan: bool = True
    min_reliability_score: float = Field(0.95, ge=0.0, le=1.0)
    
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationWeights(BaseModel):
    """Weights for multi-objective optimization."""
    cost: float = Field(0.3, ge=0.0, le=1.0)
    latency: float = Field(0.25, ge=0.0, le=1.0)
    throughput: float = Field(0.15, ge=0.0, le=1.0)
    energy: float = Field(0.1, ge=0.0, le=1.0)
    reliability: float = Field(0.2, ge=0.0, le=1.0)
    
    def normalize(self) -> OptimizationWeights:
        """Normalize weights to sum to 1."""
        total = self.cost + self.latency + self.throughput + self.energy + self.reliability
        if total == 0:
            return OptimizationWeights()
        return OptimizationWeights(
            cost=self.cost / total,
            latency=self.latency / total,
            throughput=self.throughput / total,
            energy=self.energy / total,
            reliability=self.reliability / total,
        )


class TaskStage(BaseModel):
    """A decomposed stage of a workload."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    stage_type: TaskStageType
    
    required_resource_types: list[ResourceType]
    preferred_resource_types: list[ResourceType] = Field(default_factory=list)
    
    estimated_flops: float = Field(0, ge=0)
    estimated_memory_gb: float = Field(0, ge=0)
    estimated_io_gb: float = Field(0, ge=0)
    estimated_duration_hours: float = Field(0, ge=0)
    
    parallelizable: bool = False
    dependencies: list[str] = Field(default_factory=list, description="IDs of dependent stages")
    
    latency_sensitive: bool = False
    can_use_spot: bool = True


class WorkloadDecomposition(BaseModel):
    """Decomposed workload into executable stages."""
    workload_id: str
    stages: list[TaskStage]
    total_estimated_hours: float
    total_estimated_cost_usd: float
    critical_path_hours: float
    parallelism_factor: float = Field(1.0, ge=1.0)


# =============================================================================
# Provider Models
# =============================================================================


class ProviderCapacity(BaseModel):
    """Current capacity of a provider."""
    gpu_count: int = 0
    gpu_memory_gb: float = 0
    cpu_cores: int = 0
    memory_gb: float = 0
    storage_tb: float = 0
    npu_count: int = 0
    
    utilization_percent: float = Field(0, ge=0, le=100)
    available_until: Optional[datetime] = None


class PricingPolicy(BaseModel):
    """Pricing policy for a provider."""
    base_gpu_hour_usd: float
    base_cpu_hour_usd: float
    base_npu_hour_usd: float = 0
    
    spot_discount_percent: float = Field(0, ge=0, le=90)
    reserved_discount_percent: float = Field(0, ge=0, le=50)
    volume_discount_thresholds: list[tuple[float, float]] = Field(
        default_factory=list,
        description="List of (hours_threshold, discount_percent)"
    )
    
    min_commitment_hours: float = 0
    surge_multiplier: float = Field(1.0, ge=1.0, le=5.0)


class ProviderProfile(BaseModel):
    """Profile of a compute provider."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider_type: ProviderType
    
    capacity: ProviderCapacity
    pricing: PricingPolicy
    
    reliability_score: float = Field(0.99, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(50, ge=0)
    
    regions: list[str]
    compliance_certifications: list[str] = Field(default_factory=list)
    
    carbon_intensity_gco2_kwh: float = Field(400, ge=0)
    renewable_energy_percent: float = Field(0, ge=0, le=100)
    
    negotiation_flexibility: float = Field(0.1, ge=0.0, le=1.0)
    negotiation_style: NegotiationStrategy = NegotiationStrategy.BALANCED
    
    sla_uptime_guarantee: float = Field(0.99, ge=0.0, le=1.0)
    max_job_duration_hours: float = Field(720, gt=0)
    
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderOffer(BaseModel):
    """An offer from a provider for a workload."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider_id: str
    provider_name: str
    
    workload_id: str
    stage_ids: list[str] = Field(default_factory=list)
    
    quoted_price_usd: float
    quoted_duration_hours: float
    
    resource_allocation: dict[ResourceType, int]
    
    is_spot: bool = False
    valid_until: datetime
    
    reliability_estimate: float = Field(0.99, ge=0.0, le=1.0)
    carbon_footprint_kg: float = Field(0, ge=0)
    
    terms: dict[str, Any] = Field(default_factory=dict)
    negotiation_round: int = 1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Negotiation Models
# =============================================================================


class NegotiationMessage(BaseModel):
    """A message in a negotiation exchange."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    negotiation_id: str
    round: int
    
    sender: str  # "agent" or provider_id
    recipient: str
    
    message_type: str  # "request_quote", "offer", "counter_offer", "accept", "reject"
    content: dict[str, Any]
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NegotiationState(BaseModel):
    """State of an ongoing negotiation."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    workload_id: str
    
    strategy: NegotiationStrategy
    current_round: int = 0
    max_rounds: int = 5
    
    active_providers: list[str]
    offers: list[ProviderOffer] = Field(default_factory=list)
    messages: list[NegotiationMessage] = Field(default_factory=list)
    
    best_offer_id: Optional[str] = None
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# =============================================================================
# Plan Models
# =============================================================================


class ResourceAllocation(BaseModel):
    """Allocation of a stage to a provider's resources."""
    stage_id: str
    provider_id: str
    provider_name: str
    
    resource_type: ResourceType
    resource_count: int
    
    estimated_cost_usd: float
    estimated_duration_hours: float
    
    start_offset_hours: float = 0
    is_spot: bool = False


class ExecutionPlan(BaseModel):
    """A complete execution plan for a workload."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    workload_id: str
    version: int = 1
    
    status: PlanStatus = PlanStatus.DRAFT
    
    allocations: list[ResourceAllocation]
    
    total_cost_usd: float
    total_duration_hours: float
    
    optimization_score: float = Field(0, ge=0, le=1.0)
    reliability_score: float = Field(0, ge=0, le=1.0)
    carbon_footprint_kg: float = Field(0, ge=0)
    
    plan_type: str  # "cheapest", "fastest", "balanced", "greenest"
    
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class PlanComparison(BaseModel):
    """Comparison of multiple execution plans."""
    workload_id: str
    plans: list[ExecutionPlan]
    recommended_plan_id: str
    recommendation_reason: str
    
    baseline_cost_usd: float
    baseline_duration_hours: float
    
    cost_savings_vs_baseline: float
    time_savings_vs_baseline: float


# =============================================================================
# Execution Models
# =============================================================================


class ExecutionStageStatus(BaseModel):
    """Status of a single execution stage."""
    stage_id: str
    status: str  # "pending", "provisioning", "running", "completed", "failed"
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    actual_cost_usd: float = 0
    actual_duration_hours: float = 0
    
    utilization_percent: float = 0
    error_message: Optional[str] = None


class ExecutionState(BaseModel):
    """State of workload execution."""
    plan_id: str
    workload_id: str
    
    status: str  # "provisioning", "running", "completed", "failed"
    
    stages: list[ExecutionStageStatus]
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    actual_total_cost_usd: float = 0
    actual_total_duration_hours: float = 0
    
    predicted_cost_usd: float
    predicted_duration_hours: float
    
    prediction_error_cost: float = 0
    prediction_error_duration: float = 0


# =============================================================================
# Learning & Analytics Models
# =============================================================================


class EpisodeResult(BaseModel):
    """Result of a completed episode for learning."""
    episode_id: str
    workload_id: str
    plan_id: str
    
    workload_type: WorkloadType
    optimization_objective: OptimizationWeights
    
    negotiation_strategy: NegotiationStrategy
    negotiation_rounds: int
    
    predicted_cost: float
    actual_cost: float
    predicted_duration: float
    actual_duration: float
    
    sla_met: bool
    within_budget: bool
    
    total_reward: float
    
    provider_ids: list[str]
    
    regret_vs_oracle: float = 0
    human_approved: bool
    replan_count: int = 0
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StrategyPerformance(BaseModel):
    """Performance metrics for a negotiation strategy."""
    strategy: NegotiationStrategy
    episode_count: int
    
    avg_reward: float
    avg_cost_savings: float
    avg_negotiation_rounds: float
    
    approval_rate: float
    sla_success_rate: float
    
    win_rate_by_provider: dict[str, float] = Field(default_factory=dict)


# =============================================================================
# OpenEnv Action & Observation Models
# =============================================================================


class ComputeMarketAction(BaseModel):
    """Base action for the ComputeMarket environment."""
    action_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CharacterizeWorkloadAction(ComputeMarketAction):
    """Action to characterize a submitted workload."""
    action_type: str = "characterize_workload"
    workload: WorkloadSpec


class RequestQuotesAction(ComputeMarketAction):
    """Action to request quotes from providers."""
    action_type: str = "request_quotes"
    decomposition: WorkloadDecomposition
    target_providers: list[str] = Field(default_factory=list)


class CounterOfferAction(ComputeMarketAction):
    """Action to counter an offer."""
    action_type: str = "counter_offer"
    offer_id: str
    counter_price_usd: float
    counter_terms: dict[str, Any] = Field(default_factory=dict)


class SwitchStrategyAction(ComputeMarketAction):
    """Action to switch negotiation strategy."""
    action_type: str = "switch_strategy"
    new_strategy: NegotiationStrategy
    reason: str = ""


class GeneratePlanAction(ComputeMarketAction):
    """Action to generate execution plans."""
    action_type: str = "generate_plan"
    plan_type: str = "balanced"


class SubmitForApprovalAction(ComputeMarketAction):
    """Action to submit plan for human approval."""
    action_type: str = "submit_for_approval"
    plan_id: str
    summary: str


class RevisePlanAction(ComputeMarketAction):
    """Action to revise a plan based on feedback."""
    action_type: str = "revise_plan"
    plan_id: str
    feedback: str
    constraints: dict[str, Any] = Field(default_factory=dict)


class ApprovePlanAction(ComputeMarketAction):
    """Human action to approve a plan."""
    action_type: str = "approve_plan"
    plan_id: str
    approver: str = "human"


class RejectPlanAction(ComputeMarketAction):
    """Human action to reject a plan."""
    action_type: str = "reject_plan"
    plan_id: str
    reason: str
    feedback: str = ""


class ExecutePlanAction(ComputeMarketAction):
    """Action to execute an approved plan."""
    action_type: str = "execute_plan"
    plan_id: str


class FinalizeEpisodeAction(ComputeMarketAction):
    """Action to finalize the episode and collect rewards."""
    action_type: str = "finalize_episode"


class ComputeMarketObservation(BaseModel):
    """Observation returned by the ComputeMarket environment."""
    done: bool = False
    reward: float = 0.0
    
    episode_id: str
    step_count: int
    
    workload: Optional[WorkloadSpec] = None
    decomposition: Optional[WorkloadDecomposition] = None
    
    market_state: Optional[dict[str, Any]] = None
    available_providers: list[str] = Field(default_factory=list)
    
    current_offers: list[ProviderOffer] = Field(default_factory=list)
    negotiation_state: Optional[NegotiationState] = None
    
    plan_candidates: list[ExecutionPlan] = Field(default_factory=list)
    selected_plan: Optional[ExecutionPlan] = None
    
    approval_status: Optional[ApprovalDecision] = None
    approval_feedback: str = ""
    
    execution_state: Optional[ExecutionState] = None
    
    reward_breakdown: dict[str, float] = Field(default_factory=dict)
    hints: list[str] = Field(default_factory=list)
    
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComputeMarketState(BaseModel):
    """Internal state of the ComputeMarket environment."""
    episode_id: str
    step_count: int = 0
    
    phase: str = "initialization"
    
    workload: Optional[WorkloadSpec] = None
    decomposition: Optional[WorkloadDecomposition] = None
    
    providers: list[ProviderProfile] = Field(default_factory=list)
    provider_offers: dict[str, list[ProviderOffer]] = Field(default_factory=dict)
    
    negotiation: Optional[NegotiationState] = None
    
    plans: list[ExecutionPlan] = Field(default_factory=list)
    selected_plan_id: Optional[str] = None
    
    approval_decision: Optional[ApprovalDecision] = None
    approval_feedback: str = ""
    
    execution: Optional[ExecutionState] = None
    
    episode_reward: float = 0.0
    intermediate_rewards: list[float] = Field(default_factory=list)
    
    history: list[dict[str, Any]] = Field(default_factory=list)

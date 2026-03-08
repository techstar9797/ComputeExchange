"""
ComputeMarketEnvironment - OpenEnv Server-Side Implementation

This is the core environment that implements the Gymnasium-style API:
- reset(): Initialize a new episode
- step(action): Execute an action and return observation
- state: Access current episode state

The environment orchestrates multiple internal agents and simulates
a realistic compute marketplace.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

try:
    from openenv.core.env_server.types import Action, Observation, State
    from openenv.core.env_server.environment import Environment
except ImportError:
    # Standalone base classes
    from pydantic import BaseModel
    
    class Action(BaseModel):
        metadata: dict = {}
    
    class Observation(BaseModel):
        done: bool = False
        reward: float = 0.0
        metadata: dict = {}
    
    class State(BaseModel):
        episode_id: str = ""
        step_count: int = 0
    
    class Environment:
        pass

from .shared_models import (
    ApprovalDecision,
    ComputeMarketAction,
    ComputeMarketObservation,
    ComputeMarketState,
    ExecutionPlan,
    ExecutionStageStatus,
    ExecutionState,
    NegotiationState,
    NegotiationStrategy,
    PlanStatus,
    ProviderOffer,
    ResourceAllocation,
    ResourceType,
    TaskStage,
    TaskStageType,
    WorkloadDecomposition,
    WorkloadSpec,
    WorkloadType,
)

from .market_simulator import MarketSimulator
from .reward_engine import RewardEngine
from .scenario_generator import ScenarioGenerator


class ComputeMarketEnvironment(Environment):
    """
    OpenEnv environment for the compute marketplace.
    
    Episode Phases:
    1. initialization - Waiting for workload submission
    2. characterization - Analyzing and decomposing workload
    3. negotiation - Negotiating with providers
    4. planning - Generating execution plans
    5. approval - Waiting for human approval
    6. execution - Simulating workload execution
    7. finalization - Calculating final rewards
    
    Reward Structure:
    - Intermediate shaping rewards during negotiation and planning
    - Delayed reward after execution completes
    - Penalties for SLA violations, budget overruns, failed negotiations
    """
    
    PHASES = [
        "initialization",
        "characterization", 
        "negotiation",
        "planning",
        "approval",
        "execution",
        "finalization",
    ]
    
    def __init__(
        self,
        scenario_id: Optional[str] = None,
        max_steps: int = 50,
        max_negotiation_rounds: int = 5,
    ):
        """
        Initialize the ComputeMarket environment.
        
        Args:
            scenario_id: Optional scenario to load (None for random)
            max_steps: Maximum steps per episode
            max_negotiation_rounds: Maximum negotiation rounds allowed
        """
        self.scenario_id = scenario_id
        self.max_steps = max_steps
        self.max_negotiation_rounds = max_negotiation_rounds
        
        self.market = MarketSimulator()
        self.reward_engine = RewardEngine()
        self.scenario_gen = ScenarioGenerator()
        
        self._state: Optional[ComputeMarketState] = None
        self._episode_trajectory: list[dict] = []
    
    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Observation:
        """
        Reset the environment for a new episode.
        
        Args:
            seed: Random seed for reproducibility
            episode_id: Custom episode ID
            scenario_id: Scenario to load (overrides init)
            **kwargs: Additional reset parameters
            
        Returns:
            Initial observation
        """
        episode_id = episode_id or str(uuid4())
        
        # Generate or load scenario
        if scenario_id or self.scenario_id:
            scenario = self.scenario_gen.load_scenario(scenario_id or self.scenario_id)
        else:
            scenario = self.scenario_gen.generate_random(seed=seed)
        
        # Initialize market with providers
        self.market.reset(providers=scenario.providers, seed=seed)
        
        # Initialize state
        self._state = ComputeMarketState(
            episode_id=episode_id,
            step_count=0,
            phase="initialization",
            providers=scenario.providers,
            workload=scenario.workload if hasattr(scenario, 'workload') else None,
        )
        
        self._episode_trajectory = []
        
        return self._create_observation(
            reward=0.0,
            done=False,
            hints=["Submit a workload using characterize_workload action"],
        )
    
    def step(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        """
        Execute an action in the environment.
        
        Args:
            action: The action to execute
            timeout_s: Optional timeout
            **kwargs: Additional parameters
            
        Returns:
            Observation after action execution
        """
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        self._state.step_count += 1
        
        # Record trajectory
        self._episode_trajectory.append({
            "step": self._state.step_count,
            "phase": self._state.phase,
            "action": action.model_dump() if hasattr(action, 'model_dump') else str(action),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Check step limit
        if self._state.step_count >= self.max_steps:
            return self._handle_timeout()
        
        # Route action based on type
        action_data = action.model_dump() if hasattr(action, 'model_dump') else {}
        action_type = action_data.get("action_type", "unknown")
        
        handlers = {
            "characterize_workload": self._handle_characterize,
            "request_quotes": self._handle_request_quotes,
            "counter_offer": self._handle_counter_offer,
            "switch_strategy": self._handle_switch_strategy,
            "generate_plan": self._handle_generate_plan,
            "submit_for_approval": self._handle_submit_approval,
            "revise_plan": self._handle_revise_plan,
            "approve_plan": self._handle_approve,
            "reject_plan": self._handle_reject,
            "execute_plan": self._handle_execute,
            "finalize_episode": self._handle_finalize,
        }
        
        handler = handlers.get(action_type, self._handle_unknown)
        return handler(action_data)
    
    @property
    def state(self) -> State:
        """Get current environment state."""
        if self._state is None:
            return ComputeMarketState(episode_id="", step_count=0, phase="uninitialized")
        return self._state
    
    def get_trajectory(self) -> list[dict]:
        """Get the episode trajectory for training/analysis."""
        return self._episode_trajectory.copy()
    
    # ==========================================================================
    # Action Handlers
    # ==========================================================================
    
    def _handle_characterize(self, action_data: dict) -> Observation:
        """Handle workload characterization."""
        if self._state.phase not in ["initialization", "characterization"]:
            return self._create_error_observation(
                f"Cannot characterize in phase: {self._state.phase}"
            )
        
        workload_data = action_data.get("workload", {})
        if not workload_data:
            return self._create_error_observation("No workload provided")
        
        workload = WorkloadSpec(**workload_data)
        self._state.workload = workload
        
        # Decompose workload into stages
        decomposition = self._decompose_workload(workload)
        self._state.decomposition = decomposition
        self._state.phase = "characterization"
        
        # Shaping reward for successful characterization
        reward = self.reward_engine.compute_characterization_reward(workload, decomposition)
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=["Request quotes from providers using request_quotes action"],
        )
    
    def _handle_request_quotes(self, action_data: dict) -> Observation:
        """Handle quote requests from providers."""
        if self._state.phase not in ["characterization", "negotiation"]:
            return self._create_error_observation(
                f"Cannot request quotes in phase: {self._state.phase}"
            )
        
        if self._state.decomposition is None:
            return self._create_error_observation("No workload decomposition available")
        
        target_providers = action_data.get("target_providers", [])
        
        # Initialize negotiation state if needed
        if self._state.negotiation is None:
            self._state.negotiation = NegotiationState(
                workload_id=self._state.workload.id,
                strategy=NegotiationStrategy.BALANCED,
                active_providers=[p.id for p in self._state.providers],
            )
        
        # Get quotes from market
        offers = self.market.request_quotes(
            decomposition=self._state.decomposition,
            target_providers=target_providers or [p.id for p in self._state.providers],
        )
        
        self._state.negotiation.offers.extend(offers)
        self._state.negotiation.current_round += 1
        self._state.phase = "negotiation"
        
        # Store offers by provider
        for offer in offers:
            if offer.provider_id not in self._state.provider_offers:
                self._state.provider_offers[offer.provider_id] = []
            self._state.provider_offers[offer.provider_id].append(offer)
        
        # Shaping reward for getting competitive quotes
        reward = self.reward_engine.compute_negotiation_reward(
            offers=offers,
            workload=self._state.workload,
            round_num=self._state.negotiation.current_round,
        )
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=["Generate a plan or continue negotiating with counter_offer"],
        )
    
    def _handle_counter_offer(self, action_data: dict) -> Observation:
        """Handle counter-offer to a provider."""
        if self._state.phase != "negotiation":
            return self._create_error_observation("Cannot counter-offer outside negotiation")
        
        if self._state.negotiation.current_round >= self.max_negotiation_rounds:
            return self._create_error_observation("Maximum negotiation rounds reached")
        
        offer_id = action_data.get("offer_id")
        counter_price = action_data.get("counter_price_usd")
        
        # Process counter-offer through market
        response = self.market.process_counter_offer(
            offer_id=offer_id,
            counter_price=counter_price,
            counter_terms=action_data.get("counter_terms", {}),
        )
        
        self._state.negotiation.current_round += 1
        
        if response.get("accepted"):
            # Provider accepted counter-offer
            new_offer = ProviderOffer(**response["offer"])
            self._state.negotiation.offers.append(new_offer)
            reward = 0.1  # Bonus for successful negotiation
        else:
            # Provider made counter-counter-offer or rejected
            reward = -0.02  # Small penalty for failed round
        
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(reward=reward, done=False)
    
    def _handle_switch_strategy(self, action_data: dict) -> Observation:
        """Handle negotiation strategy switch."""
        if self._state.negotiation is None:
            return self._create_error_observation("No active negotiation")
        
        new_strategy = NegotiationStrategy(action_data.get("new_strategy", "balanced"))
        old_strategy = self._state.negotiation.strategy
        self._state.negotiation.strategy = new_strategy
        
        # Small penalty for switching strategies (represents cognitive cost)
        reward = -0.01
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=[f"Strategy changed from {old_strategy} to {new_strategy}"],
        )
    
    def _handle_generate_plan(self, action_data: dict) -> Observation:
        """Handle plan generation."""
        if self._state.phase not in ["negotiation", "planning"]:
            return self._create_error_observation(
                f"Cannot generate plan in phase: {self._state.phase}"
            )
        
        plan_type = action_data.get("plan_type", "balanced")
        
        # Generate plans using available offers
        plans = self._generate_plans(
            decomposition=self._state.decomposition,
            offers=self._state.negotiation.offers if self._state.negotiation else [],
            plan_types=[plan_type, "cheapest", "fastest", "greenest"],
        )
        
        self._state.plans = plans
        self._state.phase = "planning"
        
        # Reward for plan diversity and quality
        reward = self.reward_engine.compute_planning_reward(
            plans=plans,
            workload=self._state.workload,
        )
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=["Submit a plan for approval using submit_for_approval"],
        )
    
    def _handle_submit_approval(self, action_data: dict) -> Observation:
        """Handle plan submission for approval."""
        if self._state.phase != "planning":
            return self._create_error_observation("No plans available for approval")
        
        plan_id = action_data.get("plan_id")
        
        # Find the plan
        plan = next((p for p in self._state.plans if p.id == plan_id), None)
        if plan is None:
            return self._create_error_observation(f"Plan not found: {plan_id}")
        
        plan.status = PlanStatus.PENDING_APPROVAL
        self._state.selected_plan_id = plan_id
        self._state.phase = "approval"
        
        return self._create_observation(
            reward=0.0,
            done=False,
            hints=["Waiting for human approval. Use approve_plan or reject_plan."],
        )
    
    def _handle_revise_plan(self, action_data: dict) -> Observation:
        """Handle plan revision based on feedback."""
        plan_id = action_data.get("plan_id")
        feedback = action_data.get("feedback", "")
        
        # Find and revise the plan
        plan = next((p for p in self._state.plans if p.id == plan_id), None)
        if plan is None:
            return self._create_error_observation(f"Plan not found: {plan_id}")
        
        # Create revised plan (simplified - would use LLM in production)
        revised_plan = self._revise_plan(plan, feedback, action_data.get("constraints", {}))
        self._state.plans.append(revised_plan)
        
        # Penalty for replanning
        reward = -0.05
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=["Revised plan generated. Submit for approval."],
        )
    
    def _handle_approve(self, action_data: dict) -> Observation:
        """Handle human approval."""
        if self._state.phase != "approval":
            return self._create_error_observation("No plan pending approval")
        
        plan_id = action_data.get("plan_id")
        plan = next((p for p in self._state.plans if p.id == plan_id), None)
        
        if plan is None:
            return self._create_error_observation(f"Plan not found: {plan_id}")
        
        plan.status = PlanStatus.APPROVED
        plan.approved_at = datetime.utcnow()
        plan.approved_by = action_data.get("approver", "human")
        
        self._state.approval_decision = ApprovalDecision.APPROVE
        self._state.phase = "execution"
        
        # Reward for getting approval
        reward = 0.1
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=["Plan approved. Execute with execute_plan action."],
        )
    
    def _handle_reject(self, action_data: dict) -> Observation:
        """Handle human rejection."""
        if self._state.phase != "approval":
            return self._create_error_observation("No plan pending approval")
        
        plan_id = action_data.get("plan_id")
        reason = action_data.get("reason", "")
        feedback = action_data.get("feedback", "")
        
        plan = next((p for p in self._state.plans if p.id == plan_id), None)
        if plan:
            plan.status = PlanStatus.REJECTED
        
        self._state.approval_decision = ApprovalDecision.REJECT
        self._state.approval_feedback = feedback
        self._state.phase = "planning"  # Go back to planning
        
        # Penalty for rejection
        reward = -0.15
        self._state.intermediate_rewards.append(reward)
        
        return self._create_observation(
            reward=reward,
            done=False,
            hints=[f"Plan rejected: {reason}. Revise and resubmit."],
        )
    
    def _handle_execute(self, action_data: dict) -> Observation:
        """Handle plan execution."""
        if self._state.phase != "execution":
            return self._create_error_observation("No approved plan to execute")
        
        plan_id = action_data.get("plan_id")
        plan = next((p for p in self._state.plans if p.id == plan_id), None)
        
        if plan is None or plan.status != PlanStatus.APPROVED:
            return self._create_error_observation("Plan not approved")
        
        plan.status = PlanStatus.EXECUTING
        
        # Simulate execution
        execution_result = self.market.simulate_execution(
            plan=plan,
            decomposition=self._state.decomposition,
        )
        
        self._state.execution = execution_result
        
        # Check if execution completed
        if execution_result.status == "completed":
            plan.status = PlanStatus.COMPLETED
            self._state.phase = "finalization"
            
            return self._create_observation(
                reward=0.0,  # Delayed reward at finalization
                done=False,
                hints=["Execution completed. Finalize episode for final reward."],
            )
        else:
            plan.status = PlanStatus.FAILED
            
            # Penalty for failed execution
            reward = -0.3
            self._state.intermediate_rewards.append(reward)
            
            return self._create_observation(
                reward=reward,
                done=True,
                hints=["Execution failed."],
            )
    
    def _handle_finalize(self, action_data: dict) -> Observation:
        """Handle episode finalization."""
        if self._state.execution is None:
            return self._create_error_observation("No execution to finalize")
        
        # Calculate final reward
        final_reward = self.reward_engine.compute_final_reward(
            workload=self._state.workload,
            plan=next((p for p in self._state.plans if p.id == self._state.selected_plan_id), None),
            execution=self._state.execution,
            intermediate_rewards=self._state.intermediate_rewards,
        )
        
        self._state.episode_reward = final_reward
        self._state.phase = "finalization"
        
        # Record final trajectory entry
        self._episode_trajectory.append({
            "step": self._state.step_count,
            "phase": "finalization",
            "final_reward": final_reward,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return self._create_observation(
            reward=final_reward,
            done=True,
            hints=["Episode completed."],
        )
    
    def _handle_timeout(self) -> Observation:
        """Handle episode timeout."""
        reward = -0.5  # Penalty for timeout
        self._state.episode_reward = sum(self._state.intermediate_rewards) + reward
        
        return self._create_observation(
            reward=reward,
            done=True,
            hints=["Episode timed out - maximum steps reached."],
        )
    
    def _handle_unknown(self, action_data: dict) -> Observation:
        """Handle unknown action types."""
        return self._create_error_observation(
            f"Unknown action type: {action_data.get('action_type', 'missing')}"
        )
    
    # ==========================================================================
    # Helper Methods
    # ==========================================================================
    
    def _create_observation(
        self,
        reward: float,
        done: bool,
        hints: Optional[list[str]] = None,
    ) -> ComputeMarketObservation:
        """Create an observation from current state."""
        return ComputeMarketObservation(
            done=done,
            reward=reward,
            episode_id=self._state.episode_id,
            step_count=self._state.step_count,
            workload=self._state.workload,
            decomposition=self._state.decomposition,
            available_providers=[p.id for p in self._state.providers],
            current_offers=self._state.negotiation.offers if self._state.negotiation else [],
            negotiation_state=self._state.negotiation,
            plan_candidates=self._state.plans,
            selected_plan=next(
                (p for p in self._state.plans if p.id == self._state.selected_plan_id),
                None
            ) if self._state.selected_plan_id else None,
            approval_status=self._state.approval_decision,
            approval_feedback=self._state.approval_feedback,
            execution_state=self._state.execution,
            reward_breakdown=self.reward_engine.get_reward_breakdown(),
            hints=hints or [],
        )
    
    def _create_error_observation(self, error: str) -> ComputeMarketObservation:
        """Create an error observation."""
        return ComputeMarketObservation(
            done=False,
            reward=-0.05,  # Small penalty for invalid actions
            episode_id=self._state.episode_id if self._state else "",
            step_count=self._state.step_count if self._state else 0,
            hints=[f"Error: {error}"],
            metadata={"error": error},
        )
    
    def _decompose_workload(self, workload: WorkloadSpec) -> WorkloadDecomposition:
        """Decompose a workload into executable stages."""
        stages = []
        
        # Workload-type specific decomposition
        if workload.workload_type == WorkloadType.LLM_TRAINING:
            stages = [
                TaskStage(
                    name="Data Loading",
                    stage_type=TaskStageType.DATA_LOADING,
                    required_resource_types=[ResourceType.CPU, ResourceType.MEMORY],
                    estimated_duration_hours=workload.deadline_hours * 0.05,
                    parallelizable=True,
                    can_use_spot=True,
                ),
                TaskStage(
                    name="Preprocessing",
                    stage_type=TaskStageType.PREPROCESSING,
                    required_resource_types=[ResourceType.CPU],
                    estimated_duration_hours=workload.deadline_hours * 0.1,
                    parallelizable=True,
                ),
                TaskStage(
                    name="Model Training",
                    stage_type=TaskStageType.COMPUTE_INTENSIVE,
                    required_resource_types=[ResourceType.GPU],
                    preferred_resource_types=[ResourceType.TPU],
                    estimated_duration_hours=workload.deadline_hours * 0.7,
                    estimated_memory_gb=workload.model_size_gb or 16,
                    latency_sensitive=False,
                    can_use_spot=workload.allow_spot_instances,
                ),
                TaskStage(
                    name="Checkpointing",
                    stage_type=TaskStageType.IO_HEAVY,
                    required_resource_types=[ResourceType.CPU, ResourceType.MEMORY],
                    estimated_duration_hours=workload.deadline_hours * 0.1,
                ),
                TaskStage(
                    name="Evaluation",
                    stage_type=TaskStageType.COMPUTE_INTENSIVE,
                    required_resource_types=[ResourceType.GPU],
                    estimated_duration_hours=workload.deadline_hours * 0.05,
                ),
            ]
        elif workload.workload_type == WorkloadType.REALTIME_INFERENCE:
            stages = [
                TaskStage(
                    name="Model Loading",
                    stage_type=TaskStageType.DATA_LOADING,
                    required_resource_types=[ResourceType.GPU, ResourceType.MEMORY],
                    estimated_duration_hours=0.1,
                    latency_sensitive=True,
                    can_use_spot=False,
                ),
                TaskStage(
                    name="Inference Serving",
                    stage_type=TaskStageType.COMPUTE_INTENSIVE,
                    required_resource_types=[ResourceType.GPU],
                    preferred_resource_types=[ResourceType.NPU],
                    estimated_duration_hours=workload.deadline_hours,
                    latency_sensitive=True,
                    can_use_spot=False,
                ),
            ]
        else:
            # Default decomposition
            stages = [
                TaskStage(
                    name="Setup",
                    stage_type=TaskStageType.PREPROCESSING,
                    required_resource_types=[ResourceType.CPU],
                    estimated_duration_hours=workload.deadline_hours * 0.1,
                ),
                TaskStage(
                    name="Main Compute",
                    stage_type=TaskStageType.COMPUTE_INTENSIVE,
                    required_resource_types=[ResourceType.GPU, ResourceType.CPU],
                    estimated_duration_hours=workload.deadline_hours * 0.8,
                ),
                TaskStage(
                    name="Finalization",
                    stage_type=TaskStageType.POSTPROCESSING,
                    required_resource_types=[ResourceType.CPU],
                    estimated_duration_hours=workload.deadline_hours * 0.1,
                ),
            ]
        
        # Set dependencies
        for i in range(1, len(stages)):
            if not stages[i].parallelizable:
                stages[i].dependencies = [stages[i-1].id]
        
        total_hours = sum(s.estimated_duration_hours for s in stages)
        critical_path = self._calculate_critical_path(stages)
        
        return WorkloadDecomposition(
            workload_id=workload.id,
            stages=stages,
            total_estimated_hours=total_hours,
            total_estimated_cost_usd=workload.budget_usd * 0.7,  # Estimate
            critical_path_hours=critical_path,
            parallelism_factor=total_hours / critical_path if critical_path > 0 else 1.0,
        )
    
    def _calculate_critical_path(self, stages: list[TaskStage]) -> float:
        """Calculate critical path duration through stages."""
        # Simplified critical path - sequential stages
        sequential_time = 0.0
        parallel_time = 0.0
        
        for stage in stages:
            if stage.parallelizable and not stage.dependencies:
                parallel_time = max(parallel_time, stage.estimated_duration_hours)
            else:
                sequential_time += stage.estimated_duration_hours
        
        return sequential_time + parallel_time
    
    def _generate_plans(
        self,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        plan_types: list[str],
    ) -> list[ExecutionPlan]:
        """Generate execution plans from offers."""
        plans = []
        
        for plan_type in plan_types:
            # Sort offers based on plan type
            if plan_type == "cheapest":
                sorted_offers = sorted(offers, key=lambda o: o.quoted_price_usd)
            elif plan_type == "fastest":
                sorted_offers = sorted(offers, key=lambda o: o.quoted_duration_hours)
            elif plan_type == "greenest":
                sorted_offers = sorted(offers, key=lambda o: o.carbon_footprint_kg)
            else:  # balanced
                sorted_offers = sorted(
                    offers,
                    key=lambda o: o.quoted_price_usd * 0.5 + o.quoted_duration_hours * 100 * 0.5
                )
            
            if not sorted_offers:
                continue
            
            # Build allocations from best offers
            allocations = []
            total_cost = 0.0
            total_duration = 0.0
            
            for stage in decomposition.stages:
                # Find best offer for this stage
                stage_offers = [o for o in sorted_offers if stage.id in o.stage_ids or not o.stage_ids]
                if stage_offers:
                    best = stage_offers[0]
                    allocation = ResourceAllocation(
                        stage_id=stage.id,
                        provider_id=best.provider_id,
                        provider_name=best.provider_name,
                        resource_type=stage.required_resource_types[0],
                        resource_count=best.resource_allocation.get(stage.required_resource_types[0], 1),
                        estimated_cost_usd=best.quoted_price_usd / len(decomposition.stages),
                        estimated_duration_hours=best.quoted_duration_hours / len(decomposition.stages),
                        is_spot=best.is_spot,
                    )
                    allocations.append(allocation)
                    total_cost += allocation.estimated_cost_usd
                    total_duration = max(total_duration, allocation.estimated_duration_hours)
            
            if allocations:
                plan = ExecutionPlan(
                    workload_id=decomposition.workload_id,
                    allocations=allocations,
                    total_cost_usd=total_cost,
                    total_duration_hours=total_duration,
                    plan_type=plan_type,
                    optimization_score=0.8,  # Would calculate properly
                    reliability_score=0.95,
                )
                plans.append(plan)
        
        return plans
    
    def _revise_plan(
        self,
        plan: ExecutionPlan,
        feedback: str,
        constraints: dict,
    ) -> ExecutionPlan:
        """Revise a plan based on feedback."""
        # Simplified revision - would use LLM in production
        revised = ExecutionPlan(
            workload_id=plan.workload_id,
            version=plan.version + 1,
            allocations=plan.allocations,
            total_cost_usd=plan.total_cost_usd * 0.95,  # Try to reduce cost
            total_duration_hours=plan.total_duration_hours,
            plan_type=plan.plan_type,
            optimization_score=plan.optimization_score,
            reliability_score=plan.reliability_score,
            assumptions=plan.assumptions + [f"Revised based on: {feedback}"],
        )
        return revised

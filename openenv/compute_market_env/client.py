"""
ComputeMarketEnv Client

Client for connecting to the ComputeMarketEnv server.
Supports both async and sync usage patterns.
"""

from typing import Any, Optional

try:
    from openenv.core.env_client import EnvClient
    from openenv.core.env_client.types import StepResult
except ImportError:
    # Fallback for standalone usage without openenv installed
    class EnvClient:
        """Stub base class when openenv is not installed."""
        def __init__(self, base_url: str):
            self.base_url = base_url
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    class StepResult:
        """Stub step result."""
        def __init__(self, observation: Any, reward: float, done: bool):
            self.observation = observation
            self.reward = reward
            self.done = done

from .types_export import (
    ComputeMarketAction,
    ComputeMarketObservation,
    CharacterizeWorkloadAction,
    RequestQuotesAction,
    GeneratePlanAction,
    SubmitForApprovalAction,
    ApprovePlanAction,
    ExecutePlanAction,
    FinalizeEpisodeAction,
    WorkloadSpec,
    WorkloadDecomposition,
)


class ComputeMarketEnv(EnvClient):
    """
    Client for the ComputeMarket environment.
    
    This environment simulates a compute resource marketplace where agents:
    1. Characterize incoming workloads
    2. Negotiate with providers for resources
    3. Generate optimized execution plans
    4. Submit plans for human approval
    5. Execute approved plans
    6. Learn from outcomes
    
    Episode Flow:
        reset() -> characterize_workload() -> request_quotes() -> 
        generate_plan() -> submit_for_approval() -> [approve/reject] ->
        execute_plan() -> finalize_episode()
    
    Example (sync):
        >>> with ComputeMarketEnv(base_url="http://localhost:8001").sync() as env:
        ...     obs = env.reset()
        ...     obs = env.characterize_workload(workload_spec)
        ...     obs = env.request_quotes()
        ...     obs = env.generate_plan("balanced")
        ...     obs = env.submit_for_approval(plan_id, "Optimized for cost-performance")
        ...     # Human reviews and approves
        ...     obs = env.approve_plan(plan_id)
        ...     obs = env.execute_plan(plan_id)
        ...     result = env.finalize_episode()
        ...     print(f"Total reward: {result.reward}")
    
    Example (async):
        >>> async with ComputeMarketEnv(base_url="http://localhost:8001") as env:
        ...     obs = await env.reset()
        ...     obs = await env.step(CharacterizeWorkloadAction(workload=spec))
        ...     # ... continue episode
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: float = 30.0,
    ):
        """
        Initialize the ComputeMarket client.
        
        Args:
            base_url: URL of the environment server
            timeout: Request timeout in seconds
        """
        super().__init__(base_url)
        self.timeout = timeout
        self._current_observation: Optional[ComputeMarketObservation] = None
    
    @property
    def observation(self) -> Optional[ComputeMarketObservation]:
        """Get the most recent observation."""
        return self._current_observation
    
    # Convenience methods for common actions
    
    def characterize_workload(self, workload: WorkloadSpec) -> ComputeMarketObservation:
        """
        Characterize a workload and decompose it into stages.
        
        Args:
            workload: The workload specification to analyze
            
        Returns:
            Observation with decomposition results
        """
        action = CharacterizeWorkloadAction(workload=workload)
        return self.step(action)
    
    def request_quotes(
        self,
        decomposition: Optional[WorkloadDecomposition] = None,
        target_providers: Optional[list[str]] = None,
    ) -> ComputeMarketObservation:
        """
        Request quotes from providers.
        
        Args:
            decomposition: Optional decomposition (uses current if not provided)
            target_providers: Optional list of provider IDs to target
            
        Returns:
            Observation with provider offers
        """
        if decomposition is None and self._current_observation:
            decomposition = self._current_observation.decomposition
        
        action = RequestQuotesAction(
            decomposition=decomposition,
            target_providers=target_providers or [],
        )
        return self.step(action)
    
    def generate_plan(self, plan_type: str = "balanced") -> ComputeMarketObservation:
        """
        Generate an execution plan.
        
        Args:
            plan_type: One of "cheapest", "fastest", "balanced", "greenest"
            
        Returns:
            Observation with plan candidates
        """
        action = GeneratePlanAction(plan_type=plan_type)
        return self.step(action)
    
    def submit_for_approval(
        self,
        plan_id: str,
        summary: str,
    ) -> ComputeMarketObservation:
        """
        Submit a plan for human approval.
        
        Args:
            plan_id: ID of the plan to submit
            summary: Human-readable summary of the plan
            
        Returns:
            Observation indicating pending approval
        """
        action = SubmitForApprovalAction(plan_id=plan_id, summary=summary)
        return self.step(action)
    
    def approve_plan(self, plan_id: str) -> ComputeMarketObservation:
        """
        Approve a plan (human action).
        
        Args:
            plan_id: ID of the plan to approve
            
        Returns:
            Observation with approved status
        """
        action = ApprovePlanAction(plan_id=plan_id)
        return self.step(action)
    
    def execute_plan(self, plan_id: str) -> ComputeMarketObservation:
        """
        Execute an approved plan.
        
        Args:
            plan_id: ID of the plan to execute
            
        Returns:
            Observation with execution state
        """
        action = ExecutePlanAction(plan_id=plan_id)
        return self.step(action)
    
    def finalize_episode(self) -> ComputeMarketObservation:
        """
        Finalize the episode and collect final reward.
        
        Returns:
            Final observation with total reward and metrics
        """
        action = FinalizeEpisodeAction()
        return self.step(action)

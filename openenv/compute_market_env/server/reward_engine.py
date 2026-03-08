"""
Reward Engine

Computes shaped rewards for the ComputeMarket environment.
Designed for RL training with both intermediate and delayed rewards.
"""

from typing import Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "shared-types"))

from models import (
    ExecutionPlan,
    ExecutionState,
    ProviderOffer,
    WorkloadDecomposition,
    WorkloadSpec,
)


class RewardEngine:
    """
    Computes shaped rewards for the compute marketplace environment.
    
    Reward Components:
    - Cost efficiency: Lower cost relative to budget
    - Time efficiency: Faster execution relative to deadline
    - SLA compliance: Meeting reliability requirements
    - Resource matching: Appropriate workload-resource pairing
    - Negotiation efficiency: Fewer rounds, better outcomes
    - Prediction accuracy: Estimated vs actual metrics
    - Human approval likelihood: Plan quality signals
    
    Penalties:
    - Budget overrun
    - Deadline miss
    - Execution failure
    - Poor resource matching
    - Excessive replanning
    """
    
    def __init__(
        self,
        cost_weight: float = 0.25,
        time_weight: float = 0.2,
        reliability_weight: float = 0.2,
        efficiency_weight: float = 0.15,
        accuracy_weight: float = 0.1,
        approval_weight: float = 0.1,
    ):
        """
        Initialize the reward engine with component weights.
        
        Args:
            cost_weight: Weight for cost-related rewards
            time_weight: Weight for time-related rewards
            reliability_weight: Weight for reliability rewards
            efficiency_weight: Weight for negotiation efficiency
            accuracy_weight: Weight for prediction accuracy
            approval_weight: Weight for approval-related rewards
        """
        self.weights = {
            "cost": cost_weight,
            "time": time_weight,
            "reliability": reliability_weight,
            "efficiency": efficiency_weight,
            "accuracy": accuracy_weight,
            "approval": approval_weight,
        }
        
        self._reward_breakdown: dict[str, float] = {}
    
    def get_reward_breakdown(self) -> dict[str, float]:
        """Get the breakdown of reward components."""
        return self._reward_breakdown.copy()
    
    def compute_characterization_reward(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
    ) -> float:
        """
        Compute reward for workload characterization quality.
        
        Args:
            workload: The original workload spec
            decomposition: The generated decomposition
            
        Returns:
            Shaping reward for characterization
        """
        reward = 0.0
        
        # Reward for reasonable decomposition
        if 2 <= len(decomposition.stages) <= 10:
            reward += 0.05
        
        # Reward for parallelism identification
        if decomposition.parallelism_factor > 1.0:
            reward += 0.03 * min(decomposition.parallelism_factor - 1.0, 1.0)
        
        # Reward for staying within time estimates
        if decomposition.critical_path_hours <= workload.deadline_hours:
            reward += 0.05
        else:
            reward -= 0.03  # Penalty for unrealistic decomposition
        
        # Reward for cost estimation
        if decomposition.total_estimated_cost_usd <= workload.budget_usd:
            reward += 0.02
        
        self._reward_breakdown["characterization"] = reward
        return reward
    
    def compute_negotiation_reward(
        self,
        offers: list[ProviderOffer],
        workload: WorkloadSpec,
        round_num: int,
    ) -> float:
        """
        Compute reward for negotiation progress.
        
        Args:
            offers: List of received offers
            workload: The workload spec
            round_num: Current negotiation round
            
        Returns:
            Shaping reward for negotiation
        """
        reward = 0.0
        
        if not offers:
            reward = -0.05  # Penalty for no offers
            self._reward_breakdown["negotiation"] = reward
            return reward
        
        # Reward for getting multiple offers (competition)
        if len(offers) >= 3:
            reward += 0.05
        elif len(offers) >= 2:
            reward += 0.02
        
        # Reward for offers within budget
        best_price = min(o.quoted_price_usd for o in offers)
        if best_price <= workload.budget_usd:
            budget_efficiency = 1 - (best_price / workload.budget_usd)
            reward += 0.1 * budget_efficiency
        else:
            reward -= 0.05  # Penalty for all offers over budget
        
        # Reward for offers within deadline
        best_time = min(o.quoted_duration_hours for o in offers)
        if best_time <= workload.deadline_hours:
            time_efficiency = 1 - (best_time / workload.deadline_hours)
            reward += 0.05 * time_efficiency
        
        # Penalty for many negotiation rounds (efficiency)
        if round_num > 3:
            reward -= 0.02 * (round_num - 3)
        
        self._reward_breakdown["negotiation"] = reward
        return reward
    
    def compute_planning_reward(
        self,
        plans: list[ExecutionPlan],
        workload: WorkloadSpec,
    ) -> float:
        """
        Compute reward for plan generation quality.
        
        Args:
            plans: Generated execution plans
            workload: The workload spec
            
        Returns:
            Shaping reward for planning
        """
        reward = 0.0
        
        if not plans:
            reward = -0.1
            self._reward_breakdown["planning"] = reward
            return reward
        
        # Reward for plan diversity
        plan_types = set(p.plan_type for p in plans)
        if len(plan_types) >= 3:
            reward += 0.05
        elif len(plan_types) >= 2:
            reward += 0.02
        
        # Find best plan by optimization score
        best_plan = max(plans, key=lambda p: p.optimization_score)
        
        # Reward for high optimization score
        reward += 0.1 * best_plan.optimization_score
        
        # Reward for meeting budget constraint
        if best_plan.total_cost_usd <= workload.budget_usd:
            reward += 0.05
        else:
            overrun = (best_plan.total_cost_usd - workload.budget_usd) / workload.budget_usd
            reward -= 0.1 * min(overrun, 1.0)
        
        # Reward for meeting deadline
        if best_plan.total_duration_hours <= workload.deadline_hours:
            reward += 0.05
        else:
            overrun = (best_plan.total_duration_hours - workload.deadline_hours) / workload.deadline_hours
            reward -= 0.1 * min(overrun, 1.0)
        
        # Reward for reliability
        reward += 0.05 * best_plan.reliability_score
        
        self._reward_breakdown["planning"] = reward
        return reward
    
    def compute_final_reward(
        self,
        workload: WorkloadSpec,
        plan: Optional[ExecutionPlan],
        execution: ExecutionState,
        intermediate_rewards: list[float],
    ) -> float:
        """
        Compute the final delayed reward after execution.
        
        This is the main reward signal for RL training.
        
        Args:
            workload: The workload spec
            plan: The executed plan
            execution: Execution results
            intermediate_rewards: List of shaping rewards received
            
        Returns:
            Final reward value
        """
        reward = 0.0
        
        # Major component: Execution success
        if execution.status == "completed":
            reward += 0.3
        else:
            reward -= 0.5  # Major penalty for failed execution
            self._reward_breakdown["final"] = reward
            return reward
        
        # Cost efficiency
        cost_ratio = execution.actual_total_cost_usd / workload.budget_usd
        if cost_ratio <= 1.0:
            cost_reward = (1 - cost_ratio) * 0.3  # Up to 0.3 for cost savings
            reward += cost_reward
        else:
            cost_penalty = min(cost_ratio - 1.0, 1.0) * 0.4  # Penalty for overrun
            reward -= cost_penalty
        
        # Time efficiency
        time_ratio = execution.actual_total_duration_hours / workload.deadline_hours
        if time_ratio <= 1.0:
            time_reward = (1 - time_ratio) * 0.2  # Up to 0.2 for time savings
            reward += time_reward
        else:
            time_penalty = min(time_ratio - 1.0, 1.0) * 0.3  # Penalty for missing deadline
            reward -= time_penalty
        
        # SLA compliance
        sla_met = (
            execution.actual_total_cost_usd <= workload.budget_usd and
            execution.actual_total_duration_hours <= workload.deadline_hours
        )
        if sla_met:
            reward += 0.2
        
        # Prediction accuracy (lower error is better)
        avg_error = (execution.prediction_error_cost + execution.prediction_error_duration) / 2
        accuracy_reward = max(0, 0.1 - avg_error * 0.2)
        reward += accuracy_reward
        
        # Resource utilization
        avg_utilization = sum(
            s.utilization_percent for s in execution.stages
        ) / max(len(execution.stages), 1)
        if avg_utilization >= 70:
            reward += 0.05
        
        self._reward_breakdown["cost_efficiency"] = cost_ratio
        self._reward_breakdown["time_efficiency"] = time_ratio
        self._reward_breakdown["sla_met"] = 1.0 if sla_met else 0.0
        self._reward_breakdown["prediction_accuracy"] = 1 - avg_error
        self._reward_breakdown["utilization"] = avg_utilization / 100
        self._reward_breakdown["final"] = reward
        
        return round(reward, 4)
    
    def compute_regret(
        self,
        actual_reward: float,
        oracle_reward: float,
    ) -> float:
        """
        Compute regret vs oracle baseline.
        
        Args:
            actual_reward: Reward achieved
            oracle_reward: Best possible reward (oracle)
            
        Returns:
            Regret value (oracle - actual)
        """
        return max(0, oracle_reward - actual_reward)

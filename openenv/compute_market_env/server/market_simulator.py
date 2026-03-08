"""
Market Simulator

Simulates realistic compute market conditions including:
- Variable spot pricing
- Provider capacity constraints
- Negotiation dynamics
- Execution outcomes with variance
"""

import random
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from .shared_models import (
    ExecutionPlan,
    ExecutionStageStatus,
    ExecutionState,
    NegotiationStrategy,
    ProviderOffer,
    ProviderProfile,
    ResourceType,
    WorkloadDecomposition,
)


class MarketSimulator:
    """
    Simulates the compute resource marketplace.
    
    Features:
    - Dynamic pricing based on supply/demand
    - Provider negotiation behavior
    - Execution simulation with realistic variance
    - Failure injection for robustness testing
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the market simulator."""
        self.rng = random.Random(seed)
        self.providers: list[ProviderProfile] = []
        self.market_conditions: dict[str, float] = {
            "demand_multiplier": 1.0,
            "spot_availability": 0.8,
            "failure_rate": 0.02,
        }
        self._offer_cache: dict[str, ProviderOffer] = {}
    
    def reset(
        self,
        providers: list[ProviderProfile],
        seed: Optional[int] = None,
    ) -> None:
        """Reset the market with new providers and conditions."""
        if seed is not None:
            self.rng = random.Random(seed)
        
        self.providers = providers
        self._offer_cache.clear()
        
        # Randomize market conditions
        self.market_conditions = {
            "demand_multiplier": self.rng.uniform(0.8, 1.5),
            "spot_availability": self.rng.uniform(0.5, 1.0),
            "failure_rate": self.rng.uniform(0.01, 0.05),
        }
    
    def request_quotes(
        self,
        decomposition: WorkloadDecomposition,
        target_providers: list[str],
    ) -> list[ProviderOffer]:
        """
        Request quotes from providers for a workload.
        
        Args:
            decomposition: The workload decomposition
            target_providers: List of provider IDs to request from
            
        Returns:
            List of provider offers
        """
        offers = []
        
        for provider in self.providers:
            if target_providers and provider.id not in target_providers:
                continue
            
            if not provider.active:
                continue
            
            # Check capacity
            if provider.capacity.utilization_percent > 95:
                continue
            
            # Generate offer
            offer = self._generate_offer(provider, decomposition)
            offers.append(offer)
            self._offer_cache[offer.id] = offer
        
        return offers
    
    def _generate_offer(
        self,
        provider: ProviderProfile,
        decomposition: WorkloadDecomposition,
    ) -> ProviderOffer:
        """Generate an offer from a provider."""
        # Base pricing
        base_cost = 0.0
        resource_allocation: dict[ResourceType, int] = {}
        
        for stage in decomposition.stages:
            for res_type in stage.required_resource_types:
                if res_type == ResourceType.GPU:
                    hours = stage.estimated_duration_hours
                    cost = hours * provider.pricing.base_gpu_hour_usd
                    resource_allocation[res_type] = resource_allocation.get(res_type, 0) + 1
                elif res_type == ResourceType.CPU:
                    hours = stage.estimated_duration_hours
                    cost = hours * provider.pricing.base_cpu_hour_usd
                    resource_allocation[res_type] = resource_allocation.get(res_type, 0) + 4
                elif res_type == ResourceType.NPU:
                    hours = stage.estimated_duration_hours
                    cost = hours * provider.pricing.base_npu_hour_usd
                    resource_allocation[res_type] = resource_allocation.get(res_type, 0) + 1
                else:
                    cost = 0
                
                base_cost += cost
        
        # Apply market conditions
        adjusted_cost = base_cost * self.market_conditions["demand_multiplier"]
        
        # Apply provider's negotiation style variance
        style_variance = {
            NegotiationStrategy.AGGRESSIVE: self.rng.uniform(1.1, 1.3),
            NegotiationStrategy.DEFENSIVE: self.rng.uniform(0.95, 1.05),
            NegotiationStrategy.GREEDY: self.rng.uniform(1.2, 1.5),
            NegotiationStrategy.COOPERATIVE: self.rng.uniform(0.9, 1.0),
            NegotiationStrategy.BLUFFING: self.rng.uniform(1.0, 1.4),
            NegotiationStrategy.BALANCED: self.rng.uniform(0.95, 1.15),
        }
        
        final_cost = adjusted_cost * style_variance.get(
            provider.negotiation_style,
            1.0
        )
        
        # Spot pricing
        is_spot = self.rng.random() < self.market_conditions["spot_availability"]
        if is_spot:
            final_cost *= (1 - provider.pricing.spot_discount_percent / 100)
        
        # Duration estimate with variance
        base_duration = decomposition.total_estimated_hours
        duration_variance = self.rng.uniform(0.9, 1.2)
        estimated_duration = base_duration * duration_variance
        
        # Carbon footprint
        carbon = final_cost * 0.1 * (1 - provider.renewable_energy_percent / 100)
        
        return ProviderOffer(
            provider_id=provider.id,
            provider_name=provider.name,
            workload_id=decomposition.workload_id,
            stage_ids=[s.id for s in decomposition.stages],
            quoted_price_usd=round(final_cost, 2),
            quoted_duration_hours=round(estimated_duration, 2),
            resource_allocation=resource_allocation,
            is_spot=is_spot,
            valid_until=datetime.utcnow() + timedelta(hours=1),
            reliability_estimate=provider.reliability_score * self.rng.uniform(0.95, 1.0),
            carbon_footprint_kg=round(carbon, 2),
            terms={
                "min_commitment": provider.pricing.min_commitment_hours,
                "cancellation_penalty": 0.1 if is_spot else 0.25,
            },
        )
    
    def process_counter_offer(
        self,
        offer_id: str,
        counter_price: float,
        counter_terms: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process a counter-offer from the agent.
        
        Args:
            offer_id: ID of the original offer
            counter_price: Proposed counter price
            counter_terms: Additional counter terms
            
        Returns:
            Response dict with acceptance status and potentially new offer
        """
        original = self._offer_cache.get(offer_id)
        if original is None:
            return {"accepted": False, "error": "Offer not found"}
        
        provider = next(
            (p for p in self.providers if p.id == original.provider_id),
            None
        )
        if provider is None:
            return {"accepted": False, "error": "Provider not found"}
        
        # Calculate acceptance probability
        price_ratio = counter_price / original.quoted_price_usd
        flexibility = provider.negotiation_flexibility
        
        # Provider's minimum acceptable price
        min_acceptable = original.quoted_price_usd * (1 - flexibility)
        
        if counter_price >= min_acceptable:
            # Accept with some probability based on how good the offer is
            accept_prob = min(1.0, price_ratio * 0.8 + flexibility)
            
            if self.rng.random() < accept_prob:
                new_offer = ProviderOffer(
                    provider_id=original.provider_id,
                    provider_name=original.provider_name,
                    workload_id=original.workload_id,
                    stage_ids=original.stage_ids,
                    quoted_price_usd=counter_price,
                    quoted_duration_hours=original.quoted_duration_hours,
                    resource_allocation=original.resource_allocation,
                    is_spot=original.is_spot,
                    valid_until=datetime.utcnow() + timedelta(hours=1),
                    reliability_estimate=original.reliability_estimate,
                    carbon_footprint_kg=original.carbon_footprint_kg,
                    terms=original.terms,
                    negotiation_round=original.negotiation_round + 1,
                )
                self._offer_cache[new_offer.id] = new_offer
                return {"accepted": True, "offer": new_offer.model_dump()}
        
        # Provider makes counter-counter-offer
        counter_counter = original.quoted_price_usd * (1 - flexibility * 0.5)
        
        return {
            "accepted": False,
            "counter_offer": round(counter_counter, 2),
            "message": f"Provider counters at ${counter_counter:.2f}",
        }
    
    def simulate_execution(
        self,
        plan: ExecutionPlan,
        decomposition: WorkloadDecomposition,
    ) -> ExecutionState:
        """
        Simulate execution of a plan.
        
        Args:
            plan: The execution plan
            decomposition: The workload decomposition
            
        Returns:
            Execution state with simulated results
        """
        stages: list[ExecutionStageStatus] = []
        total_actual_cost = 0.0
        total_actual_duration = 0.0
        any_failed = False
        
        for allocation in plan.allocations:
            # Simulate variance in actual vs predicted
            cost_variance = self.rng.uniform(0.85, 1.2)
            duration_variance = self.rng.uniform(0.9, 1.3)
            
            actual_cost = allocation.estimated_cost_usd * cost_variance
            actual_duration = allocation.estimated_duration_hours * duration_variance
            
            # Check for failures
            failed = self.rng.random() < self.market_conditions["failure_rate"]
            
            if failed:
                any_failed = True
                status = "failed"
                error = "Simulated execution failure"
            else:
                status = "completed"
                error = None
            
            stage_status = ExecutionStageStatus(
                stage_id=allocation.stage_id,
                status=status,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow() + timedelta(hours=actual_duration),
                actual_cost_usd=round(actual_cost, 2),
                actual_duration_hours=round(actual_duration, 2),
                utilization_percent=self.rng.uniform(70, 95),
                error_message=error,
            )
            stages.append(stage_status)
            
            total_actual_cost += actual_cost
            total_actual_duration = max(total_actual_duration, actual_duration)
        
        return ExecutionState(
            plan_id=plan.id,
            workload_id=plan.workload_id,
            status="failed" if any_failed else "completed",
            stages=stages,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() + timedelta(hours=total_actual_duration),
            actual_total_cost_usd=round(total_actual_cost, 2),
            actual_total_duration_hours=round(total_actual_duration, 2),
            predicted_cost_usd=plan.total_cost_usd,
            predicted_duration_hours=plan.total_duration_hours,
            prediction_error_cost=round(
                abs(total_actual_cost - plan.total_cost_usd) / plan.total_cost_usd,
                3
            ),
            prediction_error_duration=round(
                abs(total_actual_duration - plan.total_duration_hours) / plan.total_duration_hours,
                3
            ),
        )

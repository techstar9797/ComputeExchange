"""
Planning Agent

Generates optimized execution plans by mapping workload stages to providers.
Supports multiple optimization strategies: cheapest, fastest, balanced, greenest.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from uuid import uuid4
import importlib.util

_models_path = Path(__file__).parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_models", _models_path)
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)

WorkloadSpec = _models.WorkloadSpec
WorkloadDecomposition = _models.WorkloadDecomposition
TaskStage = _models.TaskStage
ProviderProfile = _models.ProviderProfile
ProviderOffer = _models.ProviderOffer
ExecutionPlan = _models.ExecutionPlan
ResourceAllocation = _models.ResourceAllocation
ResourceType = _models.ResourceType
PlanStatus = _models.PlanStatus


@dataclass
class PlanCandidate:
    """A candidate execution plan with scoring."""
    plan: ExecutionPlan
    strategy: str
    score: float
    pros: list[str]
    cons: list[str]
    risk_factors: list[str]


class PlanningAgent:
    """
    Agent responsible for generating execution plans.
    
    Takes workload decomposition and provider offers to create:
    - Cheapest plan (minimize cost)
    - Fastest plan (minimize duration)
    - Balanced plan (optimize for cost-performance)
    - Greenest plan (minimize carbon footprint)
    """
    
    def __init__(self):
        self.plan_cache: dict[str, list[PlanCandidate]] = {}
    
    def generate_plans(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        providers: list[ProviderProfile],
    ) -> list[PlanCandidate]:
        """
        Generate multiple execution plans with different optimization objectives.
        """
        if not offers or not decomposition.stages:
            return []
        
        plans = []
        
        cheapest = self._generate_cheapest_plan(workload, decomposition, offers, providers)
        if cheapest:
            plans.append(cheapest)
        
        fastest = self._generate_fastest_plan(workload, decomposition, offers, providers)
        if fastest:
            plans.append(fastest)
        
        balanced = self._generate_balanced_plan(workload, decomposition, offers, providers)
        if balanced:
            plans.append(balanced)
        
        greenest = self._generate_greenest_plan(workload, decomposition, offers, providers)
        if greenest:
            plans.append(greenest)
        
        plans.sort(key=lambda p: p.score, reverse=True)
        
        self.plan_cache[workload.id] = plans
        return plans

    def _generate_cheapest_plan(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        providers: list[ProviderProfile],
    ) -> Optional[PlanCandidate]:
        """Generate plan optimizing for lowest cost."""
        allocations = []
        total_cost = 0.0
        total_duration = 0.0
        
        sorted_offers = sorted(offers, key=lambda o: o.total_cost_usd)
        
        for stage in decomposition.stages:
            best_offer = self._find_cheapest_offer_for_stage(stage, sorted_offers, providers)
            
            if best_offer:
                allocation = ResourceAllocation(
                    stage_id=stage.id,
                    provider_id=best_offer.provider_id,
                    resource_type=stage.required_resource_types[0] if stage.required_resource_types else ResourceType.CPU,
                    quantity=best_offer.gpu_count or best_offer.cpu_count or 1,
                    duration_hours=stage.estimated_duration_hours or 1.0,
                    cost_usd=self._calculate_stage_cost(stage, best_offer),
                    is_spot=best_offer.is_spot,
                    region=best_offer.region,
                )
                allocations.append(allocation)
                total_cost += allocation.cost_usd
                total_duration += allocation.duration_hours
        
        if not allocations:
            return None
        
        plan = ExecutionPlan(
            name="Cheapest Plan",
            workload_id=workload.id,
            allocations=allocations,
            total_cost_usd=total_cost,
            total_duration_hours=total_duration,
            estimated_reliability=0.90,
            carbon_footprint_kg=total_cost * 0.05,
            status=PlanStatus.DRAFT,
        )
        
        score = self._score_plan(plan, workload, strategy="cheapest")
        
        pros = [
            f"Lowest cost at ${total_cost:.2f}",
            f"Within budget by ${workload.budget_usd - total_cost:.2f}" if total_cost <= workload.budget_usd else "May exceed budget",
        ]
        
        cons = []
        if total_duration > workload.deadline_hours * 0.9:
            cons.append("Cutting it close on deadline")
        if any(a.is_spot for a in allocations):
            cons.append("Uses spot instances - potential interruptions")
        
        risks = []
        spot_count = sum(1 for a in allocations if a.is_spot)
        if spot_count > 0:
            risks.append(f"{spot_count} stages use spot instances")
        
        return PlanCandidate(
            plan=plan,
            strategy="cheapest",
            score=score,
            pros=pros,
            cons=cons,
            risk_factors=risks,
        )

    def _generate_fastest_plan(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        providers: list[ProviderProfile],
    ) -> Optional[PlanCandidate]:
        """Generate plan optimizing for fastest completion."""
        allocations = []
        total_cost = 0.0
        total_duration = 0.0
        
        for stage in decomposition.stages:
            best_offer = self._find_fastest_offer_for_stage(stage, offers, providers)
            
            if best_offer:
                provider = next((p for p in providers if p.id == best_offer.provider_id), None)
                speed_factor = 0.7 if provider and provider.reliability_score > 0.95 else 0.85
                
                allocation = ResourceAllocation(
                    stage_id=stage.id,
                    provider_id=best_offer.provider_id,
                    resource_type=stage.required_resource_types[0] if stage.required_resource_types else ResourceType.GPU,
                    quantity=max(best_offer.gpu_count or 1, best_offer.cpu_count or 1),
                    duration_hours=(stage.estimated_duration_hours or 1.0) * speed_factor,
                    cost_usd=self._calculate_stage_cost(stage, best_offer) * 1.3,
                    is_spot=False,
                    region=best_offer.region,
                )
                allocations.append(allocation)
                total_cost += allocation.cost_usd
                total_duration += allocation.duration_hours
        
        if not allocations:
            return None
        
        plan = ExecutionPlan(
            name="Fastest Plan",
            workload_id=workload.id,
            allocations=allocations,
            total_cost_usd=total_cost,
            total_duration_hours=total_duration,
            estimated_reliability=0.96,
            carbon_footprint_kg=total_cost * 0.08,
            status=PlanStatus.DRAFT,
        )
        
        score = self._score_plan(plan, workload, strategy="fastest")
        
        time_savings = workload.deadline_hours - total_duration
        pros = [
            f"Fastest completion at {total_duration:.1f} hours",
            f"Time to spare: {time_savings:.1f} hours" if time_savings > 0 else "Meets deadline",
            "Uses premium/dedicated instances for reliability",
        ]
        
        cons = [
            f"Higher cost at ${total_cost:.2f}",
        ]
        if total_cost > workload.budget_usd:
            cons.append(f"Exceeds budget by ${total_cost - workload.budget_usd:.2f}")
        
        return PlanCandidate(
            plan=plan,
            strategy="fastest",
            score=score,
            pros=pros,
            cons=cons,
            risk_factors=["Premium pricing"],
        )

    def _generate_balanced_plan(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        providers: list[ProviderProfile],
    ) -> Optional[PlanCandidate]:
        """Generate plan balancing cost and performance."""
        allocations = []
        total_cost = 0.0
        total_duration = 0.0
        
        weights = workload.optimization_weights
        
        def score_offer(offer: ProviderOffer, stage: TaskStage) -> float:
            provider = next((p for p in providers if p.id == offer.provider_id), None)
            
            cost_score = 1.0 - min(offer.total_cost_usd / (workload.budget_usd / len(decomposition.stages)), 1.0)
            reliability_score = provider.reliability_score if provider else 0.9
            latency_score = 1.0 - min((provider.avg_latency_ms if provider else 50) / 100, 1.0)
            
            return (
                weights.cost * cost_score +
                weights.reliability * reliability_score +
                weights.latency * latency_score
            )
        
        for stage in decomposition.stages:
            best_offer = None
            best_score = -1
            
            for offer in offers:
                if self._offer_compatible_with_stage(offer, stage, providers):
                    offer_score = score_offer(offer, stage)
                    if offer_score > best_score:
                        best_score = offer_score
                        best_offer = offer
            
            if best_offer:
                allocation = ResourceAllocation(
                    stage_id=stage.id,
                    provider_id=best_offer.provider_id,
                    resource_type=stage.required_resource_types[0] if stage.required_resource_types else ResourceType.GPU,
                    quantity=best_offer.gpu_count or best_offer.cpu_count or 1,
                    duration_hours=stage.estimated_duration_hours or 1.0,
                    cost_usd=self._calculate_stage_cost(stage, best_offer),
                    is_spot=best_offer.is_spot and workload.allow_spot_instances,
                    region=best_offer.region,
                )
                allocations.append(allocation)
                total_cost += allocation.cost_usd
                total_duration += allocation.duration_hours
        
        if not allocations:
            return None
        
        avg_reliability = sum(
            next((p.reliability_score for p in providers if p.id == a.provider_id), 0.9)
            for a in allocations
        ) / len(allocations)
        
        plan = ExecutionPlan(
            name="Balanced Plan",
            workload_id=workload.id,
            allocations=allocations,
            total_cost_usd=total_cost,
            total_duration_hours=total_duration,
            estimated_reliability=avg_reliability,
            carbon_footprint_kg=total_cost * 0.06,
            status=PlanStatus.DRAFT,
        )
        
        score = self._score_plan(plan, workload, strategy="balanced")
        
        pros = [
            f"Optimized for your priorities (cost: {weights.cost:.0%}, reliability: {weights.reliability:.0%})",
            f"Cost: ${total_cost:.2f} | Duration: {total_duration:.1f}h",
            f"Reliability score: {avg_reliability:.1%}",
        ]
        
        cons = []
        if total_cost > workload.budget_usd * 0.9:
            cons.append("Near budget limit")
        if total_duration > workload.deadline_hours * 0.8:
            cons.append("Limited schedule buffer")
        
        return PlanCandidate(
            plan=plan,
            strategy="balanced",
            score=score,
            pros=pros,
            cons=cons,
            risk_factors=[],
        )

    def _generate_greenest_plan(
        self,
        workload: WorkloadSpec,
        decomposition: WorkloadDecomposition,
        offers: list[ProviderOffer],
        providers: list[ProviderProfile],
    ) -> Optional[PlanCandidate]:
        """Generate plan optimizing for lowest carbon footprint."""
        allocations = []
        total_cost = 0.0
        total_duration = 0.0
        total_carbon = 0.0
        
        green_providers = sorted(
            [p for p in providers if p.renewable_energy_percent > 50],
            key=lambda p: p.carbon_intensity_gco2_kwh
        )
        
        if not green_providers:
            green_providers = sorted(providers, key=lambda p: p.carbon_intensity_gco2_kwh)
        
        for stage in decomposition.stages:
            best_offer = None
            best_carbon = float('inf')
            
            for provider in green_providers:
                matching_offers = [o for o in offers if o.provider_id == provider.id]
                for offer in matching_offers:
                    if self._offer_compatible_with_stage(offer, stage, providers):
                        stage_carbon = provider.carbon_intensity_gco2_kwh * (stage.estimated_duration_hours or 1.0) * 0.5
                        if stage_carbon < best_carbon:
                            best_carbon = stage_carbon
                            best_offer = offer
            
            if not best_offer and offers:
                best_offer = offers[0]
                best_carbon = 100
            
            if best_offer:
                allocation = ResourceAllocation(
                    stage_id=stage.id,
                    provider_id=best_offer.provider_id,
                    resource_type=stage.required_resource_types[0] if stage.required_resource_types else ResourceType.CPU,
                    quantity=best_offer.gpu_count or best_offer.cpu_count or 1,
                    duration_hours=(stage.estimated_duration_hours or 1.0) * 1.1,
                    cost_usd=self._calculate_stage_cost(stage, best_offer) * 1.15,
                    is_spot=False,
                    region=best_offer.region,
                )
                allocations.append(allocation)
                total_cost += allocation.cost_usd
                total_duration += allocation.duration_hours
                total_carbon += best_carbon / 1000
        
        if not allocations:
            return None
        
        plan = ExecutionPlan(
            name="Greenest Plan",
            workload_id=workload.id,
            allocations=allocations,
            total_cost_usd=total_cost,
            total_duration_hours=total_duration,
            estimated_reliability=0.93,
            carbon_footprint_kg=total_carbon,
            status=PlanStatus.DRAFT,
        )
        
        score = self._score_plan(plan, workload, strategy="greenest")
        
        pros = [
            f"Lowest carbon footprint: {total_carbon:.2f} kg CO2",
            "Uses renewable energy providers where available",
            "Supports sustainability goals",
        ]
        
        cons = [
            f"Cost: ${total_cost:.2f} (may be higher than cheapest)",
            f"Duration: {total_duration:.1f}h (may be slower)",
        ]
        
        return PlanCandidate(
            plan=plan,
            strategy="greenest",
            score=score,
            pros=pros,
            cons=cons,
            risk_factors=["Limited provider options in some regions"],
        )

    def _find_cheapest_offer_for_stage(
        self, stage: TaskStage, offers: list[ProviderOffer], providers: list[ProviderProfile]
    ) -> Optional[ProviderOffer]:
        """Find the cheapest compatible offer for a stage."""
        compatible = [o for o in offers if self._offer_compatible_with_stage(o, stage, providers)]
        if not compatible:
            return offers[0] if offers else None
        return min(compatible, key=lambda o: o.total_cost_usd)

    def _find_fastest_offer_for_stage(
        self, stage: TaskStage, offers: list[ProviderOffer], providers: list[ProviderProfile]
    ) -> Optional[ProviderOffer]:
        """Find the fastest compatible offer for a stage."""
        compatible = [o for o in offers if self._offer_compatible_with_stage(o, stage, providers)]
        if not compatible:
            return offers[0] if offers else None
        
        def speed_score(offer: ProviderOffer) -> float:
            provider = next((p for p in providers if p.id == offer.provider_id), None)
            gpu_count = offer.gpu_count or 1
            reliability = provider.reliability_score if provider else 0.9
            return gpu_count * reliability
        
        return max(compatible, key=speed_score)

    def _offer_compatible_with_stage(
        self, offer: ProviderOffer, stage: TaskStage, providers: list[ProviderProfile]
    ) -> bool:
        """Check if an offer is compatible with a stage's requirements."""
        if ResourceType.GPU in stage.required_resource_types:
            if not offer.gpu_count or offer.gpu_count == 0:
                return False
        
        if stage.estimated_memory_gb and offer.gpu_memory_gb:
            if offer.gpu_memory_gb < stage.estimated_memory_gb * 0.5:
                return False
        
        return True

    def _calculate_stage_cost(self, stage: TaskStage, offer: ProviderOffer) -> float:
        """Calculate cost for executing a stage with a given offer."""
        duration = stage.estimated_duration_hours or 1.0
        gpu_cost = (offer.gpu_hour_usd or 0) * (offer.gpu_count or 0) * duration
        cpu_cost = (offer.cpu_hour_usd or 0) * (offer.cpu_count or 0) * duration * 0.1
        return gpu_cost + cpu_cost + 1.0

    def _score_plan(self, plan: ExecutionPlan, workload: WorkloadSpec, strategy: str) -> float:
        """Score a plan based on how well it meets objectives."""
        score = 0.0
        weights = workload.optimization_weights
        
        cost_ratio = plan.total_cost_usd / workload.budget_usd if workload.budget_usd > 0 else 1.0
        cost_score = max(0, 1.0 - cost_ratio)
        
        time_ratio = plan.total_duration_hours / workload.deadline_hours if workload.deadline_hours > 0 else 1.0
        time_score = max(0, 1.0 - time_ratio)
        
        reliability_score = plan.estimated_reliability
        
        if strategy == "cheapest":
            score = 0.6 * cost_score + 0.2 * time_score + 0.2 * reliability_score
        elif strategy == "fastest":
            score = 0.2 * cost_score + 0.6 * time_score + 0.2 * reliability_score
        elif strategy == "balanced":
            score = (
                weights.cost * cost_score +
                weights.latency * time_score +
                weights.reliability * reliability_score +
                weights.throughput * 0.5 +
                weights.energy * 0.5
            )
        elif strategy == "greenest":
            carbon_score = max(0, 1.0 - plan.carbon_footprint_kg / 100)
            score = 0.3 * cost_score + 0.2 * time_score + 0.5 * carbon_score
        
        return round(score, 4)

    def compare_plans(self, plans: list[PlanCandidate], workload: WorkloadSpec) -> dict:
        """Generate comparison data for all plans."""
        if not plans:
            return {}
        
        return {
            "plans": [
                {
                    "name": p.plan.name,
                    "strategy": p.strategy,
                    "cost": p.plan.total_cost_usd,
                    "duration": p.plan.total_duration_hours,
                    "reliability": p.plan.estimated_reliability,
                    "carbon": p.plan.carbon_footprint_kg,
                    "score": p.score,
                    "pros": p.pros,
                    "cons": p.cons,
                    "risks": p.risk_factors,
                }
                for p in plans
            ],
            "recommendation": plans[0].strategy if plans else None,
            "budget_comparison": {
                "budget": workload.budget_usd,
                "cheapest": min(p.plan.total_cost_usd for p in plans) if plans else 0,
                "most_expensive": max(p.plan.total_cost_usd for p in plans) if plans else 0,
            },
            "time_comparison": {
                "deadline": workload.deadline_hours,
                "fastest": min(p.plan.total_duration_hours for p in plans) if plans else 0,
                "slowest": max(p.plan.total_duration_hours for p in plans) if plans else 0,
            },
        }

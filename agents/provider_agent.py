"""
Provider Agents

Autonomous provider-side agents that respond to negotiation requests.
Each provider can have a distinct negotiation personality and pricing strategy.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from uuid import uuid4
import random
import importlib.util

_models_path = Path(__file__).parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_models", _models_path)
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)

NegotiationStrategy = _models.NegotiationStrategy
NegotiationMessage = _models.NegotiationMessage
ProviderOffer = _models.ProviderOffer
ProviderProfile = _models.ProviderProfile
ResourceType = _models.ResourceType
WorkloadDecomposition = _models.WorkloadDecomposition


@dataclass
class ProviderState:
    """Internal state of a provider agent."""
    current_utilization: float = 0.5
    recent_deals: list[dict] = field(default_factory=list)
    negotiation_fatigue: float = 0.0
    market_position: str = "neutral"


class ProviderAgent:
    """
    Autonomous provider agent that negotiates on behalf of a compute provider.
    
    Behaviors adapt based on:
    - Current capacity utilization
    - Market conditions
    - Negotiation history
    - Provider's strategic personality
    """
    
    PERSONALITY_TRAITS = {
        NegotiationStrategy.AGGRESSIVE: {
            "initial_markup": 1.3,
            "min_margin": 0.15,
            "concession_rate": 0.05,
            "patience": 2,
            "bluff_probability": 0.3,
        },
        NegotiationStrategy.DEFENSIVE: {
            "initial_markup": 1.05,
            "min_margin": 0.02,
            "concession_rate": 0.15,
            "patience": 6,
            "bluff_probability": 0.0,
        },
        NegotiationStrategy.GREEDY: {
            "initial_markup": 1.5,
            "min_margin": 0.25,
            "concession_rate": 0.03,
            "patience": 3,
            "bluff_probability": 0.4,
        },
        NegotiationStrategy.COOPERATIVE: {
            "initial_markup": 1.1,
            "min_margin": 0.05,
            "concession_rate": 0.20,
            "patience": 8,
            "bluff_probability": 0.0,
        },
        NegotiationStrategy.BLUFFING: {
            "initial_markup": 1.4,
            "min_margin": 0.10,
            "concession_rate": 0.10,
            "patience": 4,
            "bluff_probability": 0.6,
        },
        NegotiationStrategy.BALANCED: {
            "initial_markup": 1.2,
            "min_margin": 0.08,
            "concession_rate": 0.12,
            "patience": 5,
            "bluff_probability": 0.15,
        },
    }
    
    def __init__(
        self,
        profile: ProviderProfile,
        seed: Optional[int] = None,
    ):
        self.profile = profile
        self.personality = profile.negotiation_style
        self.traits = self.PERSONALITY_TRAITS.get(
            self.personality, 
            self.PERSONALITY_TRAITS[NegotiationStrategy.BALANCED]
        )
        self.state = ProviderState(
            current_utilization=profile.capacity.utilization_percent / 100.0
        )
        self.rng = random.Random(seed)
        self._offer_floor: dict[str, float] = {}
    
    def generate_initial_offer(
        self,
        decomposition: WorkloadDecomposition,
        market_demand: float = 1.0,
    ) -> ProviderOffer:
        """
        Generate an initial offer for a workload.
        
        Args:
            decomposition: The workload decomposition
            market_demand: Current market demand multiplier (1.0 = normal)
        """
        base_cost = self._calculate_base_cost(decomposition)
        
        utilization_factor = 1.0 + (self.state.current_utilization - 0.5) * 0.5
        demand_factor = market_demand
        personality_markup = self.traits["initial_markup"]
        
        noise = self.rng.uniform(0.95, 1.05)
        
        final_price = base_cost * utilization_factor * demand_factor * personality_markup * noise
        
        self._offer_floor[decomposition.workload_id] = base_cost * (1 + self.traits["min_margin"])
        
        duration_variance = self.rng.uniform(0.9, 1.15)
        estimated_duration = decomposition.total_estimated_hours * duration_variance
        
        is_spot = (
            self.state.current_utilization < 0.6 and 
            self.rng.random() > 0.3
        )
        if is_spot:
            final_price *= (1 - self.profile.pricing.spot_discount_percent / 100)
        
        resource_alloc = self._determine_resource_allocation(decomposition)
        
        return ProviderOffer(
            provider_id=self.profile.id,
            provider_name=self.profile.name,
            workload_id=decomposition.workload_id,
            stage_ids=[s.id for s in decomposition.stages],
            quoted_price_usd=round(final_price, 2),
            quoted_duration_hours=round(estimated_duration, 2),
            resource_allocation=resource_alloc,
            is_spot=is_spot,
            valid_until=datetime.utcnow() + timedelta(hours=2),
            reliability_estimate=self.profile.reliability_score * self.rng.uniform(0.97, 1.0),
            carbon_footprint_kg=round(final_price * 0.08 * (1 - self.profile.renewable_energy_percent/100), 2),
            terms={
                "min_commitment": self.profile.pricing.min_commitment_hours,
                "cancellation_fee": 0.1 if is_spot else 0.2,
                "volume_discount": self._get_volume_discount(),
            },
        )
    
    def respond_to_counter_offer(
        self,
        original_offer: ProviderOffer,
        counter_price: float,
        round_number: int,
    ) -> tuple[str, Optional[ProviderOffer]]:
        """
        Respond to a counter-offer from the buyer agent.
        
        Returns:
            Tuple of (response_type, new_offer)
            response_type: "accept", "counter", "reject"
        """
        floor_price = self._offer_floor.get(
            original_offer.workload_id, 
            original_offer.quoted_price_usd * 0.7
        )
        
        if counter_price >= original_offer.quoted_price_usd * 0.98:
            return "accept", self._create_accepted_offer(original_offer, counter_price)
        
        if round_number > self.traits["patience"]:
            if counter_price >= floor_price:
                return "accept", self._create_accepted_offer(original_offer, counter_price)
            return "reject", None
        
        if counter_price < floor_price * 0.8:
            return "reject", None
        
        if counter_price >= floor_price:
            accept_prob = (counter_price - floor_price) / (original_offer.quoted_price_usd - floor_price)
            accept_prob = min(accept_prob * (1 + round_number * 0.1), 0.9)
            
            if self.rng.random() < accept_prob:
                return "accept", self._create_accepted_offer(original_offer, counter_price)
        
        concession = self.traits["concession_rate"] * (1 + round_number * 0.05)
        new_price = original_offer.quoted_price_usd * (1 - concession)
        new_price = max(new_price, floor_price)
        
        if abs(new_price - counter_price) < original_offer.quoted_price_usd * 0.02:
            final_price = (new_price + counter_price) / 2
            return "accept", self._create_accepted_offer(original_offer, final_price)
        
        counter_offer = self._create_counter_offer(original_offer, new_price, round_number)
        return "counter", counter_offer
    
    def generate_negotiation_message(
        self,
        response_type: str,
        original_price: float,
        new_price: Optional[float],
        round_number: int,
    ) -> NegotiationMessage:
        """Generate a human-readable negotiation message."""
        if response_type == "accept":
            content = f"Deal! We accept ${new_price:.2f}. Looking forward to working together."
        elif response_type == "reject":
            content = f"Unfortunately, we cannot go below our floor price. Our best offer was ${original_price:.2f}."
        else:
            if self.personality == NegotiationStrategy.AGGRESSIVE:
                content = f"Our pricing is firm. We can do ${new_price:.2f}, final offer."
            elif self.personality == NegotiationStrategy.COOPERATIVE:
                content = f"We want to make this work. How about ${new_price:.2f}?"
            elif self.personality == NegotiationStrategy.GREEDY:
                content = f"Given current demand, ${new_price:.2f} is very competitive."
            else:
                content = f"We can adjust to ${new_price:.2f}. Let us know."
        
        return NegotiationMessage(
            sender=self.profile.id,
            recipient="buyer_agent",
            message_type=response_type,
            content=content,
            proposed_price_usd=new_price or original_price,
        )
    
    def _calculate_base_cost(self, decomposition: WorkloadDecomposition) -> float:
        """Calculate the base cost (provider's cost) for a workload."""
        cost = 0.0
        
        for stage in decomposition.stages:
            duration = stage.estimated_duration_hours or 1.0
            
            if ResourceType.GPU in (stage.required_resource_types or []):
                cost += duration * self.profile.pricing.base_gpu_hour_usd
            elif ResourceType.NPU in (stage.required_resource_types or []):
                cost += duration * self.profile.pricing.base_npu_hour_usd
            else:
                cost += duration * self.profile.pricing.base_cpu_hour_usd
        
        return cost
    
    def _determine_resource_allocation(
        self, 
        decomposition: WorkloadDecomposition,
    ) -> dict[ResourceType, int]:
        """Determine resource allocation for the workload."""
        allocation: dict[ResourceType, int] = {}
        
        for stage in decomposition.stages:
            for res_type in (stage.required_resource_types or []):
                if res_type == ResourceType.GPU:
                    allocation[res_type] = max(allocation.get(res_type, 0), 4)
                elif res_type == ResourceType.CPU:
                    allocation[res_type] = max(allocation.get(res_type, 0), 16)
                elif res_type == ResourceType.MEMORY:
                    allocation[res_type] = max(allocation.get(res_type, 0), 64)
                elif res_type == ResourceType.NPU:
                    allocation[res_type] = max(allocation.get(res_type, 0), 2)
        
        return allocation
    
    def _get_volume_discount(self) -> float:
        """Calculate volume discount based on recent deal history."""
        recent_count = len(self.state.recent_deals)
        if recent_count >= 5:
            return 0.10
        elif recent_count >= 2:
            return 0.05
        return 0.0
    
    def _create_accepted_offer(
        self,
        original: ProviderOffer,
        accepted_price: float,
    ) -> ProviderOffer:
        """Create an accepted offer at the negotiated price."""
        return ProviderOffer(
            provider_id=original.provider_id,
            provider_name=original.provider_name,
            workload_id=original.workload_id,
            stage_ids=original.stage_ids,
            quoted_price_usd=round(accepted_price, 2),
            quoted_duration_hours=original.quoted_duration_hours,
            resource_allocation=original.resource_allocation,
            is_spot=original.is_spot,
            valid_until=datetime.utcnow() + timedelta(hours=24),
            reliability_estimate=original.reliability_estimate,
            carbon_footprint_kg=original.carbon_footprint_kg,
            terms=original.terms,
            negotiation_round=original.negotiation_round + 1,
        )
    
    def _create_counter_offer(
        self,
        original: ProviderOffer,
        new_price: float,
        round_number: int,
    ) -> ProviderOffer:
        """Create a counter-offer."""
        return ProviderOffer(
            provider_id=original.provider_id,
            provider_name=original.provider_name,
            workload_id=original.workload_id,
            stage_ids=original.stage_ids,
            quoted_price_usd=round(new_price, 2),
            quoted_duration_hours=original.quoted_duration_hours,
            resource_allocation=original.resource_allocation,
            is_spot=original.is_spot,
            valid_until=datetime.utcnow() + timedelta(hours=1),
            reliability_estimate=original.reliability_estimate,
            carbon_footprint_kg=original.carbon_footprint_kg,
            terms=original.terms,
            negotiation_round=round_number + 1,
        )
    
    def update_state(self, deal_completed: bool, deal_value: Optional[float] = None):
        """Update provider state after a negotiation."""
        if deal_completed and deal_value:
            self.state.recent_deals.append({
                "value": deal_value,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.state.current_utilization = min(
                self.state.current_utilization + 0.05, 
                0.95
            )
        
        self.state.negotiation_fatigue = max(
            0, 
            self.state.negotiation_fatigue - 0.1
        )


class ProviderMarketplace:
    """
    Manages multiple provider agents and coordinates negotiations.
    """
    
    def __init__(self, profiles: list[ProviderProfile], seed: Optional[int] = None):
        self.agents: dict[str, ProviderAgent] = {}
        self.rng = random.Random(seed)
        
        for profile in profiles:
            agent_seed = self.rng.randint(0, 2**31)
            self.agents[profile.id] = ProviderAgent(profile, seed=agent_seed)
    
    def request_all_quotes(
        self,
        decomposition: WorkloadDecomposition,
        market_demand: float = 1.0,
    ) -> list[ProviderOffer]:
        """Request quotes from all available providers."""
        offers = []
        
        for agent in self.agents.values():
            if agent.state.current_utilization < 0.95:
                offer = agent.generate_initial_offer(decomposition, market_demand)
                offers.append(offer)
        
        return offers
    
    def negotiate_with_provider(
        self,
        provider_id: str,
        original_offer: ProviderOffer,
        counter_price: float,
        round_number: int,
    ) -> tuple[str, Optional[ProviderOffer], NegotiationMessage]:
        """
        Conduct a negotiation round with a specific provider.
        """
        agent = self.agents.get(provider_id)
        if not agent:
            raise ValueError(f"Provider {provider_id} not found")
        
        response_type, new_offer = agent.respond_to_counter_offer(
            original_offer, counter_price, round_number
        )
        
        message = agent.generate_negotiation_message(
            response_type,
            original_offer.quoted_price_usd,
            new_offer.quoted_price_usd if new_offer else None,
            round_number,
        )
        
        return response_type, new_offer, message
    
    def get_market_summary(self) -> dict:
        """Get a summary of current market conditions."""
        utilizations = [a.state.current_utilization for a in self.agents.values()]
        
        return {
            "total_providers": len(self.agents),
            "avg_utilization": sum(utilizations) / len(utilizations) if utilizations else 0,
            "available_providers": sum(1 for u in utilizations if u < 0.9),
            "high_demand_providers": sum(1 for u in utilizations if u > 0.8),
        }

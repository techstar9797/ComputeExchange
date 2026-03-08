"""
Negotiation Agent

Handles price negotiation with compute providers.
Supports multiple negotiation strategies and tracks negotiation history.
"""

from dataclasses import dataclass
from datetime import datetime
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
NegotiationState = _models.NegotiationState
ProviderOffer = _models.ProviderOffer
ProviderProfile = _models.ProviderProfile
WorkloadDecomposition = _models.WorkloadDecomposition


@dataclass
class NegotiationResult:
    """Result of a negotiation round."""
    success: bool
    final_offer: Optional[ProviderOffer]
    discount_achieved: float
    rounds_taken: int
    messages: list[NegotiationMessage]


class NegotiationAgent:
    """
    Agent responsible for negotiating with compute providers.
    
    Strategies:
    - AGGRESSIVE: Push hard for discounts, risk losing deal
    - DEFENSIVE: Accept reasonable offers quickly
    - GREEDY: Always ask for more, may settle eventually
    - COOPERATIVE: Find win-win, build relationship
    - BLUFFING: Pretend to have better offers
    - BALANCED: Moderate approach based on market conditions
    """
    
    STRATEGY_PARAMS = {
        NegotiationStrategy.AGGRESSIVE: {
            "initial_discount_ask": 0.35,
            "min_acceptable_discount": 0.15,
            "concession_rate": 0.15,
            "walk_away_threshold": 0.10,
            "max_rounds": 5,
        },
        NegotiationStrategy.DEFENSIVE: {
            "initial_discount_ask": 0.10,
            "min_acceptable_discount": 0.05,
            "concession_rate": 0.30,
            "walk_away_threshold": 0.0,
            "max_rounds": 2,
        },
        NegotiationStrategy.GREEDY: {
            "initial_discount_ask": 0.50,
            "min_acceptable_discount": 0.20,
            "concession_rate": 0.10,
            "walk_away_threshold": 0.15,
            "max_rounds": 7,
        },
        NegotiationStrategy.COOPERATIVE: {
            "initial_discount_ask": 0.20,
            "min_acceptable_discount": 0.10,
            "concession_rate": 0.25,
            "walk_away_threshold": 0.05,
            "max_rounds": 4,
        },
        NegotiationStrategy.BLUFFING: {
            "initial_discount_ask": 0.40,
            "min_acceptable_discount": 0.15,
            "concession_rate": 0.20,
            "walk_away_threshold": 0.10,
            "max_rounds": 4,
        },
        NegotiationStrategy.BALANCED: {
            "initial_discount_ask": 0.25,
            "min_acceptable_discount": 0.10,
            "concession_rate": 0.20,
            "walk_away_threshold": 0.05,
            "max_rounds": 4,
        },
    }
    
    def __init__(self, strategy: NegotiationStrategy = NegotiationStrategy.BALANCED):
        self.strategy = strategy
        self.params = self.STRATEGY_PARAMS[strategy]
        self.negotiation_history: list[NegotiationState] = []
    
    def set_strategy(self, strategy: NegotiationStrategy):
        """Change negotiation strategy."""
        self.strategy = strategy
        self.params = self.STRATEGY_PARAMS[strategy]
    
    def negotiate_with_provider(
        self,
        initial_offer: ProviderOffer,
        provider: ProviderProfile,
        decomposition: WorkloadDecomposition,
    ) -> NegotiationResult:
        """
        Conduct a negotiation session with a provider.
        
        Returns the final negotiation result with achieved discount.
        """
        messages = []
        current_offer = initial_offer
        current_ask = self.params["initial_discount_ask"]
        
        for round_num in range(1, self.params["max_rounds"] + 1):
            our_message = self._generate_negotiation_message(
                round_num=round_num,
                current_ask=current_ask,
                provider=provider,
                offer=current_offer,
            )
            messages.append(our_message)
            
            provider_response, new_offer = self._simulate_provider_response(
                our_ask=current_ask,
                current_offer=current_offer,
                provider=provider,
                round_num=round_num,
            )
            messages.append(provider_response)
            
            if new_offer:
                achieved_discount = 1.0 - (new_offer.total_cost_usd / initial_offer.total_cost_usd)
                
                if achieved_discount >= self.params["min_acceptable_discount"]:
                    accept_message = NegotiationMessage(
                        sender="agent",
                        recipient=provider.id,
                        message_type="accept",
                        content=f"We accept the offer at ${new_offer.total_cost_usd:.2f}",
                        proposed_price_usd=new_offer.total_cost_usd,
                    )
                    messages.append(accept_message)
                    
                    state = NegotiationState(
                        provider_id=provider.id,
                        strategy=self.strategy,
                        rounds_completed=round_num,
                        current_best_offer=new_offer,
                        messages=messages,
                        status="accepted",
                    )
                    self.negotiation_history.append(state)
                    
                    return NegotiationResult(
                        success=True,
                        final_offer=new_offer,
                        discount_achieved=achieved_discount,
                        rounds_taken=round_num,
                        messages=messages,
                    )
                
                current_offer = new_offer
            
            current_ask = current_ask * (1 - self.params["concession_rate"])
            
            if current_ask < self.params["walk_away_threshold"]:
                break
        
        final_discount = 1.0 - (current_offer.total_cost_usd / initial_offer.total_cost_usd)
        
        if final_discount >= self.params["walk_away_threshold"]:
            return NegotiationResult(
                success=True,
                final_offer=current_offer,
                discount_achieved=final_discount,
                rounds_taken=len(messages) // 2,
                messages=messages,
            )
        
        return NegotiationResult(
            success=False,
            final_offer=None,
            discount_achieved=0.0,
            rounds_taken=len(messages) // 2,
            messages=messages,
        )
    
    def _generate_negotiation_message(
        self,
        round_num: int,
        current_ask: float,
        provider: ProviderProfile,
        offer: ProviderOffer,
    ) -> NegotiationMessage:
        """Generate a negotiation message based on strategy."""
        target_price = offer.total_cost_usd * (1 - current_ask)
        
        if self.strategy == NegotiationStrategy.AGGRESSIVE:
            if round_num == 1:
                content = f"We need a significant discount to proceed. Our target is ${target_price:.2f}."
            else:
                content = f"That's not competitive. We can get ${target_price:.2f} elsewhere."
        
        elif self.strategy == NegotiationStrategy.BLUFFING:
            content = f"We have a standing offer at ${target_price:.2f} from another provider. Can you match?"
        
        elif self.strategy == NegotiationStrategy.COOPERATIVE:
            content = f"We're looking for a long-term partnership. Would ${target_price:.2f} work if we commit to volume?"
        
        elif self.strategy == NegotiationStrategy.DEFENSIVE:
            content = f"Your offer looks good. Could you do ${target_price:.2f} to close the deal today?"
        
        elif self.strategy == NegotiationStrategy.GREEDY:
            content = f"We need at least ${target_price:.2f} per hour. This is non-negotiable."
        
        else:
            content = f"We'd like to discuss pricing. Our budget allows for ${target_price:.2f}."
        
        return NegotiationMessage(
            sender="agent",
            recipient=provider.id,
            message_type="counter_offer",
            content=content,
            proposed_price_usd=target_price,
        )
    
    def _simulate_provider_response(
        self,
        our_ask: float,
        current_offer: ProviderOffer,
        provider: ProviderProfile,
        round_num: int,
    ) -> tuple[NegotiationMessage, Optional[ProviderOffer]]:
        """Simulate provider's response to our negotiation."""
        flexibility = provider.negotiation_flexibility
        
        acceptable_discount = min(our_ask * 0.5, flexibility)
        
        rand_factor = random.uniform(0.8, 1.2)
        actual_discount = acceptable_discount * rand_factor
        
        if provider.negotiation_style == NegotiationStrategy.AGGRESSIVE:
            actual_discount *= 0.5
        elif provider.negotiation_style == NegotiationStrategy.COOPERATIVE:
            actual_discount *= 1.2
        
        actual_discount = max(0, min(actual_discount, flexibility))
        
        new_price = current_offer.total_cost_usd * (1 - actual_discount)
        
        if actual_discount < 0.02:
            content = f"Our pricing is already competitive. Best we can do is ${current_offer.total_cost_usd:.2f}."
            new_offer = None
        else:
            content = f"We can offer ${new_price:.2f}. This includes our best available rates."
            new_offer = ProviderOffer(
                provider_id=provider.id,
                provider_name=provider.name,
                gpu_count=current_offer.gpu_count,
                gpu_type=current_offer.gpu_type,
                gpu_memory_gb=current_offer.gpu_memory_gb,
                cpu_count=current_offer.cpu_count,
                memory_gb=current_offer.memory_gb,
                storage_tb=current_offer.storage_tb,
                gpu_hour_usd=current_offer.gpu_hour_usd * (1 - actual_discount) if current_offer.gpu_hour_usd else None,
                cpu_hour_usd=current_offer.cpu_hour_usd * (1 - actual_discount) if current_offer.cpu_hour_usd else None,
                total_cost_usd=new_price,
                estimated_duration_hours=current_offer.estimated_duration_hours,
                is_spot=current_offer.is_spot,
                region=current_offer.region,
                availability_percent=current_offer.availability_percent,
                sla_uptime=current_offer.sla_uptime,
                valid_until=current_offer.valid_until,
            )
        
        message = NegotiationMessage(
            sender=provider.id,
            recipient="agent",
            message_type="response",
            content=content,
            proposed_price_usd=new_price if new_offer else current_offer.total_cost_usd,
        )
        
        return message, new_offer
    
    def get_strategy_description(self) -> str:
        """Get description of current strategy."""
        descriptions = {
            NegotiationStrategy.AGGRESSIVE: "Push hard for maximum discounts, willing to walk away",
            NegotiationStrategy.DEFENSIVE: "Accept reasonable offers quickly, minimize negotiation time",
            NegotiationStrategy.GREEDY: "Always ask for more, maximize savings at any cost",
            NegotiationStrategy.COOPERATIVE: "Build relationships, seek win-win outcomes",
            NegotiationStrategy.BLUFFING: "Use competitive pressure to drive prices down",
            NegotiationStrategy.BALANCED: "Moderate approach balancing price and relationship",
        }
        return descriptions.get(self.strategy, "Unknown strategy")
    
    def analyze_negotiation_history(self) -> dict:
        """Analyze past negotiations to inform future strategy."""
        if not self.negotiation_history:
            return {"total_negotiations": 0}
        
        successful = [n for n in self.negotiation_history if n.status == "accepted"]
        
        avg_discount = sum(
            1 - (n.current_best_offer.total_cost_usd / n.initial_offer_usd) 
            for n in successful 
            if n.current_best_offer and hasattr(n, 'initial_offer_usd')
        ) / len(successful) if successful else 0
        
        return {
            "total_negotiations": len(self.negotiation_history),
            "successful": len(successful),
            "success_rate": len(successful) / len(self.negotiation_history),
            "average_discount": avg_discount,
            "avg_rounds": sum(n.rounds_completed for n in self.negotiation_history) / len(self.negotiation_history),
        }

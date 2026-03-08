"""
Learning Agent

Analyzes episode history to recommend strategies and improve over time.
Provides strategy recommendations based on workload type and past performance.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import importlib.util

_models_path = Path(__file__).parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_models", _models_path)
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)

WorkloadType = _models.WorkloadType
NegotiationStrategy = _models.NegotiationStrategy
EpisodeResult = _models.EpisodeResult


@dataclass
class StrategyRecommendation:
    """Recommended strategy with confidence and reasoning."""
    strategy: NegotiationStrategy
    confidence: float
    reasoning: str
    alternative: Optional[NegotiationStrategy] = None


@dataclass
class LearningInsights:
    """Insights derived from episode history."""
    recommended_strategy: StrategyRecommendation
    avg_reward_trend: str  # "improving", "stable", "declining"
    best_workload_type: Optional[str] = None
    tips: list[str] = None

    def __post_init__(self):
        if self.tips is None:
            self.tips = []


class LearningAgent:
    """
    Agent that learns from episode history to improve recommendations.
    
    Analyzes:
    - Strategy performance by workload type
    - Reward trends
    - Cost/duration prediction accuracy
    """

    STRATEGY_PREFERENCES = {
        WorkloadType.LLM_TRAINING: [NegotiationStrategy.BALANCED, NegotiationStrategy.COOPERATIVE],
        WorkloadType.BATCH_INFERENCE: [NegotiationStrategy.AGGRESSIVE, NegotiationStrategy.BALANCED],
        WorkloadType.REALTIME_INFERENCE: [NegotiationStrategy.DEFENSIVE, NegotiationStrategy.BALANCED],
        WorkloadType.ETL_ANALYTICS: [NegotiationStrategy.AGGRESSIVE, NegotiationStrategy.GREEDY],
        WorkloadType.RENDERING_SIMULATION: [NegotiationStrategy.BALANCED, NegotiationStrategy.COOPERATIVE],
        WorkloadType.MULTIMODAL_PIPELINE: [NegotiationStrategy.COOPERATIVE, NegotiationStrategy.BALANCED],
    }

    def __init__(self):
        self._history: list[EpisodeResult] = []

    def update_history(self, episodes: list[EpisodeResult]) -> None:
        """Update internal history for analysis."""
        self._history = list(episodes)

    def recommend_strategy(
        self,
        workload_type: Optional[WorkloadType] = None,
        episodes: Optional[list[EpisodeResult]] = None,
    ) -> StrategyRecommendation:
        """
        Recommend negotiation strategy based on history and workload type.
        """
        history = episodes or self._history

        if not history:
            pref = self.STRATEGY_PREFERENCES.get(
                workload_type or WorkloadType.LLM_TRAINING,
                [NegotiationStrategy.BALANCED],
            )
            return StrategyRecommendation(
                strategy=pref[0],
                confidence=0.5,
                reasoning="No history yet. Using default recommendation for workload type.",
                alternative=pref[1] if len(pref) > 1 else None,
            )

        workload_type = workload_type or history[-1].workload_type

        # Filter by workload type if we have enough data
        same_type = [e for e in history if e.workload_type == workload_type]
        pool = same_type if len(same_type) >= 2 else history

        # Compute strategy performance
        strat_scores: dict[NegotiationStrategy, list[float]] = {}
        for e in pool:
            s = e.negotiation_strategy
            if s not in strat_scores:
                strat_scores[s] = []
            strat_scores[s].append(e.total_reward)

        if not strat_scores:
            pref = self.STRATEGY_PREFERENCES.get(workload_type, [NegotiationStrategy.BALANCED])
            return StrategyRecommendation(
                strategy=pref[0],
                confidence=0.5,
                reasoning="Insufficient data. Using workload-type preference.",
            )

        best_strat = max(
            strat_scores.keys(),
            key=lambda s: sum(strat_scores[s]) / len(strat_scores[s]),
        )
        best_avg = sum(strat_scores[best_strat]) / len(strat_scores[best_strat])
        all_avgs = [(s, sum(v) / len(v)) for s, v in strat_scores.items()]
        all_avgs.sort(key=lambda x: -x[1])
        second = all_avgs[1][0] if len(all_avgs) > 1 else None

        confidence = min(0.95, 0.5 + 0.1 * len(pool) + 0.05 * len(strat_scores))
        reasoning = (
            f"Based on {len(pool)} past episodes ({len(same_type)} same workload type). "
            f"{best_strat.value} averaged reward {best_avg:.3f}."
        )

        return StrategyRecommendation(
            strategy=best_strat,
            confidence=confidence,
            reasoning=reasoning,
            alternative=second,
        )

    def get_insights(
        self,
        workload_type: Optional[WorkloadType] = None,
        episodes: Optional[list[EpisodeResult]] = None,
    ) -> LearningInsights:
        """Get learning insights including strategy recommendation and tips."""
        history = episodes or self._history
        rec = self.recommend_strategy(workload_type, history)

        # Reward trend
        if len(history) < 3:
            trend = "stable"
        else:
            recent = [e.total_reward for e in history[-5:]]
            older = [e.total_reward for e in history[-10:-5]] if len(history) >= 6 else recent
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older) if older else recent_avg
            trend = "improving" if recent_avg > older_avg * 1.02 else "declining" if recent_avg < older_avg * 0.98 else "stable"

        # Best workload type (by reward)
        wt_rewards: dict[str, list[float]] = {}
        for e in history:
            wt = e.workload_type.value if hasattr(e.workload_type, 'value') else str(e.workload_type)
            wt_rewards.setdefault(wt, []).append(e.total_reward)
        best_wt = max(wt_rewards.keys(), key=lambda w: sum(wt_rewards[w]) / len(wt_rewards[w])) if wt_rewards else None

        # Tips
        tips = []
        if history:
            sla_rate = sum(1 for e in history if e.sla_met) / len(history)
            if sla_rate < 0.8:
                tips.append("SLA success rate is low. Consider defensive strategy or increasing budget slack.")
            cost_accuracy = 1 - sum(abs(e.actual_cost - e.predicted_cost) / max(e.predicted_cost, 1) for e in history) / len(history)
            if cost_accuracy < 0.85:
                tips.append("Cost predictions have high variance. Add buffer to budget.")
            if rec.alternative:
                tips.append(f"If {rec.strategy.value} underperforms, try {rec.alternative.value}.")

        return LearningInsights(
            recommended_strategy=rec,
            avg_reward_trend=trend,
            best_workload_type=best_wt,
            tips=tips or ["Run more episodes to improve recommendations."],
        )

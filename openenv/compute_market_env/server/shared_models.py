"""
Shared models loader for server modules.

Uses importlib to load models from shared-types package to avoid
naming collisions with local modules named 'models'.
"""

import importlib.util
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

# Add necessary types to the global namespace before loading
_models_path = Path(__file__).parent.parent.parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_types_models", _models_path)
_shared_models = importlib.util.module_from_spec(_spec)

# Ensure all required types are available in the module's namespace for forward references
_shared_models.__dict__['Optional'] = Optional
_shared_models.__dict__['Any'] = Any
_shared_models.__dict__['datetime'] = datetime
_shared_models.__dict__['uuid4'] = uuid4

_spec.loader.exec_module(_shared_models)

# Rebuild models to resolve forward references
for name in dir(_shared_models):
    obj = getattr(_shared_models, name)
    if hasattr(obj, 'model_rebuild'):
        try:
            obj.model_rebuild()
        except Exception:
            pass

# Re-export all models
ApprovalDecision = _shared_models.ApprovalDecision
ApprovePlanAction = _shared_models.ApprovePlanAction
CharacterizeWorkloadAction = _shared_models.CharacterizeWorkloadAction
ComputeMarketAction = _shared_models.ComputeMarketAction
ComputeMarketObservation = _shared_models.ComputeMarketObservation
ComputeMarketState = _shared_models.ComputeMarketState
CounterOfferAction = _shared_models.CounterOfferAction
EpisodeResult = _shared_models.EpisodeResult
ExecutePlanAction = _shared_models.ExecutePlanAction
ExecutionPlan = _shared_models.ExecutionPlan
ExecutionStageStatus = _shared_models.ExecutionStageStatus
ExecutionState = _shared_models.ExecutionState
FinalizeEpisodeAction = _shared_models.FinalizeEpisodeAction
GeneratePlanAction = _shared_models.GeneratePlanAction
NegotiationMessage = _shared_models.NegotiationMessage
NegotiationState = _shared_models.NegotiationState
NegotiationStrategy = _shared_models.NegotiationStrategy
OptimizationObjective = _shared_models.OptimizationObjective
OptimizationWeights = _shared_models.OptimizationWeights
PlanComparison = _shared_models.PlanComparison
PlanStatus = _shared_models.PlanStatus
PricingPolicy = _shared_models.PricingPolicy
ProviderCapacity = _shared_models.ProviderCapacity
ProviderOffer = _shared_models.ProviderOffer
ProviderProfile = _shared_models.ProviderProfile
ProviderType = _shared_models.ProviderType
RejectPlanAction = _shared_models.RejectPlanAction
RequestQuotesAction = _shared_models.RequestQuotesAction
ResourceAllocation = _shared_models.ResourceAllocation
ResourceType = _shared_models.ResourceType
RevisePlanAction = _shared_models.RevisePlanAction
StrategyPerformance = _shared_models.StrategyPerformance
SubmitForApprovalAction = _shared_models.SubmitForApprovalAction
SwitchStrategyAction = _shared_models.SwitchStrategyAction
TaskStage = _shared_models.TaskStage
TaskStageType = _shared_models.TaskStageType
WorkloadDecomposition = _shared_models.WorkloadDecomposition
WorkloadSpec = _shared_models.WorkloadSpec
WorkloadType = _shared_models.WorkloadType

__all__ = [
    "ApprovalDecision",
    "ApprovePlanAction",
    "CharacterizeWorkloadAction",
    "ComputeMarketAction",
    "ComputeMarketObservation",
    "ComputeMarketState",
    "CounterOfferAction",
    "EpisodeResult",
    "ExecutePlanAction",
    "ExecutionPlan",
    "ExecutionStageStatus",
    "ExecutionState",
    "FinalizeEpisodeAction",
    "GeneratePlanAction",
    "NegotiationMessage",
    "NegotiationState",
    "NegotiationStrategy",
    "OptimizationObjective",
    "OptimizationWeights",
    "PlanComparison",
    "PlanStatus",
    "PricingPolicy",
    "ProviderCapacity",
    "ProviderOffer",
    "ProviderProfile",
    "ProviderType",
    "RejectPlanAction",
    "RequestQuotesAction",
    "ResourceAllocation",
    "ResourceType",
    "RevisePlanAction",
    "StrategyPerformance",
    "SubmitForApprovalAction",
    "SwitchStrategyAction",
    "TaskStage",
    "TaskStageType",
    "WorkloadDecomposition",
    "WorkloadSpec",
    "WorkloadType",
]

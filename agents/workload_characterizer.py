"""
Workload Characterization Agent

Analyzes workload submissions and decomposes them into execution stages.
Identifies resource requirements, dependencies, and optimal resource types.
"""

import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import importlib.util

_models_path = Path(__file__).parent.parent / "packages" / "shared-types" / "models.py"
_spec = importlib.util.spec_from_file_location("shared_models", _models_path)
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)

WorkloadSpec = _models.WorkloadSpec
WorkloadType = _models.WorkloadType
WorkloadDecomposition = _models.WorkloadDecomposition
TaskStage = _models.TaskStage
TaskStageType = _models.TaskStageType
ResourceType = _models.ResourceType


@dataclass
class CharacterizationResult:
    """Result of workload characterization."""
    decomposition: WorkloadDecomposition
    confidence: float
    analysis_notes: list[str]
    suggested_providers: list[str]


class WorkloadCharacterizer:
    """
    Agent responsible for analyzing and decomposing workloads.
    
    Takes a WorkloadSpec and produces a WorkloadDecomposition with:
    - Task stages with dependencies
    - Resource requirements per stage
    - Estimated durations and costs
    - Critical path analysis
    """
    
    STAGE_TEMPLATES = {
        WorkloadType.LLM_TRAINING: [
            {"name": "Data Preprocessing", "type": TaskStageType.PREPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.10, "gpu_ratio": 0.0},
            {"name": "Dataset Loading", "type": TaskStageType.DATA_LOADING, "resources": [ResourceType.CPU, ResourceType.MEMORY], "duration_ratio": 0.08, "gpu_ratio": 0.0},
            {"name": "Model Initialization", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.02, "gpu_ratio": 1.0},
            {"name": "Forward Pass Training", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.35, "gpu_ratio": 1.0},
            {"name": "Backward Pass & Optimization", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.30, "gpu_ratio": 1.0},
            {"name": "Checkpointing", "type": TaskStageType.IO_HEAVY, "resources": [ResourceType.CPU, ResourceType.MEMORY], "duration_ratio": 0.05, "gpu_ratio": 0.0},
            {"name": "Validation & Metrics", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.08, "gpu_ratio": 0.5},
            {"name": "Model Export", "type": TaskStageType.POSTPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.02, "gpu_ratio": 0.0},
        ],
        WorkloadType.BATCH_INFERENCE: [
            {"name": "Model Loading", "type": TaskStageType.DATA_LOADING, "resources": [ResourceType.GPU, ResourceType.MEMORY], "duration_ratio": 0.10, "gpu_ratio": 0.5},
            {"name": "Batch Preprocessing", "type": TaskStageType.PREPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.15, "gpu_ratio": 0.0},
            {"name": "Inference Execution", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.55, "gpu_ratio": 1.0},
            {"name": "Result Aggregation", "type": TaskStageType.POSTPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.15, "gpu_ratio": 0.0},
            {"name": "Output Storage", "type": TaskStageType.IO_HEAVY, "resources": [ResourceType.CPU], "duration_ratio": 0.05, "gpu_ratio": 0.0},
        ],
        WorkloadType.REALTIME_INFERENCE: [
            {"name": "Model Warm-up", "type": TaskStageType.DATA_LOADING, "resources": [ResourceType.GPU], "duration_ratio": 0.05, "gpu_ratio": 1.0},
            {"name": "Request Processing", "type": TaskStageType.PREPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.10, "gpu_ratio": 0.0},
            {"name": "Inference", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.70, "gpu_ratio": 1.0},
            {"name": "Response Formatting", "type": TaskStageType.POSTPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.15, "gpu_ratio": 0.0},
        ],
        WorkloadType.ETL_ANALYTICS: [
            {"name": "Data Extraction", "type": TaskStageType.IO_HEAVY, "resources": [ResourceType.CPU], "duration_ratio": 0.25, "gpu_ratio": 0.0},
            {"name": "Data Transformation", "type": TaskStageType.MEMORY_INTENSIVE, "resources": [ResourceType.CPU, ResourceType.MEMORY], "duration_ratio": 0.40, "gpu_ratio": 0.0},
            {"name": "Analytics Computation", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.CPU], "duration_ratio": 0.20, "gpu_ratio": 0.0},
            {"name": "Data Loading", "type": TaskStageType.IO_HEAVY, "resources": [ResourceType.CPU], "duration_ratio": 0.15, "gpu_ratio": 0.0},
        ],
        WorkloadType.RENDERING_SIMULATION: [
            {"name": "Scene Loading", "type": TaskStageType.DATA_LOADING, "resources": [ResourceType.GPU, ResourceType.MEMORY], "duration_ratio": 0.10, "gpu_ratio": 0.5},
            {"name": "Geometry Processing", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.15, "gpu_ratio": 1.0},
            {"name": "Ray Tracing / Simulation", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.55, "gpu_ratio": 1.0},
            {"name": "Post-Processing", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.15, "gpu_ratio": 0.8},
            {"name": "Output Encoding", "type": TaskStageType.POSTPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.05, "gpu_ratio": 0.0},
        ],
        WorkloadType.MULTIMODAL_PIPELINE: [
            {"name": "Text Preprocessing", "type": TaskStageType.PREPROCESSING, "resources": [ResourceType.CPU], "duration_ratio": 0.08, "gpu_ratio": 0.0},
            {"name": "Image Preprocessing", "type": TaskStageType.PREPROCESSING, "resources": [ResourceType.CPU, ResourceType.GPU], "duration_ratio": 0.10, "gpu_ratio": 0.3},
            {"name": "Text Encoder", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.20, "gpu_ratio": 1.0},
            {"name": "Vision Encoder", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.25, "gpu_ratio": 1.0},
            {"name": "Fusion & Cross-Attention", "type": TaskStageType.COMPUTE_INTENSIVE, "resources": [ResourceType.GPU], "duration_ratio": 0.25, "gpu_ratio": 1.0},
            {"name": "Output Generation", "type": TaskStageType.POSTPROCESSING, "resources": [ResourceType.GPU], "duration_ratio": 0.12, "gpu_ratio": 0.8},
        ],
    }

    def __init__(self):
        self.analysis_cache: dict[str, CharacterizationResult] = {}

    def characterize(self, workload: WorkloadSpec) -> CharacterizationResult:
        """
        Analyze a workload and produce a detailed decomposition.
        
        Returns a CharacterizationResult with:
        - Decomposed task stages with dependencies
        - Resource requirements per stage
        - Estimated durations based on workload size
        - Confidence score and analysis notes
        """
        stages = self._decompose_workload(workload)
        dependencies = self._compute_dependencies(stages)
        critical_path = self._compute_critical_path(stages, dependencies)
        
        total_hours = sum(s.estimated_duration_hours or 0 for s in stages)
        total_cost = self._estimate_total_cost(stages, workload)
        
        decomposition = WorkloadDecomposition(
            workload_id=workload.id,
            stages=stages,
            total_estimated_hours=total_hours,
            total_estimated_cost_usd=total_cost,
            critical_path_hours=total_hours,
            parallelism_factor=1.2 if workload.allow_heterogeneous_plan else 1.0,
        )
        
        confidence = self._compute_confidence(workload)
        notes = self._generate_analysis_notes(workload, stages)
        suggested = self._suggest_providers(workload, stages)
        
        result = CharacterizationResult(
            decomposition=decomposition,
            confidence=confidence,
            analysis_notes=notes,
            suggested_providers=suggested,
        )
        
        self.analysis_cache[workload.id] = result
        return result

    def _estimate_total_cost(self, stages: list[TaskStage], workload: WorkloadSpec) -> float:
        """Estimate total cost based on stages and resource requirements."""
        total = 0.0
        gpu_rate = 2.50
        cpu_rate = 0.10
        
        for stage in stages:
            duration = stage.estimated_duration_hours or 1.0
            if ResourceType.GPU in stage.required_resource_types:
                total += duration * gpu_rate
            else:
                total += duration * cpu_rate
        
        return round(total, 2)

    def _decompose_workload(self, workload: WorkloadSpec) -> list[TaskStage]:
        """Create task stages based on workload type and characteristics."""
        template = self.STAGE_TEMPLATES.get(
            workload.workload_type,
            self.STAGE_TEMPLATES[WorkloadType.LLM_TRAINING]
        )
        
        base_duration = self._estimate_base_duration(workload)
        base_cost = workload.budget_usd * 0.7
        
        stages = []
        for i, stage_def in enumerate(template):
            duration = base_duration * stage_def["duration_ratio"]
            gpu_hours = duration * stage_def["gpu_ratio"]
            cpu_hours = duration * (1 - stage_def["gpu_ratio"])
            
            estimated_cost = (gpu_hours * 2.50 + cpu_hours * 0.10)
            
            stage = TaskStage(
                name=stage_def["name"],
                stage_type=stage_def["type"],
                required_resource_types=stage_def["resources"],
                preferred_resource_types=self._get_preferred_resources(stage_def, workload),
                estimated_duration_hours=duration,
                estimated_memory_gb=self._estimate_memory_requirement(workload, stage_def),
                parallelizable=stage_def["type"] in [TaskStageType.COMPUTE_INTENSIVE, TaskStageType.PREPROCESSING],
                can_use_spot=workload.allow_spot_instances,
                latency_sensitive=workload.optimization_weights.latency > 0.25,
            )
            stages.append(stage)
        
        return stages

    def _estimate_base_duration(self, workload: WorkloadSpec) -> float:
        """Estimate total duration based on workload size and type."""
        size_factor = 1.0
        
        if workload.model_size_gb:
            size_factor = (workload.model_size_gb / 10) ** 0.7
        elif workload.data_size_gb:
            size_factor = (workload.data_size_gb / 100) ** 0.5
        
        type_multipliers = {
            WorkloadType.LLM_TRAINING: 24.0,
            WorkloadType.BATCH_INFERENCE: 4.0,
            WorkloadType.REALTIME_INFERENCE: 1.0,
            WorkloadType.ETL_ANALYTICS: 6.0,
            WorkloadType.RENDERING_SIMULATION: 12.0,
            WorkloadType.MULTIMODAL_PIPELINE: 8.0,
        }
        
        base = type_multipliers.get(workload.workload_type, 8.0)
        estimated = base * size_factor
        
        return min(estimated, workload.deadline_hours * 0.9)

    def _get_preferred_resources(self, stage_def: dict, workload: WorkloadSpec) -> list[ResourceType]:
        """Determine preferred resources based on optimization weights."""
        preferred = []
        
        if workload.optimization_weights.latency > 0.25:
            if ResourceType.GPU in stage_def["resources"]:
                preferred.append(ResourceType.NPU)
        
        if workload.optimization_weights.cost > 0.35:
            preferred.append(ResourceType.CPU)
        
        return preferred if preferred else stage_def["resources"]

    def _estimate_memory_requirement(self, workload: WorkloadSpec, stage_def: dict) -> float:
        """Estimate RAM requirement for a stage."""
        base_memory = 8.0
        
        if workload.model_size_gb:
            if stage_def["type"] == TaskStageType.COMPUTE_INTENSIVE:
                base_memory = workload.model_size_gb * 2
            else:
                base_memory = workload.model_size_gb
        
        if workload.data_size_gb:
            base_memory = max(base_memory, workload.data_size_gb * 0.3)
        
        return round(base_memory, 1)

    def _estimate_gpu_memory(self, workload: WorkloadSpec, stage_def: dict) -> float:
        """Estimate GPU memory requirement."""
        if not workload.model_size_gb:
            return 16.0
        
        training_factor = 4.0 if workload.workload_type == WorkloadType.LLM_TRAINING else 1.5
        
        return round(workload.model_size_gb * training_factor, 1)

    def _compute_dependencies(self, stages: list[TaskStage]) -> dict[str, list[str]]:
        """Compute stage dependencies (simple linear for now)."""
        dependencies = {}
        for i, stage in enumerate(stages):
            if i == 0:
                dependencies[stage.id] = []
            else:
                dependencies[stage.id] = [stages[i-1].id]
        return dependencies

    def _compute_critical_path(self, stages: list[TaskStage], dependencies: dict) -> list[str]:
        """Identify critical path stages."""
        return [s.id for s in stages]

    def _compute_confidence(self, workload: WorkloadSpec) -> float:
        """Compute confidence in the characterization."""
        confidence = 0.8
        
        if workload.model_size_gb or workload.data_size_gb:
            confidence += 0.1
        
        if workload.workload_type in self.STAGE_TEMPLATES:
            confidence += 0.05
        
        return min(confidence, 0.98)

    def _generate_analysis_notes(self, workload: WorkloadSpec, stages: list[TaskStage]) -> list[str]:
        """Generate human-readable analysis notes."""
        notes = []
        
        gpu_stages = [s for s in stages if ResourceType.GPU in s.required_resource_types]
        notes.append(f"Identified {len(gpu_stages)} GPU-intensive stages out of {len(stages)} total")
        
        total_hours = sum(s.estimated_duration_hours or 0 for s in stages)
        notes.append(f"Estimated total duration: {total_hours:.1f} hours")
        
        if workload.deadline_hours:
            slack = workload.deadline_hours - total_hours
            if slack > 0:
                notes.append(f"Schedule slack: {slack:.1f} hours available")
            else:
                notes.append("WARNING: Estimated duration exceeds deadline")
        
        if workload.allow_heterogeneous_plan:
            notes.append("Heterogeneous execution enabled - will consider CPU/GPU/NPU mix")
        
        return notes

    def _suggest_providers(self, workload: WorkloadSpec, stages: list[TaskStage]) -> list[str]:
        """Suggest suitable provider types based on workload characteristics."""
        suggestions = []
        
        gpu_ratio = sum(
            (s.estimated_duration_hours or 0) 
            for s in stages 
            if ResourceType.GPU in s.required_resource_types
        ) / max(sum(s.estimated_duration_hours or 0 for s in stages), 0.1)
        
        if gpu_ratio > 0.5:
            suggestions.append("neocloud_gpu")
            if workload.optimization_weights.cost > 0.3:
                suggestions.append("hyperscaler")
        else:
            suggestions.append("datacenter_cpu")
        
        if workload.optimization_weights.energy > 0.15:
            suggestions.append("green_datacenter")
        
        return suggestions

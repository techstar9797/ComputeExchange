"""
Scenario Generator

Generates and manages scenarios for the compute marketplace environment.
Includes predefined demo scenarios and random generation.
"""

import random
from dataclasses import dataclass
from typing import Optional

from .shared_models import (
    NegotiationStrategy,
    OptimizationWeights,
    PricingPolicy,
    ProviderCapacity,
    ProviderProfile,
    ProviderType,
    ResourceType,
    WorkloadSpec,
    WorkloadType,
)


@dataclass
class Scenario:
    """A complete scenario with workload and providers."""
    id: str
    name: str
    description: str
    workload: Optional[WorkloadSpec]
    providers: list[ProviderProfile]
    difficulty: str  # "easy", "medium", "hard"
    tags: list[str]


class ScenarioGenerator:
    """
    Generates scenarios for the compute marketplace.
    
    Includes:
    - Predefined demo scenarios for hackathon presentation
    - Random scenario generation for training
    - Configurable difficulty levels
    """
    
    # Provider archetypes (real cloud provider names)
    PROVIDER_ARCHETYPES = {
        "neocloud_gpu": ProviderProfile(
            id="nebius",
            name="Nebius",
            provider_type=ProviderType.NEOCLOUD_GPU,
            capacity=ProviderCapacity(
                gpu_count=128,
                gpu_memory_gb=80,
                cpu_cores=256,
                memory_gb=2048,
                storage_tb=100,
                utilization_percent=65,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=2.50,
                base_cpu_hour_usd=0.08,
                spot_discount_percent=60,
                reserved_discount_percent=30,
                min_commitment_hours=1,
                surge_multiplier=1.5,
            ),
            reliability_score=0.97,
            avg_latency_ms=25,
            regions=["us-west-2", "us-east-1", "eu-west-1"],
            compliance_certifications=["SOC2", "ISO27001"],
            carbon_intensity_gco2_kwh=350,
            renewable_energy_percent=40,
            negotiation_flexibility=0.25,
            negotiation_style=NegotiationStrategy.AGGRESSIVE,
            sla_uptime_guarantee=0.995,
        ),
        "datacenter_cpu": ProviderProfile(
            id="aws",
            name="AWS",
            provider_type=ProviderType.DATACENTER_CPU,
            capacity=ProviderCapacity(
                gpu_count=32,
                gpu_memory_gb=32,
                cpu_cores=1024,
                memory_gb=8192,
                storage_tb=500,
                utilization_percent=45,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=3.00,
                base_cpu_hour_usd=0.04,
                spot_discount_percent=40,
                reserved_discount_percent=40,
                min_commitment_hours=24,
                surge_multiplier=1.2,
            ),
            reliability_score=0.999,
            avg_latency_ms=50,
            regions=["us-east-1", "us-west-1", "eu-central-1"],
            compliance_certifications=["SOC2", "ISO27001", "HIPAA", "PCI-DSS"],
            carbon_intensity_gco2_kwh=450,
            renewable_energy_percent=20,
            negotiation_flexibility=0.15,
            negotiation_style=NegotiationStrategy.DEFENSIVE,
            sla_uptime_guarantee=0.9999,
        ),
        "hyperscaler": ProviderProfile(
            id="google-cloud",
            name="Google Cloud",
            provider_type=ProviderType.HYPERSCALER,
            capacity=ProviderCapacity(
                gpu_count=512,
                gpu_memory_gb=80,
                cpu_cores=4096,
                memory_gb=16384,
                storage_tb=1000,
                utilization_percent=55,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=3.50,
                base_cpu_hour_usd=0.05,
                spot_discount_percent=70,
                reserved_discount_percent=35,
                min_commitment_hours=0,
                surge_multiplier=2.0,
            ),
            reliability_score=0.9995,
            avg_latency_ms=15,
            regions=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"],
            compliance_certifications=["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP"],
            carbon_intensity_gco2_kwh=380,
            renewable_energy_percent=50,
            negotiation_flexibility=0.10,
            negotiation_style=NegotiationStrategy.BALANCED,
            sla_uptime_guarantee=0.9999,
        ),
        "edge_npu": ProviderProfile(
            id="lambda-labs",
            name="Lambda Labs",
            provider_type=ProviderType.EDGE_NPU,
            capacity=ProviderCapacity(
                gpu_count=0,
                npu_count=256,
                cpu_cores=128,
                memory_gb=512,
                storage_tb=50,
                utilization_percent=30,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=0,
                base_cpu_hour_usd=0.03,
                base_npu_hour_usd=0.80,
                spot_discount_percent=30,
                reserved_discount_percent=25,
                min_commitment_hours=1,
                surge_multiplier=1.3,
            ),
            reliability_score=0.96,
            avg_latency_ms=5,
            regions=["us-west-2", "us-east-1"],
            compliance_certifications=["SOC2"],
            carbon_intensity_gco2_kwh=200,
            renewable_energy_percent=60,
            negotiation_flexibility=0.30,
            negotiation_style=NegotiationStrategy.COOPERATIVE,
            sla_uptime_guarantee=0.99,
        ),
        "green_datacenter": ProviderProfile(
            id="coreweave",
            name="CoreWeave",
            provider_type=ProviderType.GREEN_DATACENTER,
            capacity=ProviderCapacity(
                gpu_count=64,
                gpu_memory_gb=48,
                cpu_cores=512,
                memory_gb=4096,
                storage_tb=200,
                utilization_percent=50,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=2.80,
                base_cpu_hour_usd=0.06,
                spot_discount_percent=45,
                reserved_discount_percent=30,
                min_commitment_hours=4,
                surge_multiplier=1.4,
            ),
            reliability_score=0.98,
            avg_latency_ms=35,
            regions=["eu-north-1", "us-west-2"],
            compliance_certifications=["SOC2", "ISO27001", "ISO14001"],
            carbon_intensity_gco2_kwh=50,
            renewable_energy_percent=100,
            negotiation_flexibility=0.20,
            negotiation_style=NegotiationStrategy.COOPERATIVE,
            sla_uptime_guarantee=0.995,
        ),
        "hyperscaler_azure": ProviderProfile(
            id="azure",
            name="Azure",
            provider_type=ProviderType.HYPERSCALER,
            capacity=ProviderCapacity(
                gpu_count=384,
                gpu_memory_gb=80,
                cpu_cores=3072,
                memory_gb=12288,
                storage_tb=800,
                utilization_percent=52,
            ),
            pricing=PricingPolicy(
                base_gpu_hour_usd=3.20,
                base_cpu_hour_usd=0.048,
                spot_discount_percent=65,
                reserved_discount_percent=32,
                min_commitment_hours=0,
                surge_multiplier=1.8,
            ),
            reliability_score=0.9995,
            avg_latency_ms=18,
            regions=["eastus", "westus2", "westeurope", "southeastasia"],
            compliance_certifications=["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP"],
            carbon_intensity_gco2_kwh=420,
            renewable_energy_percent=45,
            negotiation_flexibility=0.12,
            negotiation_style=NegotiationStrategy.BALANCED,
            sla_uptime_guarantee=0.9999,
        ),
    }

    # Predefined scenarios for demo
    DEMO_SCENARIOS = {
        "llm_training_7b": Scenario(
            id="llm_training_7b",
            name="LLM Training - 7B Parameters",
            description="Train a 7B parameter language model on custom dataset",
            workload=WorkloadSpec(
                name="LLM-7B-Training-v1",
                workload_type=WorkloadType.LLM_TRAINING,
                model_size_gb=28,
                data_size_gb=500,
                batch_size=32,
                deadline_hours=72,
                budget_usd=5000,
                preferred_regions=["us-west-2", "us-east-1"],
                compliance_requirements=["SOC2"],
                optimization_weights=OptimizationWeights(
                    cost=0.35,
                    latency=0.15,
                    throughput=0.25,
                    energy=0.1,
                    reliability=0.15,
                ),
                allow_spot_instances=True,
                allow_heterogeneous_plan=True,
                min_reliability_score=0.95,
            ),
            providers=[],  # Populated at runtime
            difficulty="medium",
            tags=["training", "llm", "gpu-intensive"],
        ),
        "realtime_inference": Scenario(
            id="realtime_inference",
            name="Real-time Inference API",
            description="Deploy low-latency inference endpoint for production traffic",
            workload=WorkloadSpec(
                name="Inference-API-Prod",
                workload_type=WorkloadType.REALTIME_INFERENCE,
                model_size_gb=8,
                deadline_hours=24,
                budget_usd=2000,
                preferred_regions=["us-east-1"],
                compliance_requirements=["SOC2", "HIPAA"],
                optimization_weights=OptimizationWeights(
                    cost=0.2,
                    latency=0.4,
                    throughput=0.15,
                    energy=0.05,
                    reliability=0.2,
                ),
                allow_spot_instances=False,
                allow_heterogeneous_plan=True,
                min_reliability_score=0.999,
            ),
            providers=[],
            difficulty="hard",
            tags=["inference", "low-latency", "production"],
        ),
        "batch_analytics": Scenario(
            id="batch_analytics",
            name="Batch Analytics Pipeline",
            description="Process large dataset for business intelligence",
            workload=WorkloadSpec(
                name="BI-Analytics-Q4",
                workload_type=WorkloadType.ETL_ANALYTICS,
                data_size_gb=2000,
                deadline_hours=8,
                budget_usd=500,
                preferred_regions=["us-west-2"],
                optimization_weights=OptimizationWeights(
                    cost=0.5,
                    latency=0.1,
                    throughput=0.2,
                    energy=0.1,
                    reliability=0.1,
                ),
                allow_spot_instances=True,
                allow_heterogeneous_plan=True,
            ),
            providers=[],
            difficulty="easy",
            tags=["analytics", "batch", "cost-sensitive"],
        ),
        "multimodal_pipeline": Scenario(
            id="multimodal_pipeline",
            name="Multimodal AI Pipeline",
            description="Video + audio processing with multiple model stages",
            workload=WorkloadSpec(
                name="MultiModal-Pipeline-v2",
                workload_type=WorkloadType.MULTIMODAL_PIPELINE,
                model_size_gb=45,
                data_size_gb=100,
                deadline_hours=12,
                budget_usd=3000,
                preferred_regions=["us-west-2", "us-east-1"],
                compliance_requirements=["SOC2"],
                optimization_weights=OptimizationWeights(
                    cost=0.25,
                    latency=0.25,
                    throughput=0.2,
                    energy=0.15,
                    reliability=0.15,
                ),
                allow_spot_instances=True,
                allow_heterogeneous_plan=True,
            ),
            providers=[],
            difficulty="hard",
            tags=["multimodal", "video", "complex"],
        ),
        "green_training": Scenario(
            id="green_training",
            name="Carbon-Neutral Model Training",
            description="Train model with minimal carbon footprint",
            workload=WorkloadSpec(
                name="Green-Training-Initiative",
                workload_type=WorkloadType.LLM_TRAINING,
                model_size_gb=15,
                data_size_gb=200,
                deadline_hours=168,  # 1 week - flexible
                budget_usd=8000,
                preferred_regions=["eu-north-1"],
                compliance_requirements=["ISO14001"],
                optimization_weights=OptimizationWeights(
                    cost=0.15,
                    latency=0.05,
                    throughput=0.1,
                    energy=0.6,
                    reliability=0.1,
                ),
                allow_spot_instances=True,
                allow_heterogeneous_plan=True,
            ),
            providers=[],
            difficulty="medium",
            tags=["green", "sustainable", "training"],
        ),
    }
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the scenario generator."""
        self.rng = random.Random(seed)
    
    def load_scenario(self, scenario_id: str) -> Scenario:
        """
        Load a predefined scenario by ID.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            The scenario with providers populated
        """
        if scenario_id not in self.DEMO_SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        scenario = self.DEMO_SCENARIOS[scenario_id]
        
        # Populate providers based on scenario needs
        scenario.providers = self._select_providers_for_scenario(scenario)
        
        return scenario
    
    def generate_random(self, seed: Optional[int] = None) -> Scenario:
        """
        Generate a random scenario.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            A randomly generated scenario
        """
        if seed is not None:
            self.rng = random.Random(seed)
        
        # Random workload type
        workload_type = self.rng.choice(list(WorkloadType))
        
        # Generate workload based on type
        workload = self._generate_random_workload(workload_type)
        
        # Select 3-5 providers
        num_providers = self.rng.randint(3, 5)
        providers = self.rng.sample(
            list(self.PROVIDER_ARCHETYPES.values()),
            min(num_providers, len(self.PROVIDER_ARCHETYPES))
        )
        
        # Add variance to providers
        providers = [self._add_provider_variance(p) for p in providers]
        
        return Scenario(
            id=f"random_{seed or self.rng.randint(0, 10000)}",
            name=f"Random Scenario",
            description="Randomly generated scenario for training",
            workload=workload,
            providers=providers,
            difficulty=self.rng.choice(["easy", "medium", "hard"]),
            tags=["random", "training"],
        )
    
    def _generate_random_workload(self, workload_type: WorkloadType) -> WorkloadSpec:
        """Generate a random workload of the given type."""
        configs = {
            WorkloadType.LLM_TRAINING: {
                "model_size_gb": self.rng.uniform(5, 100),
                "data_size_gb": self.rng.uniform(50, 1000),
                "deadline_hours": self.rng.uniform(24, 168),
                "budget_usd": self.rng.uniform(1000, 20000),
            },
            WorkloadType.BATCH_INFERENCE: {
                "model_size_gb": self.rng.uniform(2, 30),
                "data_size_gb": self.rng.uniform(10, 500),
                "deadline_hours": self.rng.uniform(1, 24),
                "budget_usd": self.rng.uniform(100, 2000),
            },
            WorkloadType.REALTIME_INFERENCE: {
                "model_size_gb": self.rng.uniform(2, 20),
                "deadline_hours": self.rng.uniform(1, 48),
                "budget_usd": self.rng.uniform(500, 5000),
            },
            WorkloadType.ETL_ANALYTICS: {
                "data_size_gb": self.rng.uniform(100, 5000),
                "deadline_hours": self.rng.uniform(2, 24),
                "budget_usd": self.rng.uniform(200, 2000),
            },
            WorkloadType.RENDERING_SIMULATION: {
                "data_size_gb": self.rng.uniform(50, 500),
                "deadline_hours": self.rng.uniform(4, 48),
                "budget_usd": self.rng.uniform(500, 5000),
            },
            WorkloadType.MULTIMODAL_PIPELINE: {
                "model_size_gb": self.rng.uniform(10, 80),
                "data_size_gb": self.rng.uniform(20, 300),
                "deadline_hours": self.rng.uniform(4, 72),
                "budget_usd": self.rng.uniform(1000, 10000),
            },
        }
        
        config = configs.get(workload_type, configs[WorkloadType.ETL_ANALYTICS])
        
        return WorkloadSpec(
            name=f"Random-{workload_type.value}-{self.rng.randint(1000, 9999)}",
            workload_type=workload_type,
            model_size_gb=config.get("model_size_gb"),
            data_size_gb=config.get("data_size_gb"),
            deadline_hours=config["deadline_hours"],
            budget_usd=config["budget_usd"],
            preferred_regions=self.rng.sample(
                ["us-west-2", "us-east-1", "eu-west-1", "ap-southeast-1"],
                self.rng.randint(1, 2)
            ),
            optimization_weights=OptimizationWeights(
                cost=self.rng.uniform(0.1, 0.5),
                latency=self.rng.uniform(0.1, 0.4),
                throughput=self.rng.uniform(0.1, 0.3),
                energy=self.rng.uniform(0.05, 0.2),
                reliability=self.rng.uniform(0.1, 0.3),
            ).normalize(),
            allow_spot_instances=self.rng.random() > 0.3,
            allow_heterogeneous_plan=self.rng.random() > 0.2,
            min_reliability_score=self.rng.uniform(0.9, 0.999),
        )
    
    def _select_providers_for_scenario(self, scenario: Scenario) -> list[ProviderProfile]:
        """Select appropriate providers for a scenario."""
        providers = list(self.PROVIDER_ARCHETYPES.values())
        
        # Add variance to make each run slightly different
        return [self._add_provider_variance(p) for p in providers]
    
    def _add_provider_variance(self, provider: ProviderProfile) -> ProviderProfile:
        """Add random variance to a provider profile."""
        # Create a copy with variance
        data = provider.model_dump()
        
        # Vary utilization
        data["capacity"]["utilization_percent"] = max(
            0,
            min(100, data["capacity"]["utilization_percent"] + self.rng.uniform(-20, 20))
        )
        
        # Vary pricing slightly
        data["pricing"]["base_gpu_hour_usd"] *= self.rng.uniform(0.9, 1.1)
        data["pricing"]["base_cpu_hour_usd"] *= self.rng.uniform(0.9, 1.1)
        
        # Vary reliability slightly
        data["reliability_score"] = max(
            0.9,
            min(1.0, data["reliability_score"] + self.rng.uniform(-0.02, 0.02))
        )
        
        # Give unique ID
        data["id"] = f"{data['id']}-{self.rng.randint(1000, 9999)}"
        
        return ProviderProfile(**data)
    
    def list_scenarios(self) -> list[dict]:
        """List all available predefined scenarios."""
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "difficulty": s.difficulty,
                "tags": s.tags,
            }
            for s in self.DEMO_SCENARIOS.values()
        ]

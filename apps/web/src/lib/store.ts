import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AppPhase =
  | "landing"
  | "submission"
  | "orchestration"
  | "approval"
  | "execution"
  | "analytics";

interface WorkloadState {
  name: string;
  workloadType: string;
  modelSizeGb: number;
  dataSizeGb: number;
  deadlineHours: number;
  budgetUsd: number;
  preferredRegions: string[];
  complianceRequirements: string[];
  costWeight: number;
  latencyWeight: number;
  throughputWeight: number;
  energyWeight: number;
  reliabilityWeight: number;
  allowSpotInstances: boolean;
  allowHeterogeneousPlan: boolean;
}

interface CharacterizationResult {
  confidence: number;
  analysis_notes: string[];
  suggested_providers: string[];
  total_stages: number;
  total_estimated_hours: number;
  total_estimated_cost_usd: number;
}

interface Stage {
  id: string;
  name: string;
  type: string;
  resources: string[];
  duration_hours: number;
  memory_gb: number;
  parallelizable: boolean;
}

interface PlanComparison {
  budget: number;
  cheapest: number;
  most_expensive: number;
  deadline: number;
  fastest: number;
  slowest: number;
}

interface AppStore {
  // Session
  sessionId: string | null;
  phase: AppPhase;
  serverPhase: string | null;
  
  // Workload
  workload: WorkloadState;
  decomposition: any | null;
  characterization: CharacterizationResult | null;
  stages: Stage[];
  
  // Marketplace
  providers: any[];
  offers: any[];
  negotiationRound: number;
  negotiationStrategy: string;
  
  // Plans
  plans: any[];
  selectedPlanId: string | null;
  planComparison: PlanComparison | null;
  recommendation: string | null;
  
  // Execution
  execution: any | null;
  
  // Results
  episodeReward: number;
  rewardBreakdown: Record<string, number>;
  
  // Actions
  setSessionId: (id: string | null) => void;
  setPhase: (phase: AppPhase) => void;
  setWorkload: (workload: Partial<WorkloadState>) => void;
  setDecomposition: (decomposition: any) => void;
  setCharacterization: (char: CharacterizationResult, stages: Stage[]) => void;
  setProviders: (providers: any[]) => void;
  setOffers: (offers: any[]) => void;
  setNegotiationRound: (round: number) => void;
  setNegotiationStrategy: (strategy: string) => void;
  setPlans: (plans: any[], comparison?: any, recommendation?: string) => void;
  setSelectedPlanId: (id: string | null) => void;
  setExecution: (execution: any) => void;
  setEpisodeReward: (reward: number, breakdown?: Record<string, number>) => void;
  syncFromServerState: (state: {
    phase?: string;
    providers?: any[];
    offers?: any[];
    plans?: any[];
    decomposition?: any;
    negotiation?: { offers?: any[] };
  }) => void;
  restoreFromServerState: (state: {
    phase?: string;
    decomposition?: any;
    offers?: any[];
    plans?: any[];
    execution?: any;
    episode_reward?: number;
    selected_plan?: any;
    workload?: any;
  }) => void;
  reset: () => void;
}

const initialWorkload: WorkloadState = {
  name: "",
  workloadType: "llm_training",
  modelSizeGb: 30,
  dataSizeGb: 100,
  deadlineHours: 48,
  budgetUsd: 3000,
  preferredRegions: ["us-west-2"],
  complianceRequirements: [],
  costWeight: 0.3,
  latencyWeight: 0.25,
  throughputWeight: 0.15,
  energyWeight: 0.1,
  reliabilityWeight: 0.2,
  allowSpotInstances: true,
  allowHeterogeneousPlan: true,
};

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
  sessionId: null,
  phase: "landing",
  serverPhase: null,
  workload: initialWorkload,
  decomposition: null,
  characterization: null,
  stages: [],
  providers: [],
  offers: [],
  negotiationRound: 0,
  negotiationStrategy: "balanced",
  plans: [],
  selectedPlanId: null,
  planComparison: null,
  recommendation: null,
  execution: null,
  episodeReward: 0,
  rewardBreakdown: {},
  
  setSessionId: (id) => set({ sessionId: id }),
  setPhase: (phase) => set({ phase }),
  setWorkload: (workload) =>
    set((state) => ({ workload: { ...state.workload, ...workload } })),
  setDecomposition: (decomposition) => set({ decomposition }),
  setCharacterization: (char, stages) => set({ characterization: char, stages }),
  setProviders: (providers) => set({ providers }),
  setOffers: (offers) => set({ offers }),
  setNegotiationRound: (round) => set({ negotiationRound: round }),
  setNegotiationStrategy: (strategy) => set({ negotiationStrategy: strategy }),
  setPlans: (plans, comparison = null, recommendation = null) => 
    set({ plans, planComparison: comparison, recommendation }),
  setSelectedPlanId: (id) => set({ selectedPlanId: id }),
  setExecution: (execution) => set({ execution }),
  setEpisodeReward: (reward, breakdown = {}) =>
    set({ episodeReward: reward, rewardBreakdown: breakdown }),
  syncFromServerState: (state) =>
    set((s) => {
      const offers = state.offers ?? state.negotiation?.offers ?? s.offers;
      const next: Partial<AppStore> = {};
      if (state.phase) next.serverPhase = state.phase;
      if (state.providers) next.providers = state.providers;
      if (offers && offers !== s.offers) next.offers = offers;
      if (state.decomposition) next.decomposition = state.decomposition;
      if (state.plans && state.plans.length > 0) {
        next.plans = state.plans.map((p: any) => ({
          id: p.id,
          plan_type: p.plan_type || "balanced",
          total_cost_usd: p.total_cost_usd ?? 0,
          total_duration_hours: p.total_duration_hours ?? 0,
          reliability_score: p.reliability_score ?? 0.9,
          carbon_footprint_kg: p.carbon_footprint_kg ?? 0,
          optimization_score: p.optimization_score ?? 0.5,
        }));
      }
      return next;
    }),
  restoreFromServerState: (state) =>
    set((s) => {
      const next: Partial<AppStore> = {};
      if (state.phase) next.serverPhase = state.phase;
      if (state.decomposition) next.decomposition = state.decomposition;
      if (state.offers?.length) next.offers = state.offers;
      if (state.execution) next.execution = state.execution;
      if (state.episode_reward != null) next.episodeReward = state.episode_reward;
      if (state.selected_plan) next.selectedPlanId = state.selected_plan?.id ?? s.selectedPlanId;
      if (state.workload) {
        const w = state.workload;
        next.workload = {
          ...s.workload,
          name: w.name ?? s.workload.name,
          workloadType: w.workload_type ?? s.workload.workloadType,
          modelSizeGb: w.model_size_gb ?? s.workload.modelSizeGb,
          dataSizeGb: w.data_size_gb ?? s.workload.dataSizeGb,
          deadlineHours: w.deadline_hours ?? s.workload.deadlineHours,
          budgetUsd: w.budget_usd ?? s.workload.budgetUsd,
        };
      }
      if (state.plans?.length) {
        next.plans = state.plans.map((p: any) => ({
          id: p.id,
          plan_type: p.plan_type || "balanced",
          total_cost_usd: p.total_cost_usd ?? 0,
          total_duration_hours: p.total_duration_hours ?? 0,
          reliability_score: p.reliability_score ?? 0.9,
          carbon_footprint_kg: p.carbon_footprint_kg ?? 0,
          optimization_score: p.optimization_score ?? 0.5,
        }));
      }
      return next;
    }),
  reset: () =>
    set({
      sessionId: null,
      phase: "landing",
      serverPhase: null,
      workload: initialWorkload,
      decomposition: null,
      characterization: null,
      stages: [],
      providers: [],
      offers: [],
      negotiationRound: 0,
      negotiationStrategy: "balanced",
      plans: [],
      selectedPlanId: null,
      planComparison: null,
      recommendation: null,
      execution: null,
      episodeReward: 0,
      rewardBreakdown: {},
    }),
    }),
    {
      name: "compute-exchange-session",
      partialize: (s) => ({ sessionId: s.sessionId }),
    }
  )
);

import { create } from "zustand";

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

interface AppStore {
  // Session
  sessionId: string | null;
  phase: AppPhase;
  
  // Workload
  workload: WorkloadState;
  decomposition: any | null;
  
  // Marketplace
  providers: any[];
  offers: any[];
  negotiationRound: number;
  negotiationStrategy: string;
  
  // Plans
  plans: any[];
  selectedPlanId: string | null;
  
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
  setProviders: (providers: any[]) => void;
  setOffers: (offers: any[]) => void;
  setNegotiationRound: (round: number) => void;
  setNegotiationStrategy: (strategy: string) => void;
  setPlans: (plans: any[]) => void;
  setSelectedPlanId: (id: string | null) => void;
  setExecution: (execution: any) => void;
  setEpisodeReward: (reward: number, breakdown?: Record<string, number>) => void;
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

export const useAppStore = create<AppStore>((set) => ({
  sessionId: null,
  phase: "landing",
  workload: initialWorkload,
  decomposition: null,
  providers: [],
  offers: [],
  negotiationRound: 0,
  negotiationStrategy: "balanced",
  plans: [],
  selectedPlanId: null,
  execution: null,
  episodeReward: 0,
  rewardBreakdown: {},
  
  setSessionId: (id) => set({ sessionId: id }),
  setPhase: (phase) => set({ phase }),
  setWorkload: (workload) =>
    set((state) => ({ workload: { ...state.workload, ...workload } })),
  setDecomposition: (decomposition) => set({ decomposition }),
  setProviders: (providers) => set({ providers }),
  setOffers: (offers) => set({ offers }),
  setNegotiationRound: (round) => set({ negotiationRound: round }),
  setNegotiationStrategy: (strategy) => set({ negotiationStrategy: strategy }),
  setPlans: (plans) => set({ plans }),
  setSelectedPlanId: (id) => set({ selectedPlanId: id }),
  setExecution: (execution) => set({ execution }),
  setEpisodeReward: (reward, breakdown = {}) =>
    set({ episodeReward: reward, rewardBreakdown: breakdown }),
  reset: () =>
    set({
      sessionId: null,
      phase: "landing",
      workload: initialWorkload,
      decomposition: null,
      providers: [],
      offers: [],
      negotiationRound: 0,
      negotiationStrategy: "balanced",
      plans: [],
      selectedPlanId: null,
      execution: null,
      episodeReward: 0,
      rewardBreakdown: {},
    }),
}));

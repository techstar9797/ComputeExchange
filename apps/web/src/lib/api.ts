const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface WorkloadSubmission {
  name: string;
  workload_type: string;
  model_size_gb?: number;
  data_size_gb?: number;
  batch_size?: number;
  deadline_hours: number;
  budget_usd: number;
  preferred_regions: string[];
  compliance_requirements: string[];
  cost_weight: number;
  latency_weight: number;
  throughput_weight: number;
  energy_weight: number;
  reliability_weight: number;
  allow_spot_instances: boolean;
  allow_heterogeneous_plan: boolean;
  min_reliability_score: number;
}

export interface SessionState {
  session_id: string;
  phase: string;
  step_count: number;
  workload?: any;
  decomposition?: any;
  providers: any[];
  offers: any[];
  plans: any[];
  selected_plan?: any;
  execution?: any;
  episode_reward: number;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  difficulty: string;
  tags: string[];
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = body.detail;
      let message = `Request failed (${response.status})`;
      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join("; ");
      } else if (detail && typeof detail === "object" && "msg" in detail) {
        message = (detail as { msg: string }).msg;
      }
      throw new Error(message);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request("/health");
  }

  async createSession(): Promise<{ session_id: string; status: string }> {
    return this.request("/session/create", { method: "POST" });
  }

  async getScenarios(): Promise<{ scenarios: Scenario[] }> {
    return this.request("/scenarios");
  }

  async resetSession(
    sessionId: string,
    scenarioId?: string,
    seed?: number
  ): Promise<any> {
    const params = new URLSearchParams();
    if (scenarioId) params.set("scenario_id", scenarioId);
    if (seed) params.set("seed", seed.toString());
    const query = params.toString() ? `?${params}` : "";
    return this.request(`/session/${sessionId}/reset${query}`, {
      method: "POST",
    });
  }

  async submitWorkload(workload: WorkloadSubmission): Promise<any> {
    return this.request("/workload/submit", {
      method: "POST",
      body: JSON.stringify(workload),
    });
  }

  async startNegotiation(
    sessionId: string,
    strategy: string = "balanced",
    maxRounds: number = 5
  ): Promise<any> {
    return this.request(`/session/${sessionId}/negotiate`, {
      method: "POST",
      body: JSON.stringify({
        strategy,
        max_rounds: maxRounds,
        target_providers: [],
      }),
    });
  }

  async generatePlans(
    sessionId: string,
    planTypes: string[] = ["balanced", "cheapest", "fastest", "greenest"]
  ): Promise<any> {
    return this.request("/plans/generate", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        plan_types: planTypes,
      }),
    });
  }

  async submitForApproval(
    sessionId: string,
    planId: string,
    summary: string
  ): Promise<any> {
    const params = new URLSearchParams({
      session_id: sessionId,
      plan_id: planId,
      summary,
    });
    return this.request(`/plans/submit-approval?${params}`, {
      method: "POST",
    });
  }

  async approvePlan(
    sessionId: string,
    planId: string,
    decision: "approve" | "reject",
    feedback: string = ""
  ): Promise<any> {
    return this.request("/plans/approve", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        plan_id: planId,
        decision,
        feedback,
      }),
    });
  }

  async startExecution(sessionId: string, planId: string): Promise<any> {
    return this.request("/execution/start", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        plan_id: planId,
      }),
    });
  }

  async finalizeEpisode(sessionId: string): Promise<any> {
    return this.request(`/session/${sessionId}/finalize`, { method: "POST" });
  }

  async getSessionState(sessionId: string): Promise<SessionState> {
    return this.request(`/session/${sessionId}/state`);
  }

  async getAnalytics(): Promise<any> {
    return this.request("/analytics/metrics");
  }

  async getEpisodeHistory(limit: number = 50): Promise<any> {
    return this.request(`/analytics/history?limit=${limit}`);
  }
}

export const api = new ApiClient();

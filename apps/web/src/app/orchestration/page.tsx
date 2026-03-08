"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Server,
  ArrowLeft,
  ArrowRight,
  Cpu,
  Brain,
  Zap,
  Shield,
  Leaf,
  Clock,
  DollarSign,
  CheckCircle,
  MessageSquare,
  Users,
  BarChart3,
  Activity,
  Target,
  Wifi,
  WifiOff,
  Loader2,
} from "lucide-react";
import { useOrchestrationWebSocket } from "@/hooks/useOrchestrationWebSocket";
import { useSessionRecovery } from "@/hooks/useSessionRecovery";
import { useErrorStore } from "@/lib/error-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppStore } from "@/lib/store";
import { api } from "@/lib/api";
import { getProviderDisplayName } from "@/lib/provider-names";

const negotiationStrategies = [
  { value: "aggressive", label: "Aggressive", description: "Push for lowest prices" },
  { value: "defensive", label: "Defensive", description: "Prioritize reliability" },
  { value: "balanced", label: "Balanced", description: "Optimize cost-performance" },
  { value: "cooperative", label: "Cooperative", description: "Build provider relationships" },
  { value: "greedy", label: "Greedy", description: "Take best immediate offer" },
];

export default function OrchestrationPage() {
  const router = useRouter();
  const {
    sessionId,
    workload,
    characterization,
    decomposition,
    providers,
    offers,
    negotiationRound,
    negotiationStrategy,
    plans,
    serverPhase,
    setProviders,
    setOffers,
    setNegotiationRound,
    setNegotiationStrategy,
    setPlans,
    setSelectedPlanId,
    setPhase,
    syncFromServerState,
  } = useAppStore();

  const [isNegotiating, setIsNegotiating] = useState(false);
  const [isGeneratingPlans, setIsGeneratingPlans] = useState(false);
  const [negotiationLog, setNegotiationLog] = useState<{ time: string; message: string }[]>([]);
  const [currentPhase, setCurrentPhase] = useState<"characterization" | "negotiation" | "planning">("characterization");

  const addLog = useCallback((message: string) => {
    setNegotiationLog((prev) => [
      ...prev,
      { time: new Date().toLocaleTimeString(), message },
    ]);
  }, []);

  const handleStateUpdate = useCallback(
    (state: { phase?: string; providers?: any[]; negotiation?: { offers?: any[] }; decomposition?: any; plans?: any[] }) => {
      syncFromServerState({
        phase: state.phase,
        providers: state.providers,
        offers: state.negotiation?.offers,
        decomposition: state.decomposition,
        plans: state.plans,
      });
    },
    [syncFromServerState]
  );

  const { connectionStatus, refreshState } = useOrchestrationWebSocket(
    sessionId,
    handleStateUpdate
  );
  const { setError } = useErrorStore();
  useSessionRecovery("orchestration");
  const [recommendedStrategy, setRecommendedStrategy] = useState<string | null>(null);

  useEffect(() => {
    api.getStrategyRecommendation(workload?.workloadType).then((r) => setRecommendedStrategy(r.strategy)).catch(() => {});
  }, [workload?.workloadType]);

  useEffect(() => {
    if (!sessionId) {
      router.push("/submit");
    }
  }, [sessionId, router]);

  useEffect(() => {
    const phase = serverPhase || (decomposition ? (offers.length > 0 ? (plans.length > 0 ? "planning" : "negotiation") : "characterization") : "characterization");
    setCurrentPhase(phase === "planning" ? "planning" : phase === "negotiation" ? "negotiation" : "characterization");
  }, [serverPhase, decomposition, offers.length, plans.length]);

  const handleStartNegotiation = async () => {
    if (!sessionId) return;
    
    setIsNegotiating(true);
    addLog(`Starting negotiation with ${negotiationStrategy} strategy...`);

    try {
      const result = await api.startNegotiation(sessionId, negotiationStrategy);
      
      setOffers(result.offers || []);
      setNegotiationRound(result.round || 1);
      setCurrentPhase("negotiation");
      
      addLog(`Received ${result.offers?.length || 0} offers from providers`);
      addLog(`Negotiation round: ${result.round || 1}`);
      refreshState();
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      addLog(`Error: ${msg}`);
      setError(msg);
    } finally {
      setIsNegotiating(false);
    }
  };

  const handleGeneratePlans = async () => {
    if (!sessionId) return;

    setIsGeneratingPlans(true);
    addLog("Generating execution plans...");

    try {
      const result = await api.generatePlans(sessionId);
      const normalizedPlans = (result.plans || []).map((p: any) => ({
        ...p,
        plan_type: p.plan_type ?? p.strategy ?? "balanced",
        total_cost_usd: p.cost ?? p.total_cost_usd ?? 0,
        total_duration_hours: p.duration ?? p.total_duration_hours ?? 0,
        optimization_score: p.score ?? p.optimization_score ?? 0.5,
        reliability_score: p.reliability ?? p.reliability_score ?? 0.9,
      }));
      setPlans(normalizedPlans);
      setCurrentPhase("planning");
      
      addLog(`Generated ${result.plans?.length || 0} execution plans`);
      refreshState();
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      addLog(`Error: ${msg}`);
      setError(msg);
    } finally {
      setIsGeneratingPlans(false);
    }
  };

  const handleSelectPlan = (planId: string) => {
    setSelectedPlanId(planId);
    setPhase("approval");
    router.push("/approval");
  };

  const formatPrice = (price: number | undefined | null) =>
    price != null ? `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="min-h-screen py-8 px-6">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <Link href="/submit" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Submission
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Server className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">ComputeExchange</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-start justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Marketplace Orchestration</h1>
            <p className="text-slate-400">
              Multi-agent negotiation and plan generation in progress
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={`gap-1.5 ${
                connectionStatus === "connected"
                  ? "border-green-500/30 text-green-400 bg-green-500/10"
                  : connectionStatus === "connecting"
                  ? "border-amber-500/30 text-amber-400 bg-amber-500/10"
                  : "border-slate-500/30 text-slate-500"
              }`}
            >
              {connectionStatus === "connected" ? (
                <Wifi className="w-3.5 h-3.5" />
              ) : connectionStatus === "connecting" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <WifiOff className="w-3.5 h-3.5" />
              )}
              <span className="text-xs font-medium">
                {connectionStatus === "connected"
                  ? "Live"
                  : connectionStatus === "connecting"
                  ? "Connecting..."
                  : "Offline"}
              </span>
            </Badge>
          </div>
        </motion.div>

        {/* Phase Progress */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <Card className="bg-slate-900/80 border-white/10">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                {[
                  { id: "characterization", label: "Characterization", icon: Brain },
                  { id: "negotiation", label: "Negotiation", icon: MessageSquare },
                  { id: "planning", label: "Planning", icon: Target },
                ].map((phase, i) => (
                  <div key={phase.id} className="flex items-center">
                    <div
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                        currentPhase === phase.id
                          ? "bg-blue-500/20 text-blue-400"
                          : i < ["characterization", "negotiation", "planning"].indexOf(currentPhase)
                          ? "text-green-400"
                          : "text-slate-500"
                      }`}
                    >
                      {i < ["characterization", "negotiation", "planning"].indexOf(currentPhase) ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <phase.icon className="w-5 h-5" />
                      )}
                      <span className="font-medium">{phase.label}</span>
                    </div>
                    {i < 2 && (
                      <ArrowRight className="w-5 h-5 text-slate-600 mx-4" />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Workload Characterization */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-400" />
                    Workload Decomposition
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {decomposition?.stages?.map((stage: any, i: number) => (
                    <div
                      key={stage.id || i}
                      className="p-3 rounded-lg bg-slate-800/50 border border-white/5"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white font-medium text-sm">{stage.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {stage.stage_type}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Clock className="w-3 h-3" />
                        {stage.estimated_duration_hours?.toFixed(1)}h
                        <span className="mx-1">•</span>
                        {stage.required_resource_types?.join(", ")}
                      </div>
                    </div>
                  )) || (
                    <div className="text-slate-500 text-sm">Loading decomposition...</div>
                  )}
                  
                  {decomposition && (
                    <div className="pt-4 border-t border-white/10 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Total Estimated Time</span>
                        <span className="text-white">{decomposition.total_estimated_hours?.toFixed(1)}h</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Critical Path</span>
                        <span className="text-white">{decomposition.critical_path_hours?.toFixed(1)}h</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Parallelism Factor</span>
                        <span className="text-white">{decomposition.parallelism_factor?.toFixed(2)}x</span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Negotiation Strategy */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    Negotiation Strategy
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {recommendedStrategy && (
                    <p className="text-xs text-slate-400 mb-2">
                      Recommended: <span className="text-blue-400 capitalize">{recommendedStrategy}</span>
                    </p>
                  )}
                  <Select
                    value={negotiationStrategy}
                    onValueChange={setNegotiationStrategy}
                  >
                    <SelectTrigger className="bg-slate-800/50 border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {negotiationStrategies.map((strategy) => (
                        <SelectItem key={strategy.value} value={strategy.value}>
                          <div>
                            <div className="font-medium">{strategy.label}</div>
                            <div className="text-xs text-slate-400">{strategy.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500"
                    onClick={handleStartNegotiation}
                    disabled={isNegotiating}
                  >
                    {isNegotiating ? (
                      <>
                        <Activity className="w-4 h-4 mr-2 animate-pulse" />
                        Negotiating...
                      </>
                    ) : (
                      <>
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Start Negotiation
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Center Column - Offers & Negotiation */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Users className="w-5 h-5 text-green-400" />
                      Provider Offers
                    </div>
                    {negotiationRound > 0 && (
                      <Badge className="bg-blue-500/20 text-blue-400">
                        Round {negotiationRound}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <AnimatePresence>
                    {offers.length > 0 ? (
                      offers.map((offer: any, i: number) => (
                        <motion.div
                          key={offer.id || i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                          className="p-4 rounded-lg bg-slate-800/50 border border-white/5 hover:border-blue-500/30 transition-colors"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="text-white font-semibold">{getProviderDisplayName(offer)}</h4>
                              <p className="text-xs text-slate-500">{offer.provider_id}</p>
                            </div>
                            {offer.is_spot && (
                              <Badge className="bg-yellow-500/20 text-yellow-400 text-xs">
                                Spot
                              </Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                            <div className="flex items-center gap-2">
                              <DollarSign className="w-4 h-4 text-green-400" />
                              <span className="text-white font-medium">
                                {formatPrice(offer.quoted_price_usd)}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock className="w-4 h-4 text-blue-400" />
                              <span className="text-white">
                                {offer.quoted_duration_hours?.toFixed(1)}h
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <div className="flex items-center gap-1">
                              <Shield className="w-3 h-3" />
                              {(offer.reliability_estimate * 100).toFixed(1)}%
                            </div>
                            <div className="flex items-center gap-1">
                              <Leaf className="w-3 h-3" />
                              {offer.carbon_footprint_kg?.toFixed(1)} kg CO2
                            </div>
                          </div>
                        </motion.div>
                      ))
                    ) : isNegotiating ? (
                      <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                          <div
                            key={i}
                            className="h-20 rounded-lg bg-slate-800/50 animate-pulse border border-white/5"
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>Start negotiation to receive offers</p>
                      </div>
                    )}
                  </AnimatePresence>

                  {offers.length > 0 && (
                    <Button
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500"
                      onClick={handleGeneratePlans}
                      disabled={isGeneratingPlans}
                    >
                      {isGeneratingPlans ? (
                        <>
                          <Activity className="w-4 h-4 mr-2 animate-pulse" />
                          Generating Plans...
                        </>
                      ) : (
                        <>
                          <Target className="w-4 h-4 mr-2" />
                          Generate Execution Plans
                        </>
                      )}
                    </Button>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Negotiation Log */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-sm">
                    <Activity className="w-4 h-4 text-blue-400" />
                    Activity Log
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-32 overflow-y-auto space-y-1 font-mono text-xs">
                    {negotiationLog.map((log, i) => (
                      <div key={i} className="text-slate-400">
                        <span className="text-slate-600">[{log.time}]</span> {log.message}
                      </div>
                    ))}
                    {negotiationLog.length === 0 && (
                      <div className="text-slate-600">Waiting for activity...</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Right Column - Plans */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-pink-400" />
                    Execution Plans
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <AnimatePresence>
                    {plans.length > 0 ? (
                      plans.map((plan: any, i: number) => (
                        <motion.div
                          key={plan.id || i}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.1 }}
                          className="p-4 rounded-lg bg-slate-800/50 border border-white/5 hover:border-blue-500/50 transition-colors cursor-pointer"
                          onClick={() => handleSelectPlan(plan.id)}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <Badge
                              className={`${
                                plan.plan_type === "cheapest"
                                  ? "bg-green-500/20 text-green-400"
                                  : plan.plan_type === "fastest"
                                  ? "bg-blue-500/20 text-blue-400"
                                  : plan.plan_type === "greenest"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : "bg-purple-500/20 text-purple-400"
                              }`}
                            >
                              {(() => {
                                const t = plan.plan_type ?? plan.strategy ?? "balanced";
                                const s = String(t);
                                return s.charAt(0).toUpperCase() + s.slice(1);
                              })()}
                            </Badge>
                            <div className="text-xs text-slate-500">
                              Score: {((plan.optimization_score ?? 0.5) * 100).toFixed(0)}%
                            </div>
                          </div>

                          <div className="space-y-2 mb-3">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400 text-sm">Cost</span>
                              <span className="text-white font-semibold">
                                {formatPrice(plan.total_cost_usd)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400 text-sm">Duration</span>
                              <span className="text-white">
                                {(plan.total_duration_hours ?? 0).toFixed(1)}h
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400 text-sm">Reliability</span>
                              <span className="text-white">
                                {((plan.reliability_score ?? 0.9) * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          <Progress
                            value={(plan.optimization_score ?? 0.5) * 100}
                            className="h-1"
                          />
                        </motion.div>
                      ))
                    ) : isGeneratingPlans ? (
                      <div className="space-y-3">
                        {[1, 2, 3, 4].map((i) => (
                          <div
                            key={i}
                            className="h-24 rounded-lg bg-slate-800/50 animate-pulse border border-white/5"
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>Generate plans after negotiation</p>
                      </div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

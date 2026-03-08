"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Server,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  DollarSign,
  Clock,
  Shield,
  Leaf,
  Cpu,
  Users,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { useAppStore } from "@/lib/store";
import { api } from "@/lib/api";
import { useErrorStore } from "@/lib/error-store";
import { useSessionRecovery } from "@/hooks/useSessionRecovery";

export default function ApprovalPage() {
  const router = useRouter();
  const {
    sessionId,
    plans,
    selectedPlanId,
    workload,
    setExecution,
    setPhase,
    setEpisodeReward,
  } = useAppStore();

  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [feedback, setFeedback] = useState("");
  const { setError } = useErrorStore();
  useSessionRecovery("approval");

  const selectedPlan = plans.find((p: any) => p.id === selectedPlanId);

  useEffect(() => {
    if (!sessionId || !selectedPlanId) {
      router.push("/orchestration");
    }
  }, [sessionId, selectedPlanId, router]);

  const handleApprove = async () => {
    if (!sessionId || !selectedPlanId) return;
    
    setIsApproving(true);
    try {
      // Submit for approval first
      await api.submitForApproval(sessionId, selectedPlanId, "Human approved plan");
      
      // Then approve
      await api.approvePlan(sessionId, selectedPlanId, "approve");
      
      // Start execution
      const execResult = await api.startExecution(sessionId, selectedPlanId);
      setExecution(execResult.execution);
      
      // Finalize
      const finalResult = await api.finalizeEpisode(sessionId);
      setEpisodeReward(finalResult.total_reward, finalResult.reward_breakdown);
      
      setPhase("execution");
      router.push("/execution");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Approval failed");
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!sessionId || !selectedPlanId) return;
    
    setIsRejecting(true);
    try {
      await api.submitForApproval(sessionId, selectedPlanId, "");
      await api.approvePlan(sessionId, selectedPlanId, "reject", feedback || "Plan rejected by human");
      setPhase("orchestration");
      router.push("/orchestration");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Rejection failed");
    } finally {
      setIsRejecting(false);
    }
  };

  if (!selectedPlan) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400">Loading plan...</div>
      </div>
    );
  }

  const formatPrice = (price: number) =>
    `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const savings = workload.budgetUsd - selectedPlan.total_cost_usd;
  const savingsPercent = (savings / workload.budgetUsd) * 100;
  const withinBudget = selectedPlan.total_cost_usd <= workload.budgetUsd;
  const withinDeadline = selectedPlan.total_duration_hours <= workload.deadlineHours;

  return (
    <div className="min-h-screen py-8 px-6">
      {/* Navigation */}
      <nav className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <Link href="/orchestration" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Orchestration
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Server className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">ComputeExchange</span>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Plan Approval Required</h1>
              <p className="text-slate-400">Review the execution plan and approve or request changes</p>
            </div>
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Plan Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Plan Summary */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white">Execution Plan</CardTitle>
                      <CardDescription>
                        {selectedPlan.plan_type?.charAt(0).toUpperCase() + selectedPlan.plan_type?.slice(1)} optimization strategy
                      </CardDescription>
                    </div>
                    <Badge
                      className={`${
                        selectedPlan.plan_type === "cheapest"
                          ? "bg-green-500/20 text-green-400"
                          : selectedPlan.plan_type === "fastest"
                          ? "bg-blue-500/20 text-blue-400"
                          : selectedPlan.plan_type === "greenest"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-purple-500/20 text-purple-400"
                      }`}
                    >
                      {selectedPlan.plan_type}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-4 gap-6">
                    <div className="text-center p-4 rounded-lg bg-slate-800/50">
                      <DollarSign className="w-6 h-6 text-green-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-white mb-1">
                        {formatPrice(selectedPlan.total_cost_usd)}
                      </div>
                      <div className="text-xs text-slate-500">Total Cost</div>
                      {withinBudget && (
                        <Badge className="mt-2 bg-green-500/20 text-green-400 text-xs">
                          {savingsPercent.toFixed(0)}% under budget
                        </Badge>
                      )}
                    </div>
                    
                    <div className="text-center p-4 rounded-lg bg-slate-800/50">
                      <Clock className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-white mb-1">
                        {selectedPlan.total_duration_hours?.toFixed(1)}h
                      </div>
                      <div className="text-xs text-slate-500">Duration</div>
                      {withinDeadline && (
                        <Badge className="mt-2 bg-blue-500/20 text-blue-400 text-xs">
                          Within deadline
                        </Badge>
                      )}
                    </div>
                    
                    <div className="text-center p-4 rounded-lg bg-slate-800/50">
                      <Shield className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-white mb-1">
                        {(selectedPlan.reliability_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-slate-500">Reliability</div>
                    </div>
                    
                    <div className="text-center p-4 rounded-lg bg-slate-800/50">
                      <Leaf className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-white mb-1">
                        {selectedPlan.carbon_footprint_kg?.toFixed(1) || "N/A"}
                      </div>
                      <div className="text-xs text-slate-500">kg CO2</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Resource Allocations */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-blue-400" />
                    Resource Allocations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {selectedPlan.allocations?.map((alloc: any, i: number) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-white/5"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                            <Cpu className="w-5 h-5 text-blue-400" />
                          </div>
                          <div>
                            <div className="text-white font-medium">Stage: {alloc.stage_id?.slice(0, 8)}</div>
                            <div className="text-xs text-slate-400">
                              Provider: {alloc.provider_name}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-medium">
                            {formatPrice(alloc.estimated_cost_usd)}
                          </div>
                          <div className="text-xs text-slate-400">
                            {alloc.estimated_duration_hours?.toFixed(1)}h • {alloc.resource_type}
                            {alloc.is_spot && (
                              <Badge className="ml-2 bg-yellow-500/20 text-yellow-400 text-xs">
                                Spot
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    )) || (
                      <div className="text-slate-500 text-center py-4">
                        No allocations available
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Risks & Assumptions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                    Risks & Assumptions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedPlan.risks?.length > 0 ? (
                      selectedPlan.risks.map((risk: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-sm">
                          <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                          <span className="text-slate-300">{risk}</span>
                        </div>
                      ))
                    ) : (
                      <div className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-300">No significant risks identified</span>
                      </div>
                    )}
                    
                    <Separator className="bg-white/10" />
                    
                    {selectedPlan.assumptions?.length > 0 ? (
                      selectedPlan.assumptions.map((assumption: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-sm">
                          <MessageSquare className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                          <span className="text-slate-300">{assumption}</span>
                        </div>
                      ))
                    ) : (
                      <div className="flex items-start gap-2 text-sm">
                        <MessageSquare className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-300">Standard market conditions assumed</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Right Column - Actions */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card className="bg-slate-900/80 border-white/10 sticky top-8">
                <CardHeader>
                  <CardTitle className="text-white">Your Decision</CardTitle>
                  <CardDescription>
                    Review the plan details and make your decision
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Compliance Checks */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      {withinBudget ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className={withinBudget ? "text-slate-300" : "text-red-400"}>
                        {withinBudget ? "Within budget" : "Over budget"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      {withinDeadline ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className={withinDeadline ? "text-slate-300" : "text-red-400"}>
                        {withinDeadline ? "Meets deadline" : "Exceeds deadline"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-slate-300">Reliability threshold met</span>
                    </div>
                  </div>

                  <Separator className="bg-white/10" />

                  {/* Optimization Score */}
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-400">Overall Score</span>
                      <span className="text-white font-medium">
                        {(selectedPlan.optimization_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={selectedPlan.optimization_score * 100} className="h-2" />
                  </div>

                  <Separator className="bg-white/10" />

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    <Button
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500"
                      size="lg"
                      onClick={handleApprove}
                      disabled={isApproving}
                    >
                      {isApproving ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Approving...
                        </>
                      ) : (
                        <>
                          <ThumbsUp className="w-4 h-4 mr-2" />
                          Approve & Execute
                        </>
                      )}
                    </Button>

                    <Button
                      variant="outline"
                      className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10"
                      onClick={handleReject}
                      disabled={isRejecting}
                    >
                      {isRejecting ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Rejecting...
                        </>
                      ) : (
                        <>
                          <ThumbsDown className="w-4 h-4 mr-2" />
                          Reject & Replan
                        </>
                      )}
                    </Button>
                  </div>

                  <p className="text-xs text-slate-500 text-center">
                    Your decision will be recorded as a training signal
                    for improving future plan generation.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

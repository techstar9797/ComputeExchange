"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Server,
  ArrowRight,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Activity,
  TrendingUp,
  TrendingDown,
  Award,
  BarChart3,
  Zap,
  Target,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { useAppStore } from "@/lib/store";
import { useSessionRecovery } from "@/hooks/useSessionRecovery";

export default function ExecutionPage() {
  const router = useRouter();
  const {
    sessionId,
    execution,
    episodeReward,
    rewardBreakdown,
    workload,
    plans,
    selectedPlanId,
    reset,
  } = useAppStore();

  const selectedPlan = plans.find((p: any) => p.id === selectedPlanId);
  useSessionRecovery("execution");

  useEffect(() => {
    if (!sessionId || !execution) {
      router.push("/");
    }
  }, [sessionId, execution, router]);

  const handleNewWorkload = () => {
    reset();
    router.push("/submit");
  };

  const handleViewAnalytics = () => {
    router.push("/analytics");
  };

  if (!execution || !selectedPlan) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400">Loading execution results...</div>
      </div>
    );
  }

  const formatPrice = (price: number) =>
    `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const isSuccess = execution.status === "completed";
  const costVariance = execution.actual_total_cost_usd - execution.predicted_cost_usd;
  const costVariancePercent = (costVariance / execution.predicted_cost_usd) * 100;
  const durationVariance = execution.actual_total_duration_hours - execution.predicted_duration_hours;
  const durationVariancePercent = (durationVariance / execution.predicted_duration_hours) * 100;
  
  const slaMetCost = execution.actual_total_cost_usd <= workload.budgetUsd;
  const slaMetTime = execution.actual_total_duration_hours <= workload.deadlineHours;
  const slaMet = slaMetCost && slaMetTime;

  return (
    <div className="min-h-screen py-8 px-6">
      {/* Navigation */}
      <nav className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Server className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">ComputeExchange</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/analytics" className="text-slate-400 hover:text-white transition-colors">
              Analytics
            </Link>
            <Button onClick={handleNewWorkload}>
              New Workload
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <div className={`w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center ${
            isSuccess ? "bg-green-500/20" : "bg-red-500/20"
          }`}>
            {isSuccess ? (
              <CheckCircle className="w-10 h-10 text-green-400" />
            ) : (
              <XCircle className="w-10 h-10 text-red-400" />
            )}
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            {isSuccess ? "Execution Complete" : "Execution Failed"}
          </h1>
          <p className="text-slate-400">
            Episode finished. Review your results and reward breakdown.
          </p>
        </motion.div>

        {/* Reward Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <Card className={`border-2 ${
            episodeReward > 0
              ? "bg-green-500/10 border-green-500/30"
              : episodeReward < 0
              ? "bg-red-500/10 border-red-500/30"
              : "bg-slate-900/80 border-white/10"
          }`}>
            <CardContent className="py-8">
              <div className="text-center">
                <Award className={`w-12 h-12 mx-auto mb-4 ${
                  episodeReward > 0 ? "text-green-400" : episodeReward < 0 ? "text-red-400" : "text-slate-400"
                }`} />
                <div className="text-5xl font-bold text-white mb-2">
                  {episodeReward > 0 ? "+" : ""}{episodeReward.toFixed(4)}
                </div>
                <div className="text-slate-400">Episode Reward</div>
                {slaMet && (
                  <Badge className="mt-4 bg-green-500/20 text-green-400">
                    SLA Achieved
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Actual vs Predicted */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="bg-slate-900/80 border-white/10">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-400" />
                  Actual vs Predicted
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Cost Comparison */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-400">Cost</span>
                    <div className="flex items-center gap-2">
                      {costVariance <= 0 ? (
                        <TrendingDown className="w-4 h-4 text-green-400" />
                      ) : (
                        <TrendingUp className="w-4 h-4 text-red-400" />
                      )}
                      <span className={costVariance <= 0 ? "text-green-400" : "text-red-400"}>
                        {costVariancePercent > 0 ? "+" : ""}{costVariancePercent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-500 mb-1">Predicted</div>
                      <div className="text-white font-semibold">{formatPrice(execution.predicted_cost_usd)}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-500 mb-1">Actual</div>
                      <div className="text-white font-semibold">{formatPrice(execution.actual_total_cost_usd)}</div>
                    </div>
                  </div>
                </div>

                {/* Duration Comparison */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-400">Duration</span>
                    <div className="flex items-center gap-2">
                      {durationVariance <= 0 ? (
                        <TrendingDown className="w-4 h-4 text-green-400" />
                      ) : (
                        <TrendingUp className="w-4 h-4 text-red-400" />
                      )}
                      <span className={durationVariance <= 0 ? "text-green-400" : "text-red-400"}>
                        {durationVariancePercent > 0 ? "+" : ""}{durationVariancePercent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-500 mb-1">Predicted</div>
                      <div className="text-white font-semibold">{execution.predicted_duration_hours.toFixed(1)}h</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-500 mb-1">Actual</div>
                      <div className="text-white font-semibold">{execution.actual_total_duration_hours.toFixed(1)}h</div>
                    </div>
                  </div>
                </div>

                {/* Prediction Accuracy */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-slate-400">Prediction Accuracy</span>
                    <span className="text-white">
                      {((1 - (Math.abs(execution.prediction_error_cost) + Math.abs(execution.prediction_error_duration)) / 2) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={(1 - (Math.abs(execution.prediction_error_cost) + Math.abs(execution.prediction_error_duration)) / 2) * 100} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Reward Breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="bg-slate-900/80 border-white/10">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                  Reward Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(rewardBreakdown).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}</span>
                      <span className={typeof value === "number" && value >= 0.5 ? "text-green-400" : "text-white"}>
                        {typeof value === "number" ? value.toFixed(3) : value}
                      </span>
                    </div>
                    {typeof value === "number" && value <= 1 && value >= 0 && (
                      <Progress value={value * 100} className="h-1" />
                    )}
                  </div>
                ))}

                {Object.keys(rewardBreakdown).length === 0 && (
                  <div className="text-slate-500 text-center py-4">
                    No breakdown available
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Stage Results */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <Card className="bg-slate-900/80 border-white/10">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-400" />
                Execution Stages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {execution.stages?.map((stage: any, i: number) => (
                  <div
                    key={i}
                    className={`p-4 rounded-lg border ${
                      stage.status === "completed"
                        ? "bg-green-500/10 border-green-500/30"
                        : stage.status === "failed"
                        ? "bg-red-500/10 border-red-500/30"
                        : "bg-slate-800/50 border-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium text-sm">
                        Stage {i + 1}
                      </span>
                      {stage.status === "completed" ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : stage.status === "failed" ? (
                        <XCircle className="w-4 h-4 text-red-400" />
                      ) : (
                        <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                      )}
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Cost</span>
                        <span className="text-slate-300">{formatPrice(stage.actual_cost_usd)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Duration</span>
                        <span className="text-slate-300">{stage.actual_duration_hours?.toFixed(2)}h</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Utilization</span>
                        <span className="text-slate-300">{stage.utilization_percent?.toFixed(0)}%</span>
                      </div>
                    </div>
                    {stage.error_message && (
                      <div className="mt-2 text-xs text-red-400 truncate">
                        {stage.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center gap-4"
        >
          <Button
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500"
            onClick={handleNewWorkload}
          >
            <Zap className="w-4 h-4 mr-2" />
            Submit New Workload
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
            onClick={handleViewAnalytics}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            View Analytics
          </Button>
        </motion.div>
      </div>
    </div>
  );
}

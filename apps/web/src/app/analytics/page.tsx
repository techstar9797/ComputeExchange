"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Server,
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Award,
  BarChart3,
  PieChart,
  Activity,
  Target,
  DollarSign,
  Clock,
  Users,
  Zap,
  Brain,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { useErrorStore } from "@/lib/error-store";

interface Metrics {
  total_episodes: number;
  avg_reward: number;
  avg_cost_savings: number;
  avg_time_savings: number;
  sla_success_rate: number;
  strategy_performance: Record<string, any>;
  provider_stats: Record<string, any>;
}

interface Episode {
  episode_id: string;
  workload_id: string;
  workload_type: string;
  negotiation_strategy: string;
  predicted_cost: number;
  actual_cost: number;
  predicted_duration: number;
  actual_duration: number;
  sla_met: boolean;
  total_reward: number;
  timestamp: string;
}

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [insights, setInsights] = useState<{
    recommended_strategy: string;
    confidence: number;
    reasoning: string;
    alternative?: string;
    avg_reward_trend: string;
    best_workload_type: string | null;
    tips: string[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { setError } = useErrorStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [metricsData, historyData, insightsData] = await Promise.all([
        api.getAnalytics(),
        api.getEpisodeHistory(20),
        api.getLearningInsights().catch(() => null),
      ]);
      setMetrics(metricsData);
      setEpisodes(historyData.episodes || []);
      setInsights(insightsData);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to load analytics");
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price: number) =>
    `$${price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div className="min-h-screen py-8 px-6">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
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
          className="mb-8 flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics & Learning</h1>
            <p className="text-slate-400">
              Track performance, analyze strategies, and see how the system learns over time
            </p>
          </div>
          <Button
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
            onClick={loadData}
            disabled={isLoading}
          >
            {isLoading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Refresh
          </Button>
        </motion.div>

        {/* Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <Card className="bg-slate-900/80 border-white/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Episodes</p>
                  <p className="text-3xl font-bold text-white">
                    {metrics?.total_episodes || 0}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/80 border-white/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Avg Reward</p>
                  <p className={`text-3xl font-bold ${(metrics?.avg_reward || 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {(metrics?.avg_reward || 0).toFixed(3)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <Award className="w-6 h-6 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/80 border-white/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Avg Cost Savings</p>
                  <p className="text-3xl font-bold text-white">
                    {formatPercent(metrics?.avg_cost_savings || 0)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/80 border-white/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">SLA Success Rate</p>
                  <p className="text-3xl font-bold text-white">
                    {formatPercent(metrics?.sla_success_rate || 0)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                  <Target className="w-6 h-6 text-yellow-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Tabs defaultValue="history" className="space-y-6">
            <TabsList className="bg-slate-800/50 border border-white/10">
              <TabsTrigger value="history">Episode History</TabsTrigger>
              <TabsTrigger value="strategies">Strategy Performance</TabsTrigger>
              <TabsTrigger value="learning">Learning Progress</TabsTrigger>
            </TabsList>

            {/* Episode History */}
            <TabsContent value="history">
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-400" />
                    Recent Episodes
                  </CardTitle>
                  <CardDescription>
                    History of workload executions and their outcomes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {episodes.length > 0 ? (
                    <div className="space-y-3">
                      {episodes.map((episode, i) => (
                        <div
                          key={episode.episode_id || i}
                          className={`p-4 rounded-lg border ${
                            episode.sla_met
                              ? "bg-green-500/5 border-green-500/20"
                              : "bg-red-500/5 border-red-500/20"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <Badge variant="outline" className="text-xs">
                                {episode.workload_type?.replace(/_/g, " ")}
                              </Badge>
                              <Badge
                                className={`text-xs ${
                                  episode.negotiation_strategy === "balanced"
                                    ? "bg-purple-500/20 text-purple-400"
                                    : episode.negotiation_strategy === "aggressive"
                                    ? "bg-red-500/20 text-red-400"
                                    : "bg-blue-500/20 text-blue-400"
                                }`}
                              >
                                {episode.negotiation_strategy}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-medium ${
                                episode.total_reward >= 0 ? "text-green-400" : "text-red-400"
                              }`}>
                                {episode.total_reward >= 0 ? "+" : ""}{episode.total_reward.toFixed(3)}
                              </span>
                              {episode.sla_met ? (
                                <Badge className="bg-green-500/20 text-green-400 text-xs">
                                  SLA Met
                                </Badge>
                              ) : (
                                <Badge className="bg-red-500/20 text-red-400 text-xs">
                                  SLA Missed
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-slate-500">Predicted Cost</span>
                              <div className="text-white">{formatPrice(episode.predicted_cost)}</div>
                            </div>
                            <div>
                              <span className="text-slate-500">Actual Cost</span>
                              <div className="text-white">{formatPrice(episode.actual_cost)}</div>
                            </div>
                            <div>
                              <span className="text-slate-500">Pred. Duration</span>
                              <div className="text-white">{episode.predicted_duration.toFixed(1)}h</div>
                            </div>
                            <div>
                              <span className="text-slate-500">Actual Duration</span>
                              <div className="text-white">{episode.actual_duration.toFixed(1)}h</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No episodes recorded yet</p>
                      <p className="text-sm">Submit workloads to see history</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Strategy Performance */}
            <TabsContent value="strategies">
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-400" />
                    Strategy Performance
                  </CardTitle>
                  <CardDescription>
                    Compare how different negotiation strategies perform
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {metrics?.strategy_performance && Object.keys(metrics.strategy_performance).length > 0 ? (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {Object.entries(metrics.strategy_performance).map(([strategy, data]: [string, any]) => (
                        <div
                          key={strategy}
                          className="p-4 rounded-lg bg-slate-800/50 border border-white/5"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="text-white font-semibold capitalize">{strategy}</h4>
                            <Badge variant="outline" className="text-xs">
                              {data.count} runs
                            </Badge>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-400">Avg Reward</span>
                                <span className={data.avg_reward >= 0 ? "text-green-400" : "text-red-400"}>
                                  {data.avg_reward?.toFixed(3)}
                                </span>
                              </div>
                              <Progress value={Math.max(0, (data.avg_reward + 1) * 50)} className="h-1" />
                            </div>
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-400">SLA Rate</span>
                                <span className="text-white">{formatPercent(data.sla_rate || 0)}</span>
                              </div>
                              <Progress value={(data.sla_rate || 0) * 100} className="h-1" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No strategy data available</p>
                      <p className="text-sm">Run multiple episodes to compare strategies</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Learning Progress */}
            <TabsContent value="learning">
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="bg-slate-900/80 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-green-400" />
                      Learning Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-4 rounded-lg bg-slate-800/50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400">Reward Trend</span>
                        <span className={`flex items-center gap-1 ${
                          insights?.avg_reward_trend === "improving" ? "text-green-400" :
                          insights?.avg_reward_trend === "declining" ? "text-red-400" : "text-slate-400"
                        }`}>
                          {insights?.avg_reward_trend === "improving" && <TrendingUp className="w-4 h-4" />}
                          {insights?.avg_reward_trend === "declining" && <TrendingDown className="w-4 h-4" />}
                          {insights?.avg_reward_trend?.charAt(0).toUpperCase() || "Calibrating"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        {insights ? `Based on ${episodes.length} episodes. ${insights.reasoning}` : "Run episodes to see trends"}
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400">Recommended Strategy</span>
                        <Badge className="bg-blue-500/20 text-blue-400 capitalize">
                          {insights?.recommended_strategy || "balanced"}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mb-2">
                        Confidence: {insights ? `${(insights.confidence * 100).toFixed(0)}%` : "N/A"}
                      </p>
                      {insights?.alternative && (
                        <p className="text-xs text-slate-400">
                          Alternative: {insights.alternative}
                        </p>
                      )}
                    </div>

                    {insights?.tips && insights.tips.length > 0 && (
                      <div className="p-4 rounded-lg bg-slate-800/50">
                        <div className="text-slate-400 text-sm font-medium mb-2">Tips</div>
                        <ul className="text-xs text-slate-500 space-y-1">
                          {insights.tips.map((tip, i) => (
                            <li key={i}>• {tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="bg-slate-900/80 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Zap className="w-5 h-5 text-yellow-400" />
                      Training Ready
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-slate-400">
                      This environment exports trajectories compatible with:
                    </p>

                    <div className="space-y-2">
                      <div className="flex items-center gap-2 p-2 rounded bg-slate-800/50">
                        <div className="w-2 h-2 rounded-full bg-green-400" />
                        <span className="text-white text-sm">TorchForge GRPO</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded bg-slate-800/50">
                        <div className="w-2 h-2 rounded-full bg-green-400" />
                        <span className="text-white text-sm">HuggingFace TRL</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded bg-slate-800/50">
                        <div className="w-2 h-2 rounded-full bg-green-400" />
                        <span className="text-white text-sm">OpenEnv Training Loops</span>
                      </div>
                    </div>

                    <div className="pt-4">
                      <Button className="w-full" variant="outline">
                        Export Trajectories
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}

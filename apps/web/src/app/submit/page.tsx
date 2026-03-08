"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Server,
  ArrowLeft,
  Cpu,
  Brain,
  Database,
  Gauge,
  Zap,
  Leaf,
  Shield,
  Clock,
  DollarSign,
  MapPin,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store";
import { api } from "@/lib/api";

const workloadTypes = [
  { value: "llm_training", label: "LLM Training", icon: Brain },
  { value: "batch_inference", label: "Batch Inference", icon: Cpu },
  { value: "realtime_inference", label: "Real-time Inference", icon: Zap },
  { value: "etl_analytics", label: "ETL / Analytics", icon: Database },
  { value: "rendering_simulation", label: "Rendering / Simulation", icon: Gauge },
  { value: "multimodal_pipeline", label: "Multimodal Pipeline", icon: Brain },
];

const regions = [
  { value: "us-west-2", label: "US West (Oregon)" },
  { value: "us-east-1", label: "US East (Virginia)" },
  { value: "eu-west-1", label: "EU West (Ireland)" },
  { value: "eu-central-1", label: "EU Central (Frankfurt)" },
  { value: "ap-southeast-1", label: "Asia Pacific (Singapore)" },
  { value: "ap-northeast-1", label: "Asia Pacific (Tokyo)" },
];

const complianceOptions = [
  { value: "SOC2", label: "SOC 2" },
  { value: "ISO27001", label: "ISO 27001" },
  { value: "HIPAA", label: "HIPAA" },
  { value: "PCI-DSS", label: "PCI-DSS" },
  { value: "GDPR", label: "GDPR" },
  { value: "ISO14001", label: "ISO 14001 (Environmental)" },
];

export default function SubmitWorkloadPage() {
  const router = useRouter();
  const { workload, setWorkload, setPhase, setSessionId, setDecomposition, setCharacterization } = useAppStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedRegions, setSelectedRegions] = useState<string[]>(["us-west-2"]);
  const [selectedCompliance, setSelectedCompliance] = useState<string[]>([]);

  const totalWeight =
    workload.costWeight +
    workload.latencyWeight +
    workload.throughputWeight +
    workload.energyWeight +
    workload.reliabilityWeight;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const result = await api.submitWorkload({
        name: workload.name || `${workload.workloadType}-${Date.now()}`,
        workload_type: workload.workloadType,
        model_size_gb: workload.modelSizeGb,
        data_size_gb: workload.dataSizeGb,
        deadline_hours: workload.deadlineHours,
        budget_usd: workload.budgetUsd,
        preferred_regions: selectedRegions,
        compliance_requirements: selectedCompliance,
        cost_weight: workload.costWeight,
        latency_weight: workload.latencyWeight,
        throughput_weight: workload.throughputWeight,
        energy_weight: workload.energyWeight,
        reliability_weight: workload.reliabilityWeight,
        allow_spot_instances: workload.allowSpotInstances,
        allow_heterogeneous_plan: workload.allowHeterogeneousPlan,
        min_reliability_score: 0.95,
      });

      setSessionId(result.session_id);
      setDecomposition(result.decomposition);
      if (result.characterization && result.stages) {
        setCharacterization(result.characterization, result.stages);
      }
      setPhase("orchestration");
      router.push("/orchestration");
    } catch (error) {
      console.error("Failed to submit workload:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen py-8 px-6">
      {/* Navigation */}
      <nav className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back
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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-white mb-2">Submit Workload</h1>
          <p className="text-slate-400">
            Define your compute requirements and optimization preferences
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Workload Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-blue-400" />
                    Workload Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Workload Name</Label>
                      <Input
                        placeholder="My Training Job"
                        value={workload.name}
                        onChange={(e) => setWorkload({ name: e.target.value })}
                        className="bg-slate-800/50 border-white/10 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Workload Type</Label>
                      <Select
                        value={workload.workloadType}
                        onValueChange={(value) => setWorkload({ workloadType: value })}
                      >
                        <SelectTrigger className="bg-slate-800/50 border-white/10 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {workloadTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center gap-2">
                                <type.icon className="w-4 h-4" />
                                {type.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Model Size (GB)</Label>
                      <Input
                        type="number"
                        value={workload.modelSizeGb}
                        onChange={(e) => setWorkload({ modelSizeGb: Number(e.target.value) })}
                        className="bg-slate-800/50 border-white/10 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Data Size (GB)</Label>
                      <Input
                        type="number"
                        value={workload.dataSizeGb}
                        onChange={(e) => setWorkload({ dataSizeGb: Number(e.target.value) })}
                        className="bg-slate-800/50 border-white/10 text-white"
                      />
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Deadline (hours)
                      </Label>
                      <Input
                        type="number"
                        value={workload.deadlineHours}
                        onChange={(e) => setWorkload({ deadlineHours: Number(e.target.value) })}
                        className="bg-slate-800/50 border-white/10 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300 flex items-center gap-2">
                        <DollarSign className="w-4 h-4" />
                        Budget (USD)
                      </Label>
                      <Input
                        type="number"
                        value={workload.budgetUsd}
                        onChange={(e) => setWorkload({ budgetUsd: Number(e.target.value) })}
                        className="bg-slate-800/50 border-white/10 text-white"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Optimization Weights */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Gauge className="w-5 h-5 text-purple-400" />
                    Optimization Preferences
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {[
                    { key: "costWeight", label: "Cost", icon: DollarSign, color: "blue" },
                    { key: "latencyWeight", label: "Latency", icon: Zap, color: "yellow" },
                    { key: "throughputWeight", label: "Throughput", icon: Gauge, color: "green" },
                    { key: "energyWeight", label: "Energy Efficiency", icon: Leaf, color: "emerald" },
                    { key: "reliabilityWeight", label: "Reliability", icon: Shield, color: "purple" },
                  ].map(({ key, label, icon: Icon, color }) => (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-slate-300 flex items-center gap-2">
                          <Icon className={`w-4 h-4 text-${color}-400`} />
                          {label}
                        </Label>
                        <span className="text-slate-400 text-sm">
                          {((workload[key as keyof typeof workload] as number) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <Slider
                        value={[(workload[key as keyof typeof workload] as number) * 100]}
                        onValueChange={([value]) =>
                          setWorkload({ [key]: value / 100 })
                        }
                        max={100}
                        step={5}
                        className="cursor-pointer"
                      />
                    </div>
                  ))}
                  <div className="pt-2 text-sm text-slate-500">
                    Total: {(totalWeight * 100).toFixed(0)}%{" "}
                    {Math.abs(totalWeight - 1) > 0.01 && (
                      <span className="text-yellow-500">(will be normalized)</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Regions & Compliance */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-slate-900/80 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-green-400" />
                    Regions & Compliance
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Preferred Regions</Label>
                    <div className="flex flex-wrap gap-2">
                      {regions.map((region) => (
                        <Badge
                          key={region.value}
                          variant={selectedRegions.includes(region.value) ? "default" : "outline"}
                          className={`cursor-pointer ${
                            selectedRegions.includes(region.value)
                              ? "bg-blue-600 hover:bg-blue-500"
                              : "border-white/20 text-slate-400 hover:text-white"
                          }`}
                          onClick={() => {
                            if (selectedRegions.includes(region.value)) {
                              setSelectedRegions(selectedRegions.filter((r) => r !== region.value));
                            } else {
                              setSelectedRegions([...selectedRegions, region.value]);
                            }
                          }}
                        >
                          {region.label}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300">Compliance Requirements</Label>
                    <div className="flex flex-wrap gap-2">
                      {complianceOptions.map((comp) => (
                        <Badge
                          key={comp.value}
                          variant={selectedCompliance.includes(comp.value) ? "default" : "outline"}
                          className={`cursor-pointer ${
                            selectedCompliance.includes(comp.value)
                              ? "bg-purple-600 hover:bg-purple-500"
                              : "border-white/20 text-slate-400 hover:text-white"
                          }`}
                          onClick={() => {
                            if (selectedCompliance.includes(comp.value)) {
                              setSelectedCompliance(selectedCompliance.filter((c) => c !== comp.value));
                            } else {
                              setSelectedCompliance([...selectedCompliance, comp.value]);
                            }
                          }}
                        >
                          {comp.label}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Right Column - Summary & Actions */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card className="bg-slate-900/80 border-white/10 sticky top-8">
                <CardHeader>
                  <CardTitle className="text-white">Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Workload Type</span>
                      <span className="text-white">
                        {workloadTypes.find((t) => t.value === workload.workloadType)?.label}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Model Size</span>
                      <span className="text-white">{workload.modelSizeGb} GB</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Data Size</span>
                      <span className="text-white">{workload.dataSizeGb} GB</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Deadline</span>
                      <span className="text-white">{workload.deadlineHours} hours</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Budget</span>
                      <span className="text-white font-semibold">${workload.budgetUsd.toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="border-t border-white/10 pt-4 space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-slate-300">AI workload characterization</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-slate-300">Multi-provider negotiation</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-slate-300">Optimized execution plan</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-slate-300">Human approval workflow</span>
                    </div>
                  </div>

                  <Button
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500"
                    size="lg"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Submitting..." : "Submit Workload"}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

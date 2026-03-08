"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { 
  Cpu, 
  Zap, 
  TrendingDown, 
  Shield, 
  Globe,
  ArrowRight,
  Server,
  Brain,
  BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Orchestration",
    description: "Multi-agent system automatically characterizes workloads, negotiates with providers, and generates optimized execution plans.",
  },
  {
    icon: TrendingDown,
    title: "Cost Optimization",
    description: "Save up to 60% on compute costs through intelligent spot instance allocation and provider negotiation.",
  },
  {
    icon: Zap,
    title: "Performance Matching",
    description: "Automatically match workload stages to optimal resources - CPU, GPU, NPU, or specialized accelerators.",
  },
  {
    icon: Shield,
    title: "Human-in-the-Loop",
    description: "Full visibility and approval workflow ensures humans stay in control of critical infrastructure decisions.",
  },
];

const workflowSteps = [
  { step: "1", title: "Submit Workload", desc: "Define your compute requirements" },
  { step: "2", title: "AI Characterization", desc: "Automatic workload decomposition" },
  { step: "3", title: "Provider Negotiation", desc: "Multi-agent marketplace bidding" },
  { step: "4", title: "Plan Generation", desc: "Optimized execution plans" },
  { step: "5", title: "Human Approval", desc: "Review and approve" },
  { step: "6", title: "Execute & Learn", desc: "Run workload, improve over time" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
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
            <Link href="/submit">
              <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500">
                Submit Workload
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm mb-8">
              <Cpu className="w-4 h-4" />
              OpenEnv Multi-Agent Environment
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              The{" "}
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Marketplace
              </span>
              <br />
              for Compute Resources
            </h1>
            
            <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-10">
              AI-powered multi-agent orchestration that automatically characterizes your workloads,
              negotiates with providers, and generates optimal execution plans.
              <span className="text-white font-medium"> The Expedia for GPU compute.</span>
            </p>
            
            <div className="flex items-center justify-center gap-4">
              <Link href="/submit">
                <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-lg px-8 py-6">
                  Submit a Workload
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Link href="/demo">
                <Button size="lg" variant="outline" className="text-lg px-8 py-6 border-white/20 text-white hover:bg-white/10">
                  Watch Demo
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Animated Workflow */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-20"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-2xl blur-3xl" />
              <Card className="relative bg-slate-900/80 border-white/10 overflow-hidden">
                <CardContent className="p-8">
                  <div className="flex items-center justify-between gap-4 overflow-x-auto pb-4">
                    {workflowSteps.map((step, i) => (
                      <motion.div
                        key={step.step}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.5 + i * 0.1 }}
                        className="flex-shrink-0 flex flex-col items-center text-center min-w-[140px]"
                      >
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg mb-3">
                          {step.step}
                        </div>
                        <h3 className="text-white font-semibold text-sm mb-1">{step.title}</h3>
                        <p className="text-slate-500 text-xs">{step.desc}</p>
                        {i < workflowSteps.length - 1 && (
                          <ArrowRight className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 hidden lg:block" />
                        )}
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Intelligent Compute Orchestration
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Our multi-agent system handles the complexity of compute allocation,
              so you can focus on building.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="bg-slate-800/50 border-white/10 h-full hover:border-blue-500/50 transition-colors">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                      <feature.icon className="w-6 h-6 text-blue-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-slate-400 text-sm">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* OpenEnv Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm mb-4">
                <Globe className="w-4 h-4" />
                OpenEnv Native
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                Built for Training &<br />Agentic Workflows
              </h2>
              <p className="text-slate-400 mb-6">
                ComputeExchange is built as an OpenEnv environment with proper reset(), step(), 
                and state() APIs. Every episode generates trajectories that can be used for 
                GRPO training with TorchForge or TRL.
              </p>
              <ul className="space-y-3 text-slate-300">
                <li className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  Shaped rewards for RL post-training
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-purple-500" />
                  Episode trajectory export for offline training
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-pink-500" />
                  Multi-agent coordination benchmarks
                </li>
                <li className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  Human-in-the-loop reward signals
                </li>
              </ul>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <Card className="bg-slate-800/50 border-white/10">
                <CardContent className="p-6">
                  <pre className="text-sm text-slate-300 overflow-x-auto">
                    <code>{`from compute_market_env import ComputeMarketEnv

# Connect to environment
with ComputeMarketEnv().sync() as env:
    obs = env.reset(scenario="llm_training_7b")
    
    # Characterize workload
    obs = env.characterize_workload(workload)
    
    # Negotiate with providers  
    obs = env.request_quotes()
    
    # Generate optimized plan
    obs = env.generate_plan("balanced")
    
    # Human approval
    obs = env.approve_plan(plan_id)
    
    # Execute and learn
    result = env.execute_plan(plan_id)
    final = env.finalize_episode()
    
    print(f"Reward: {final.reward}")
    # Export trajectory for training`}</code>
                  </pre>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Card className="bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-pink-600/20 border-white/10">
              <CardContent className="p-12">
                <BarChart3 className="w-12 h-12 text-blue-400 mx-auto mb-6" />
                <h2 className="text-3xl font-bold text-white mb-4">
                  Ready to Optimize Your Compute?
                </h2>
                <p className="text-slate-400 mb-8 max-w-xl mx-auto">
                  Start orchestrating your workloads across the compute marketplace.
                  Our AI agents will find the optimal allocation for your needs.
                </p>
                <Link href="/submit">
                  <Button size="lg" className="bg-white text-slate-900 hover:bg-slate-100 text-lg px-8">
                    Get Started
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-slate-500 text-sm">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4" />
            ComputeExchange
          </div>
          <div>Built for OpenEnv Hackathon 2026</div>
        </div>
      </footer>
    </div>
  );
}

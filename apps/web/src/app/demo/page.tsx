"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Server, Brain, Users, BarChart3, CheckCircle, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const steps = [
  { icon: Server, title: "Submit Workload", desc: "Define your compute requirements, budget, and deadline." },
  { icon: Brain, title: "AI Characterization", desc: "Agents decompose your workload into executable stages." },
  { icon: Users, title: "Provider Negotiation", desc: "Nebius, AWS, Lambda Labs, CoreWeave, Google Cloud, Azure compete with offers." },
  { icon: BarChart3, title: "Execution Plans", desc: "Cheapest, fastest, balanced, and greenest plans generated." },
  { icon: CheckCircle, title: "Human Approval", desc: "Review cost, duration, and risks—approve or reject." },
  { icon: ArrowRight, title: "Execute & Learn", desc: "Run the plan; the system learns from outcomes for next time." },
];

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white">
      <nav className="border-b border-white/5 bg-slate-900/50 backdrop-blur">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors">
            <Server className="w-6 h-6" />
            <span className="font-bold text-lg">ComputeExchange</span>
          </Link>
          <Link href="/">
            <Button variant="ghost" className="text-slate-400 hover:text-white">
              Back to Home
            </Button>
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14"
        >
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Watch the Demo
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-10">
            See how AI agents characterize your workload, negotiate with cloud providers, and generate optimized execution plans in under two minutes.
          </p>
          <Link href="/submit">
            <Button
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-lg px-10 py-6"
            >
              <Play className="mr-2 w-5 h-5" />
              Start Demo
            </Button>
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-xl font-semibold text-slate-300 mb-6">What you’ll see</h2>
          <div className="space-y-4">
            {steps.map(({ icon: Icon, title, desc }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
              >
                <Card className="bg-slate-800/50 border-white/10">
                  <CardContent className="flex items-start gap-4 p-4">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{title}</h3>
                      <p className="text-sm text-slate-400">{desc}</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-14 text-center"
        >
          <Link href="/submit">
            <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
              Start Demo
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </div>
  );
}

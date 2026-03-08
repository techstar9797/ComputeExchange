"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { useErrorStore } from "@/lib/error-store";

/**
 * Recovers session state from server when we have sessionId but missing data.
 * Use on orchestration, approval, execution pages.
 */
export function useSessionRecovery(requiredPage: "orchestration" | "approval" | "execution") {
  const router = useRouter();
  const { sessionId, decomposition, plans, execution, setSessionId, restoreFromServerState } =
    useAppStore();
  const { setError } = useErrorStore();
  const [isRecovering, setIsRecovering] = useState(false);

  useEffect(() => {
    if (!sessionId) return;

    const needsRecovery =
      (requiredPage === "orchestration" && !decomposition) ||
      (requiredPage === "approval" && plans.length === 0) ||
      (requiredPage === "execution" && !execution);

    if (!needsRecovery) return;

    let cancelled = false;
    setIsRecovering(true);

    api
      .getSessionState(sessionId)
      .then((state) => {
        if (cancelled) return;
        const isEmpty =
          (state.phase === "initialization" || state.phase === "uninitialized") &&
          !state.decomposition &&
          (!state.plans || state.plans.length === 0);
        if (isEmpty) {
          setError("Session expired. Please submit a new workload.");
          setSessionId(null);
          router.push("/submit");
          return;
        }
        restoreFromServerState({
          phase: state.phase,
          decomposition: state.decomposition ?? undefined,
          offers: state.offers ?? [],
          plans: state.plans ?? [],
          execution: state.execution ?? undefined,
          episode_reward: state.episode_reward,
          selected_plan: state.selected_plan,
          workload: state.workload,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Session expired or not found");
        setSessionId(null);
        router.push("/submit");
      })
      .finally(() => {
        if (!cancelled) setIsRecovering(false);
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId, requiredPage, decomposition, plans.length, execution]);

  return { isRecovering };
}

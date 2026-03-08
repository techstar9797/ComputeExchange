"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useErrorStore } from "@/lib/error-store";

export function ErrorBanner() {
  const { error, clearError } = useErrorStore();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 8000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  return (
    <AnimatePresence>
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-xl w-[calc(100%-2rem)]"
        >
          <div className="flex items-center gap-3 p-4 rounded-lg bg-red-950/95 border border-red-500/30 shadow-lg backdrop-blur">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="flex-1 text-sm text-red-100">{error}</p>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-500/20"
              onClick={clearError}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

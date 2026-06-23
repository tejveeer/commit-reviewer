import { motion } from "framer-motion";
import type { ReactNode } from "react";

function Centered({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        {children}
      </motion.div>
    </div>
  );
}

export function LoadingState() {
  return (
    <Centered>
      <div className="flex items-center gap-2 text-stone-500 dark:text-stone-400">
        <motion.span
          className="size-3 rounded-full bg-amber-500"
          animate={{ scale: [1, 1.4, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
        />
        Loading report...
      </div>
    </Centered>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <Centered>
      <h2 className="text-lg font-bold text-amber-700 dark:text-amber-400">
        Could not load the report
      </h2>
      <p className="mt-1 max-w-md text-sm text-stone-500 dark:text-stone-400">{message}</p>
      <p className="mt-3 text-xs text-stone-400 dark:text-stone-500">
        Run <code className="font-mono text-amber-700 dark:text-amber-400">review-commits</code>{" "}
        to generate <code className="font-mono">report.json</code>.
      </p>
    </Centered>
  );
}

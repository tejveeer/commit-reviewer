import { motion } from "framer-motion";
import type { Report } from "../types";
import { ThemeToggle } from "./ThemeToggle";

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

interface HeaderProps {
  report: Report;
  dark: boolean;
  toggle: () => void;
}

export function Header({ report, dark, toggle }: HeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="mb-4 border-b border-slate-200 bg-white/95 dark:border-slate-800 dark:bg-slate-950/95"
    >
      <div className="mx-auto flex max-w-5xl items-start justify-between gap-2 px-3 py-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-teal-500" />
            <span className="size-2 rounded-full bg-coral-500" />
            <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
              Commit Reviewer
            </h1>
          </div>
          <p className="mt-0.5 truncate font-mono text-xs text-slate-500 dark:text-slate-400">
            {report.repo}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
            <span className="rounded-md border border-teal-200 bg-teal-50 px-1.5 py-0.5 font-semibold uppercase tracking-wide text-teal-700 dark:border-teal-500/30 dark:bg-teal-500/10 dark:text-teal-300">
              {report.mode}
            </span>
            <span className="rounded-md border border-coral-200 bg-coral-50 px-1.5 py-0.5 font-mono text-coral-700 dark:border-coral-500/30 dark:bg-coral-500/10 dark:text-coral-300">
              {report.model}
            </span>
            <span className="text-slate-400 dark:text-slate-500">
              {formatDate(report.generated_at)}
            </span>
          </div>
        </div>
        <ThemeToggle dark={dark} toggle={toggle} />
      </div>
    </motion.header>
  );
}

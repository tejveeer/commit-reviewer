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
      className="mb-4 border-b border-amber-300 bg-amber-100/95 dark:border-stone-800 dark:bg-stone-950/95"
    >
      <div className="mx-auto flex max-w-5xl items-start justify-between gap-2 px-3 py-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-amber-500" />
            <span className="size-2 rounded-full bg-amber-300" />
            <h1 className="text-lg font-bold tracking-tight text-stone-800 dark:text-stone-100">
              Commit Reviewer
            </h1>
          </div>
          <p className="mt-0.5 truncate font-mono text-xs text-stone-500 dark:text-stone-400">
            {report.repo}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
            <span className="rounded-md border border-amber-200 bg-amber-100/70 px-1.5 py-0.5 font-semibold uppercase tracking-wide text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
              {report.mode}
            </span>
            <span className="rounded-md border border-amber-200 bg-amber-50 px-1.5 py-0.5 font-mono text-stone-600 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-300">
              {report.model}
            </span>
            <span className="text-stone-400 dark:text-stone-500">
              {formatDate(report.generated_at)}
            </span>
          </div>
        </div>
        <ThemeToggle dark={dark} toggle={toggle} />
      </div>
    </motion.header>
  );
}

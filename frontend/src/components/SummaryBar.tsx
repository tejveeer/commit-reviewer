import { motion } from "framer-motion";
import { RATINGS, type Summary } from "../types";
import { RATING_STYLES } from "../ratings";

export function SummaryBar({ summary }: { summary: Summary }) {
  const total = summary.excellent + summary.good + summary.bad;

  return (
    <section className="mx-auto max-w-5xl px-3 py-2">
      <div className="flex items-center gap-3 text-sm">
        {RATINGS.map((rating) => (
          <div key={rating} className="flex items-center gap-1.5">
            <span className={`size-2 rounded-full ${RATING_STYLES[rating].dot}`} />
            <span className="font-semibold text-slate-900 dark:text-white">
              {summary[rating]}
            </span>
            <span className="text-slate-500 dark:text-slate-400">
              {RATING_STYLES[rating].label}
            </span>
          </div>
        ))}
        <span className="ml-auto text-xs text-slate-400 dark:text-slate-500">
          {total} commit{total === 1 ? "" : "s"}
        </span>
      </div>

      <div className="mt-1.5 flex h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        {RATINGS.map((rating) => {
          const pct = total === 0 ? 0 : (summary[rating] / total) * 100;
          return (
            <motion.div
              key={rating}
              className={RATING_STYLES[rating].bar}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          );
        })}
      </div>
    </section>
  );
}

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import type { ReviewedCommit } from "../types";
import { RatingBadge } from "./RatingBadge";

function splitMessage(message: string): { subject: string; body: string } {
  const [subject, ...rest] = message.split("\n");
  return { subject, body: rest.join("\n").trim() };
}

export function CommitRow({ commit }: { commit: ReviewedCommit }) {
  const { subject, body } = splitMessage(commit.message);
  const [open, setOpen] = useState(false);
  const expandable = body.length > 0;

  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      onClick={expandable ? () => setOpen((o) => !o) : undefined}
      className={`rounded-sm border border-slate-200 bg-white p-2 transition-colors hover:border-teal-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-teal-700 ${
        expandable ? "cursor-pointer" : ""
      }`}
    >
      <div className="flex items-start gap-2">
        <code className="mt-0.5 rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-teal-700 dark:bg-slate-800 dark:text-teal-300">
          {commit.sha.slice(0, 7)}
        </code>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="min-w-0 font-medium text-slate-900 dark:text-slate-100">
              {subject}
              {expandable && (
                <span className="ml-1.5 align-middle text-xs text-slate-400">
                  {open ? "▾" : "▸"}
                </span>
              )}
            </p>
            <RatingBadge rating={commit.rating} />
          </div>

          <AnimatePresence initial={false}>
            {open && expandable && (
              <motion.pre
                key="body"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="overflow-hidden whitespace-pre-wrap font-mono text-xs text-slate-600 dark:text-slate-400"
              >
                {body}
              </motion.pre>
            )}
          </AnimatePresence>

          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-slate-400 dark:text-slate-500">
            <span>{commit.author}</span>
          </p>

          <p className="mt-1 border-l-2 border-coral-300 pl-2 text-sm text-slate-600 dark:border-coral-500/40 dark:text-slate-300">
            {commit.reasoning}
          </p>
        </div>
      </div>
    </motion.li>
  );
}

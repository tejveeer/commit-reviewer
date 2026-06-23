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
      className={`rounded-sm border border-amber-200 bg-amber-50 p-2 transition-colors hover:border-amber-400 dark:border-stone-800 dark:bg-stone-900 dark:hover:border-amber-700 ${
        expandable ? "cursor-pointer" : ""
      }`}
    >
      <div className="flex items-start gap-2">
        <code className="mt-0.5 rounded-md bg-amber-100 px-1.5 py-0.5 font-mono text-xs text-amber-800 dark:bg-stone-800 dark:text-amber-300">
          {commit.sha.slice(0, 7)}
        </code>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="min-w-0 font-medium text-stone-800 dark:text-stone-100">
              {subject}
              {expandable && (
                <span className="ml-1.5 align-middle text-xs text-stone-400">
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
                className="overflow-hidden whitespace-pre-wrap font-mono text-xs text-stone-600 dark:text-stone-400"
              >
                {body}
              </motion.pre>
            )}
          </AnimatePresence>

          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-stone-400 dark:text-stone-500">
            <span>{commit.author}</span>
          </p>

          <p className="mt-1 border-l-2 border-amber-300 pl-2 text-sm text-stone-600 dark:border-amber-500/40 dark:text-stone-300">
            {commit.reasoning}
          </p>
        </div>
      </div>
    </motion.li>
  );
}

import { AnimatePresence, motion } from "framer-motion";
import type { ReviewedCommit } from "../types";
import { CommitRow } from "./CommitRow";

export function CommitList({ commits }: { commits: ReviewedCommit[] }) {
  if (commits.length === 0) {
    return (
      <p className="mx-auto max-w-5xl px-3 py-8 text-center text-sm text-stone-400 dark:text-stone-500">
        No commits match the current filter.
      </p>
    );
  }

  return (
    <motion.ul layout className="mx-auto flex max-w-5xl flex-col gap-1.5 px-3 pb-8">
      <AnimatePresence mode="popLayout">
        {commits.map((commit) => (
          <CommitRow key={commit.sha} commit={commit} />
        ))}
      </AnimatePresence>
    </motion.ul>
  );
}

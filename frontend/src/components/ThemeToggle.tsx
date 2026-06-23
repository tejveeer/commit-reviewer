import { motion } from "framer-motion";

export function ThemeToggle({ dark, toggle }: { dark: boolean; toggle: () => void }) {
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="group flex cursor-pointer items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-sm text-stone-600 transition-colors hover:border-amber-400 hover:text-amber-700 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 dark:hover:border-amber-500 dark:hover:text-amber-400"
    >
      <motion.span
        key={dark ? "moon" : "sun"}
        initial={{ rotate: -90, opacity: 0 }}
        animate={{ rotate: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className="text-base leading-none"
      >
        {dark ? "🌙" : "☀️"}
      </motion.span>
      <span className="hidden sm:inline">{dark ? "Dark" : "Light"}</span>
    </button>
  );
}

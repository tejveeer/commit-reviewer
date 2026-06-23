import type { Rating } from "./types";

interface RatingStyle {
  label: string;
  /** Badge: tinted background, text, and border (light + dark). */
  badge: string;
  /** Solid color for the summary proportion bar segment. */
  bar: string;
  /** Small dot color. */
  dot: string;
}

export const RATING_STYLES: Record<Rating, RatingStyle> = {
  excellent: {
    label: "Excellent",
    badge:
      "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/30",
    bar: "bg-emerald-500",
    dot: "bg-emerald-500",
  },
  good: {
    label: "Good",
    badge:
      "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/30",
    bar: "bg-amber-500",
    dot: "bg-amber-500",
  },
  bad: {
    label: "Bad",
    badge:
      "bg-red-50 text-red-700 border-red-200 dark:bg-red-500/10 dark:text-red-300 dark:border-red-500/30",
    bar: "bg-red-500",
    dot: "bg-red-500",
  },
};

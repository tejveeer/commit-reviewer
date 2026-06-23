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

/**
 * Monochromatic by intensity: excellent is the strongest amber, good is a
 * mid amber, and bad fades to a muted warm taupe (least "intense").
 */
export const RATING_STYLES: Record<Rating, RatingStyle> = {
  excellent: {
    label: "Excellent",
    badge:
      "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/40",
    bar: "bg-amber-500",
    dot: "bg-amber-500",
  },
  good: {
    label: "Good",
    badge:
      "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-400/10 dark:text-amber-200/80 dark:border-amber-400/25",
    bar: "bg-amber-300",
    dot: "bg-amber-300",
  },
  bad: {
    label: "Bad",
    badge:
      "bg-stone-100 text-stone-500 border-stone-300 dark:bg-stone-500/10 dark:text-stone-400 dark:border-stone-600/40",
    bar: "bg-stone-400",
    dot: "bg-stone-400",
  },
};

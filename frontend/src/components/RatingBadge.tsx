import type { Rating } from "../types";
import { RATING_STYLES } from "../ratings";

export function RatingBadge({ rating }: { rating: Rating }) {
  const style = RATING_STYLES[rating];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${style.badge}`}
    >
      <span className={`size-1.5 rounded-full ${style.dot}`} />
      {style.label}
    </span>
  );
}

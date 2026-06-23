import { RATINGS, type Rating } from "../types";
import { RATING_STYLES } from "../ratings";

export type RatingFilter = Rating | "all";

interface FiltersProps {
  filter: RatingFilter;
  setFilter: (filter: RatingFilter) => void;
  search: string;
  setSearch: (search: string) => void;
}

const CHIPS: RatingFilter[] = ["all", ...RATINGS];

export function Filters({ filter, setFilter, search, setSearch }: FiltersProps) {
  return (
    <section className="mx-auto flex max-w-5xl flex-wrap items-center gap-2 px-3 py-2">
      <div className="flex flex-wrap gap-1">
        {CHIPS.map((chip) => {
          const active = filter === chip;
          const label = chip === "all" ? "All" : RATING_STYLES[chip].label;
          return (
            <button
              key={chip}
              type="button"
              onClick={() => setFilter(chip)}
              className={`cursor-pointer rounded-lg border px-2 py-1 text-xs font-semibold transition-colors ${
                active
                  ? "border-amber-600 bg-amber-600 text-white"
                  : "border-amber-200 bg-amber-50 text-stone-600 hover:border-amber-400 hover:text-amber-700 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 dark:hover:border-amber-500 dark:hover:text-amber-400"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search message or SHA..."
        className="ml-auto w-full max-w-xs rounded-lg border border-amber-200 bg-amber-50 px-2 py-1 text-sm text-stone-700 outline-none transition-colors placeholder:text-stone-400 focus:border-amber-500 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-200 dark:placeholder:text-stone-500"
      />
    </section>
  );
}

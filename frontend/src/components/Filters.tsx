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
                  ? "border-teal-500 bg-teal-500 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-teal-400 hover:text-teal-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-teal-500 dark:hover:text-teal-400"
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
        className="ml-auto w-full max-w-xs rounded-lg border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500"
      />
    </section>
  );
}

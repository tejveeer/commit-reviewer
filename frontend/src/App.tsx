import { useMemo, useState } from "react";
import { CommitList } from "./components/CommitList";
import { Filters, type RatingFilter } from "./components/Filters";
import { Header } from "./components/Header";
import { SummaryBar } from "./components/SummaryBar";
import { ErrorState, LoadingState } from "./components/States";
import { useDarkMode } from "./hooks/useDarkMode";
import { useReport } from "./hooks/useReport";

export default function App() {
  const { dark, toggle } = useDarkMode();
  const state = useReport();

  const [filter, setFilter] = useState<RatingFilter>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (state.status !== "ready") return [];
    const query = search.trim().toLowerCase();
    return state.report.commits.filter((commit) => {
      if (filter !== "all" && commit.rating !== filter) return false;
      if (!query) return true;
      return (
        commit.message.toLowerCase().includes(query) ||
        commit.sha.toLowerCase().startsWith(query)
      );
    });
  }, [state, filter, search]);

  if (state.status === "loading") return <LoadingState />;
  if (state.status === "error") return <ErrorState message={state.error} />;

  return (
    <div className="min-h-screen">
      <Header report={state.report} dark={dark} toggle={toggle} />
      <SummaryBar summary={state.report.summary} />
      <Filters
        filter={filter}
        setFilter={setFilter}
        search={search}
        setSearch={setSearch}
      />
      <CommitList commits={filtered} />
    </div>
  );
}

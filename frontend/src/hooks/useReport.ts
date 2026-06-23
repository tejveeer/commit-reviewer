import { useEffect, useState } from "react";
import type { Report } from "../types";

type State =
  | { status: "loading" }
  | { status: "error"; error: string }
  | { status: "ready"; report: Report };

export function useReport(): State {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    fetch("./report.json", { cache: "no-store" })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Could not load report.json (HTTP ${res.status})`);
        }
        return res.json() as Promise<Report>;
      })
      .then((report) => {
        if (!cancelled) setState({ status: "ready", report });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : String(err);
          setState({ status: "error", error: message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

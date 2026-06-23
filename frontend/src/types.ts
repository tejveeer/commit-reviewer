export type Rating = "excellent" | "good" | "bad";

export type Mode = "local" | "remote";

export interface ReviewedCommit {
  sha: string;
  author: string;
  date: string;
  message: string;
  rating: Rating;
  reasoning: string;
}

export interface Summary {
  excellent: number;
  good: number;
  bad: number;
}

export interface Report {
  repo: string;
  mode: Mode;
  model: string;
  generated_at: string;
  summary: Summary;
  commits: ReviewedCommit[];
}

export const RATINGS: Rating[] = ["excellent", "good", "bad"];

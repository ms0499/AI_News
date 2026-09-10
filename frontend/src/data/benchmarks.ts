// Curated benchmark snapshot of frontier AI models.
//
// There is no free, live, no-key "quality benchmark" API (LMArena and
// Artificial Analysis are key-gated; the Hugging Face leaderboard the app
// already uses is a *trending/popularity* score, not a capability benchmark).
// So this is a hand-curated snapshot, in the same spirit as
// `backend/data/curated_models.py`'s flagship dict.
//
// HOW TO UPDATE: edit the rows below and bump BENCHMARK_AS_OF. `index` is a
// 0–100 composite "intelligence" score; `reasoning` and `coding` are 0–100
// sub-scores. Keep the array sorted by `index` descending — the panel renders
// in this order and derives the rank from position.

export interface BenchmarkModel {
  model: string;
  company: string;
  index: number; // composite intelligence index, 0–100
  reasoning: number; // reasoning/knowledge sub-score, 0–100
  coding: number; // coding sub-score, 0–100
}

export const BENCHMARK_AS_OF = "September 2026";

export const BENCHMARK_MODELS: BenchmarkModel[] = [
  { model: "GPT-6 Astra", company: "OpenAI", index: 89, reasoning: 91, coding: 88 },
  { model: "Gemini 3 Pro", company: "Google", index: 87, reasoning: 89, coding: 85 },
  { model: "Claude Opus 4.8", company: "Anthropic", index: 86, reasoning: 87, coding: 90 },
  { model: "Grok 4", company: "xAI", index: 82, reasoning: 84, coding: 80 },
  { model: "DeepSeek V3", company: "DeepSeek", index: 79, reasoning: 80, coding: 82 },
  { model: "Llama 4 Maverick", company: "Meta", index: 76, reasoning: 77, coding: 74 },
  { model: "Qwen3 Max", company: "Alibaba", index: 74, reasoning: 75, coding: 76 },
];

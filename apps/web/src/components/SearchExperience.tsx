"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { DuaCard } from "./DuaCard";
import { SituationChips } from "./SituationChips";
import { EngineError, fetchRecommendations, fetchTaxonomy } from "./../lib/api";
import {
  clearHistory,
  getFavourites,
  recordRecent,
  toggleFavourite,
} from "./../lib/storage";
import { humanise, type ExtractedContext, type RecommendationResponse, type Taxonomy } from "./../lib/types";

const EXAMPLES = [
  "I am anxious about a medical result",
  "Money is tight this month and I am stressed",
  "I argued with my brother and feel regretful",
  "It is the first Friday of the month",
  "I am travelling in an unfamiliar city",
  "I lost someone dear to me",
];

const LABEL_SETS = ["situations", "emotions", "intentions", "occasions", "topics"] as const;

export function SearchExperience() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  // Lazy initialiser rather than an effect: reading localStorage during the first
  // render avoids a cascading second render and the setState-in-effect warning.
  const [favourites, setFavourites] = useState<string[]>(() => getFavourites());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTaxonomy()
      .then(setTaxonomy)
      .catch(() => setTaxonomy(null));
  }, []);

  const occasion = useMemo(() => {
    const picked = [...selected].filter((slug) =>
      (taxonomy?.occasions ?? []).some((term) => term.id === slug),
    );
    return picked[0] ?? null;
  }, [selected, taxonomy]);

  const toggleChip = useCallback((slug: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }, []);

  async function search(event?: React.FormEvent) {
    event?.preventDefault();
    const text = query.trim();
    if (!text) {
      setError("Please describe your situation in a few words.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRecommendations(text, {
        k: 5,
        occasion,
        favourites,
      });
      setResponse(result);
      recordRecent(result.results.map((r) => r.dua_id));
    } catch (cause) {
      setResponse(null);
      setError(cause instanceof EngineError ? cause.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleToggleFavourite(duaId: string) {
    setFavourites(toggleFavourite(duaId));
  }

  const extracted: ExtractedContext | null = response?.extracted_context ?? null;
  const hasContext = extracted && LABEL_SETS.some((set) => (extracted.labels[set] ?? []).length > 0);

  return (
    <div className="space-y-8">
      <section className="card relative overflow-hidden shadow-lg ring-1 ring-sand-200/60 transition-shadow hover:shadow-xl">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 -top-24 h-48 w-48 rounded-full bg-emerald-100/40 blur-2xl"
        />
        <form onSubmit={search} className="relative space-y-5">
          <div>
            <label htmlFor="query" className="block text-lg font-semibold text-sand-900">
              What is going on?
            </label>
            <p className="mt-1 text-sm leading-relaxed text-sand-600 sm:text-base">
              Describe your situation in your own words. Nothing you type is stored on a
              server — all processing is local-first.
            </p>
            <textarea
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="For example: I am worried about my exam results next week and feeling overwhelmed"
              className="mt-3 w-full resize-y rounded-2xl border border-sand-300 bg-white/95 p-4 text-base shadow-sm transition focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-200/80"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                className="chip"
                onClick={() => setQuery(example)}
                disabled={loading}
              >
                {example}
              </button>
            ))}
          </div>

          <SituationChips
            taxonomy={taxonomy}
            selected={selected}
            onToggle={toggleChip}
            disabled={loading}
          />

          <div className="flex flex-wrap gap-3">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Searchingâ€¦" : "Find a Dua"}
            </button>
            {favourites.length > 0 && (
              <button
                type="button"
                className="btn-ghost"
                onClick={() => {
                  clearHistory();
                  setFavourites([]);
                }}
              >
                Clear saved Duas ({favourites.length})
              </button>
            )}
          </div>
        </form>
      </section>

      {error && (
        <div role="alert" className="card border-red-300 bg-red-50 text-red-900">
          {error}
        </div>
      )}

      {response && (
        <>
          {hasContext && extracted && (
            <section className="card">
              <h2 className="font-medium text-sand-900">What we understood</h2>
              <p className="mt-1 text-sm text-sand-600">
                Inferred automatically from your words. These are draft labels, not an
                assessment of your situation.
              </p>
              <dl className="mt-3 space-y-2 text-sm">
                {LABEL_SETS.map((set) => {
                  const labels = extracted.labels[set] ?? [];
                  if (labels.length === 0) return null;
                  return (
                    <div key={set} className="flex gap-2">
                      <dt className="w-24 shrink-0 capitalize text-sand-600">{set}</dt>
                      <dd className="flex flex-wrap gap-1.5">
                        {labels.map((label) => (
                          <span
                            key={label}
                            className="rounded-full bg-sand-100 px-2 py-0.5 text-sand-800"
                          >
                            {humanise(label)}
                          </span>
                        ))}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </section>
          )}

          <section aria-live="polite" className="space-y-4">
            <h2 className="text-lg font-semibold text-sand-900">
              {response.results.length} suggestion{response.results.length === 1 ? "" : "s"}
            </h2>
            {response.results.length === 0 && (
              <p className="card text-sand-700">
                Nothing in the current corpus matched. Try describing the situation
                differently, or browse by situation.
              </p>
            )}
            {response.results.map((result, index) => (
              <DuaCard
                key={result.dua_id}
                result={result}
                explanation={response.explanations[index]}
                favourite={favourites.includes(result.dua_id)}
                onToggleFavourite={handleToggleFavourite}
              />
            ))}
          </section>

          <p className="text-sm text-sand-600">{response.disclaimer}</p>
        </>
      )}
    </div>
  );
}


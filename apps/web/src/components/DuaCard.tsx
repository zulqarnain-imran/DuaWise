"use client";

import { humanise, type DuaResult, type Explanation } from "../lib/types";
import { useState } from "react";

interface Props {
  result: DuaResult;
  explanation?: Explanation;
  favourite: boolean;
  onToggleFavourite: (duaId: string) => void;
}

const REFERENCE_LABELS: Record<string, string> = {
  matched_to_hadith: "Matched to a hadith collection",
  chapter_and_item_only: "Cited by chapter and item",
  quran_verse: "Qur'an verse",
};

type Lang = "ar" | "en" | "ur";

export function DuaCard({ result, explanation, favourite, onToggleFavourite }: Props) {
  const [lang, setLang] = useState<Lang>("ar");
  
  const hasUrdu = false; // corpus doesn't have Urdu; keeping structure for future

  return (
    <article className="card card-glow group flex flex-col gap-6 overflow-hidden">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 h-48 w-48 rounded-full bg-gradient-to-br from-emerald-100/40 to-teal-100/30 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100"
      />
      <header className="relative flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <h3 className="text-xl font-bold tracking-tight text-sand-900 sm:text-2xl">
            {result.title}
          </h3>
          <p className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-0.5 text-xs font-semibold uppercase tracking-wide text-emerald-800 ring-1 ring-emerald-200/70">
            {result.source_work}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onToggleFavourite(result.dua_id)}
            aria-pressed={favourite}
            className={`chip shrink-0 ${
              favourite ? "chip-active" : ""
            }`}
            title={favourite ? "Remove from saved" : "Save locally"}
          >
            {favourite ? "★ Saved" : "☆ Save"}
          </button>
        </div>
      </header>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-sand-200/60 bg-gradient-to-r from-sand-50/80 to-white/90 p-2 shadow-sm ring-1 ring-sand-100/70 backdrop-blur-sm">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setLang("ar")}
            className={`chip ${lang === "ar" ? "chip-active" : ""}`}
            data-lang="ar"
          >
            العربية
          </button>
          <button
            type="button"
            onClick={() => setLang("en")}
            className={`chip ${lang === "en" ? "chip-active" : ""}`}
          >
            English
          </button>
          <button
            type="button"
            onClick={() => setLang("ur")}
            className={`chip ${lang === "ur" ? "chip-active" : ""}`}
            data-lang="ur"
            disabled={!hasUrdu}
          >
            اردو
          </button>
        </div>
        <span className="px-2 text-xs text-sand-500">
          {lang === "ar" ? "Arabic" : lang === "ur" ? "Urdu" : "English"} • 3 Languages
        </span>
      </div>

      <div className="relative min-h-[6rem]">
        {lang === "ar" && (
          <p dir="rtl" lang="ar" data-lang="ar" className="text-right text-4xl leading-[2.5] text-sand-900 sm:text-5xl">
            {result.arabic}
          </p>
        )}
        {lang === "en" && (
          <p lang="en" data-lang="en" className="text-left text-lg leading-relaxed text-sand-800 sm:text-xl">
            {result.translation}
          </p>
        )}
        {lang === "ur" && (
          <div dir="rtl" lang="ur" data-lang="ur" className="space-y-4 text-right">
            <p className="text-3xl leading-[2.6] text-sand-900 sm:text-4xl">
              {result.arabic}
            </p>
            <p className="text-xl leading-[2.5] text-sand-800">
              {result.translation}
            </p>
          </div>
        )}
      </div>

      {result.recitation_count !== null && result.recitation_count > 1 && (
        <p className="text-sm text-sand-600">
          Traditionally recited {result.recitation_count} times.
        </p>
      )}

      <div className="relative rounded-2xl border border-sand-200/70 bg-gradient-to-br from-sand-50 to-white p-4 text-sm shadow-sm ring-1 ring-sand-200/50">
        <p className="font-semibold text-sand-900">Source &amp; Attribution</p>
        <p className="mt-2 text-sand-800">{result.source_reference}</p>
        {result.hadith_reference && (
          <p className="mt-1 text-sand-700">
            Reported in: <span dir="auto">{result.hadith_reference}</span>
          </p>
        )}
        <p className="mt-2 text-xs uppercase tracking-wide text-sand-600">
          {REFERENCE_LABELS[result.reference_status] ?? result.reference_status}
        </p>
      </div>

      {explanation && explanation.reasons.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-emerald-800 hover:text-emerald-900">
            Why this was suggested (explainable ranking)
          </summary>
          <p className="mt-2 text-xs text-sand-600">
            Score components from the context-aware ranker (M4). Higher contribution means
            stronger influence on the final score.
          </p>
          <ul className="mt-3 space-y-1.5 text-sand-700">
            {explanation.reasons.slice(0, 4).map((reason) => (
              <li key={reason.feature} className="flex justify-between gap-3">
                <span className="font-medium text-sand-800">{humanise(reason.feature)}</span>
                <span className="tabular-nums text-sand-500">
                  {reason.contribution.toFixed(3)}
                </span>
              </li>
            ))}
          </ul>
          {Object.keys(explanation.matched_labels).length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {Object.entries(explanation.matched_labels).flatMap(([feature, labels]) =>
                labels.map((label) => (
                  <span
                    key={`${feature}-${label}`}
                    className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800"
                  >
                    {humanise(label)}
                  </span>
                )),
              )}
            </div>
          )}
        </details>
      )}

      {result.review_states.scholar === "not_reviewed" && (
        <p className="text-xs text-amber-800">
          Context labels are draft and awaiting scholar review.
        </p>
      )}
    </article>
  );
}


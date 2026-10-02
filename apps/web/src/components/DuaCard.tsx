"use client";

import { humanise, type DuaResult, type Explanation } from "../lib/types";

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

export function DuaCard({ result, explanation, favourite, onToggleFavourite }: Props) {
  return (
    <article className="card flex flex-col gap-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-sand-900">{result.title}</h3>
          <p className="mt-1 text-xs uppercase tracking-wide text-sand-600">
            {result.source_work}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onToggleFavourite(result.dua_id)}
          aria-pressed={favourite}
          className="chip shrink-0"
          title={favourite ? "Remove from saved" : "Save locally"}
        >
          {favourite ? "â˜… Saved" : "â˜† Save"}
        </button>
      </header>

      <p dir="rtl" lang="ar" className="text-right text-2xl text-sand-900">
        {result.arabic}
      </p>

      <p className="text-sand-800">{result.translation}</p>

      {result.recitation_count !== null && result.recitation_count > 1 && (
        <p className="text-sm text-sand-600">
          Traditionally recited {result.recitation_count} times.
        </p>
      )}

      <div className="rounded-xl bg-sand-100 p-3 text-sm">
        <p className="font-medium text-sand-900">Source</p>
        <p className="mt-1 text-sand-800">{result.source_reference}</p>
        {result.hadith_reference && (
          <p className="mt-1 text-sand-700">
            Reported in: <span dir="auto">{result.hadith_reference}</span>
          </p>
        )}
        <p className="mt-1 text-xs text-sand-600">
          {REFERENCE_LABELS[result.reference_status] ?? result.reference_status}
        </p>
      </div>

      {explanation && explanation.reasons.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-emerald-700">
            Why this was suggested
          </summary>
          <ul className="mt-2 space-y-1 text-sand-700">
            {explanation.reasons.slice(0, 4).map((reason) => (
              <li key={reason.feature} className="flex justify-between gap-3">
                <span>{reason.feature}</span>
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


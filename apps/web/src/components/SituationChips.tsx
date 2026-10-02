"use client";

import { useState } from "react";
import type { Taxonomy, TaxonomyTerm } from "../lib/types";
import { humanise } from "../lib/types";

interface Props {
  taxonomy: Taxonomy | null;
  selected: Set<string>;
  onToggle: (slug: string) => void;
  disabled?: boolean;
}

const GROUPS: { key: keyof Taxonomy; label: string; hint: string }[] = [
  { key: "situations", label: "Situation", hint: "What is happening" },
  { key: "occasions", label: "Occasion", hint: "When or what day" },
];

export function SituationChips({ taxonomy, selected, onToggle, disabled }: Props) {
  const [open, setOpen] = useState(false);

  if (!taxonomy) {
    return (
      <div className="text-sm text-sand-600" aria-live="polite">
        Loading situationsâ€¦
      </div>
    );
  }

  const activeTerms = GROUPS.flatMap((group) =>
    (taxonomy[group.key] ?? [])
      .filter((term) => selected.has(term.id))
      .map((term) => ({ ...term, group: group.label })),
  );

  return (
    <div className="space-y-3">
      <button
        type="button"
        className="btn-ghost text-sm"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="taxonomy-chips"
      >
        {open ? "Hide" : "Browse by"}
        {selected.size > 0 ? ` situation (${selected.size} selected)` : " situation or occasion"}
      </button>

      {activeTerms.length > 0 && (
        <p className="text-sm text-sand-700">
          Selected:{" "}
          <span className="font-medium text-emerald-800">
            {activeTerms.map((term) => term.group + ": " + humanise(term.id)).join(", ")}
          </span>
        </p>
      )}

      {open && (
        <div id="taxonomy-chips" className="space-y-4 rounded-2xl border border-sand-200 bg-white p-4">
          {GROUPS.map((group) => {
            const terms: TaxonomyTerm[] = taxonomy[group.key] ?? [];
            if (terms.length === 0) return null;
            return (
              <fieldset key={group.key} disabled={disabled}>
                <legend className="mb-2 text-sm font-medium text-sand-900">
                  {group.label}
                  <span className="ml-2 font-normal text-sand-600">{group.hint}</span>
                </legend>
                <div className="flex flex-wrap gap-2">
                  {terms.map((term) => {
                    const isActive = selected.has(term.id);
                    return (
                      <button
                        key={term.id}
                        type="button"
                        className={`chip ${isActive ? "chip-active" : ""}`}
                        aria-pressed={isActive}
                        title={term.definition}
                        onClick={() => onToggle(term.id)}
                      >
                        {term.label}
                      </button>
                    );
                  })}
                </div>
              </fieldset>
            );
          })}
        </div>
      )}
    </div>
  );
}


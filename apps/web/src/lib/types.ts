/**
 * Types mirroring the Python service's JSON contract (dua_reco/server.py).
 *
 * Hand-maintained rather than generated: the engine is a separately versioned
 * service. `isRecommendationResponse` guards against a contract drift silently
 * rendering an error payload as a result list.
 */

export interface DuaLabels {
  situations: string[];
  emotions: string[];
  intentions: string[];
  occasions: string[];
  topics: string[];
}

export interface DuaResult {
  dua_id: string;
  title: string;
  arabic: string;
  translation: string;
  source_work: string;
  source_reference: string;
  hadith_reference: string | null;
  reference_status: string;
  review_states: Record<string, string>;
  recitation_count: number | null;
  final_score: number;
  components: Record<string, number>;
  labels: DuaLabels;
}

export interface Explanation {
  rank: number;
  dua_id: string;
  title: string;
  final_score: number;
  reasons: { feature: string; contribution: number }[];
  matched_labels: Record<string, string[]>;
  source: {
    work: string;
    reference: string;
    hadith_reference: string | null;
    reference_status: string;
  };
  review_states: Record<string, string>;
  disclaimer: string;
}

export interface ExtractedContext {
  labels: Partial<Record<keyof DuaLabels, string[]>>;
  scores: Partial<Record<keyof DuaLabels, Record<string, number>>>;
}

export interface RecommendationResponse {
  query: string;
  extracted_context: ExtractedContext;
  results: DuaResult[];
  explanations: Explanation[];
  disclaimer: string;
  provenance: Record<string, unknown> | null;
  annotation_status: string | null;
}

export interface Taxonomy {
  situations: TaxonomyTerm[];
  emotions: TaxonomyTerm[];
  intentions: TaxonomyTerm[];
  occasions: TaxonomyTerm[];
  topics: TaxonomyTerm[];
}

export interface TaxonomyTerm {
  id: string;
  label: string;
  definition: string;
}

export interface Health {
  status: string;
  corpus_size: number;
  embedding_model: string;
  fallback_encoder: boolean;
  weights_tuned: boolean;
  annotation_status: string | null;
}

export function isRecommendationResponse(value: unknown): value is RecommendationResponse {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<RecommendationResponse>;
  return (
    Array.isArray(candidate.results) &&
    Array.isArray(candidate.explanations) &&
    typeof candidate.disclaimer === "string" &&
    typeof candidate.query === "string"
  );
}

/** Human-readable label for a slug from the controlled vocabulary. */
export function humanise(slug: string): string {
  return slug.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

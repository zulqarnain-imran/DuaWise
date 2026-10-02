import {
  isRecommendationResponse,
  type Health,
  type RecommendationResponse,
  type Taxonomy,
} from "./types";

/**
 * The browser never calls the Python service directly. It goes through the
 * Next.js rewrite so the engine host is never exposed to the client and CORS
 * does not depend on the deployment domain.
 */
const ENGINE_BASE = "/api/engine";

export class EngineError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "EngineError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${ENGINE_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    // A connection failure means the Python service is down, which is an
    // operational problem rather than a bad request, so it gets its own message.
    throw new EngineError(
      "The recommendation service is unreachable. Start it with: ml\\.venv\\Scripts\\python.exe -m uvicorn dua_reco.server:app --port 8000",
      503,
    );
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new EngineError(
      detail ? `Engine error ${response.status}: ${detail.slice(0, 200)}` : `Engine error ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as T;
}

export async function fetchHealth(): Promise<Health> {
  return request<Health>("/health");
}

export async function fetchTaxonomy(): Promise<Taxonomy> {
  return request<Taxonomy>("/taxonomy");
}

export async function fetchRecommendations(
  query: string,
  options: { k?: number; occasion?: string | null; favourites?: string[]; excludeIds?: string[] } = {},
): Promise<RecommendationResponse> {
  const payload = await request<unknown>("/recommend", {
    method: "POST",
    body: JSON.stringify({
      query,
      k: options.k ?? 5,
      occasion: options.occasion ?? null,
      favourites: options.favourites ?? [],
      exclude_ids: options.excludeIds ?? [],
    }),
  });

  if (!isRecommendationResponse(payload)) {
    throw new EngineError("Unexpected response shape from the recommendation service", 502);
  }
  return payload;
}

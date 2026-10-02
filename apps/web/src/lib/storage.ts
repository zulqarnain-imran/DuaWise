/**
 * Local-only history for saved Duas.
 *
 * Deliberately localStorage rather than a server account: the project decision was
 * an anonymous, no-login experience. Nothing identifying is stored or transmitted.
 */

const FAVOURITES_KEY = "dua-wise:favourites";
const RECENT_KEY = "dua-wise:recent";

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    // Private-browsing modes and corrupted values must not break the app.
    return fallback;
  }
}

function write(key: string, value: unknown): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Quota or privacy mode: the feature degrades, the app continues.
  }
}

export const MAX_RECENT = 12;

export function getFavourites(): string[] {
  return read<string[]>(FAVOURITES_KEY, []);
}

export function toggleFavourite(duaId: string): string[] {
  const current = getFavourites();
  const next = current.includes(duaId)
    ? current.filter((id) => id !== duaId)
    : [...current, duaId];
  write(FAVOURITES_KEY, next);
  return next;
}

export function isFavourite(duaId: string, favourites: string[]): boolean {
  return favourites.includes(duaId);
}

export function getRecent(): string[] {
  return read<string[]>(RECENT_KEY, []);
}

export function recordRecent(duaIds: string[]): void {
  const existing = getRecent();
  const merged = [...duaIds, ...existing.filter((id) => !duaIds.includes(id))];
  write(RECENT_KEY, merged.slice(0, MAX_RECENT));
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(FAVOURITES_KEY);
  window.localStorage.removeItem(RECENT_KEY);
}

export interface EntryBase {
  dateISO: string;
  notes?: string;
  createdAtISO: string;
}

export interface RunEntry extends EntryBase {
  miles: number;
  paceMinPerMile: number;
}

export interface SingleValueEntry extends EntryBase {
  value: number;
}

export type GoalEntry = RunEntry | SingleValueEntry;

const STORAGE_KEY_PREFIX = 'goalEntries:';

export function loadEntries<T extends GoalEntry>(goalId: string): T[] {
  if (typeof window === 'undefined') return [];
  const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${goalId}`);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as T[];
  } catch {
    return [];
  }
}

export function appendEntry<T extends GoalEntry>(goalId: string, entry: T): T[] {
  const entries = loadEntries<T>(goalId);
  entries.push(entry);
  localStorage.setItem(`${STORAGE_KEY_PREFIX}${goalId}`, JSON.stringify(entries));
  return entries;
}

export function exportEntries(goalId: string): string {
  const entries = loadEntries(goalId);
  return JSON.stringify(entries, null, 2);
}

export function importEntries<T extends GoalEntry>(goalId: string, jsonString: string): T[] {
  const parsed = JSON.parse(jsonString) as T[];
  if (!Array.isArray(parsed)) throw new Error('Invalid format: expected array');
  localStorage.setItem(`${STORAGE_KEY_PREFIX}${goalId}`, JSON.stringify(parsed));
  return parsed;
}

export function getLatestEntry<T extends GoalEntry>(goalId: string): T | null {
  const entries = loadEntries<T>(goalId);
  if (entries.length === 0) return null;
  // Return the most recently created entry
  return entries.reduce((latest, entry) =>
    new Date(entry.createdAtISO) > new Date(latest.createdAtISO) ? entry : latest
  );
}

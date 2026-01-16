'use client';

import { useMemo } from 'react';
import { loadEntries, GoalEntry, RunEntry, SingleValueEntry } from '@/app/config/storage';

interface Props {
  goalId: string;
  refreshKey?: number;
}

function isRunEntry(entry: GoalEntry): entry is RunEntry {
  return 'miles' in entry && 'paceMinPerMile' in entry;
}

export function RecentEntries({ goalId, refreshKey }: Props) {
  const entries = useMemo(() => {
    // refreshKey is used to trigger re-computation
    void refreshKey;
    return loadEntries(goalId);
  }, [goalId, refreshKey]);

  const recentTen = [...entries].reverse().slice(0, 10);

  if (recentTen.length === 0) {
    return <p className="text-gray-500 text-sm">No entries yet.</p>;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-gray-900">Recent Entries</h3>
      <ul className="divide-y divide-gray-200">
        {recentTen.map((entry, idx) => (
          <li key={idx} className="py-2">
            <div className="flex justify-between">
              <span className="text-gray-900">
                {new Date(entry.dateISO).toLocaleDateString()}
              </span>
              <span className="text-gray-700">
                {isRunEntry(entry)
                  ? `${entry.miles} miles @ ${entry.paceMinPerMile} min/mi`
                  : goalId === 'hangouts'
                  ? `${(entry as SingleValueEntry).value} hangouts`
                  : `${(entry as SingleValueEntry).value} minutes`}
              </span>
            </div>
            {entry.notes && (
              <p className="text-sm text-gray-500 mt-1">{entry.notes}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

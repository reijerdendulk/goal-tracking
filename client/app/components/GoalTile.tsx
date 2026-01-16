'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Goal } from '@/app/config/goals';
import { getLatestEntry, GoalEntry, RunEntry, SingleValueEntry } from '@/app/config/storage';

interface Props {
  goal: Goal;
}

function isRunEntry(entry: GoalEntry): entry is RunEntry {
  return 'miles' in entry && 'paceMinPerMile' in entry;
}

function formatLastEntry(goalId: string, entry: GoalEntry | null): string {
  if (!entry) return 'No entries yet';

  if (isRunEntry(entry)) {
    return `${entry.miles} miles @ ${entry.paceMinPerMile} min/mi`;
  }

  const singleEntry = entry as SingleValueEntry;
  if (goalId === 'hangouts') {
    return `${singleEntry.value} hangout${singleEntry.value !== 1 ? 's' : ''}`;
  }
  return `${singleEntry.value} minutes`;
}

export function GoalTile({ goal }: Props) {
  const [lastEntry, setLastEntry] = useState<GoalEntry | null>(null);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  // Re-read from localStorage when pathname changes (client-side navigation)
  useEffect(() => {
    setMounted(true);
    setLastEntry(getLatestEntry(goal.id));
  }, [goal.id, pathname]);

  // Re-read from localStorage when page becomes visible (user navigates back)
  useEffect(() => {
    function handleVisibilityChange() {
      if (document.visibilityState === 'visible') {
        setLastEntry(getLatestEntry(goal.id));
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [goal.id]);

  // Also re-read on focus (covers more navigation patterns)
  useEffect(() => {
    function handleFocus() {
      setLastEntry(getLatestEntry(goal.id));
    }

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [goal.id]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900">{goal.name}</h3>
      <p className="text-sm text-gray-500 mt-1">{goal.description}</p>
      <p className="text-sm text-gray-700 mt-2">
        <span className="font-medium">Last entry:</span>{' '}
        {mounted ? formatLastEntry(goal.id, lastEntry) : '...'}
      </p>
      <Link
        href={goal.hrefNew}
        className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
      >
        Open
      </Link>
    </div>
  );
}

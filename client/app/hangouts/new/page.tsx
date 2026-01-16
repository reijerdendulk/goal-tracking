'use client';

import { useState, FormEvent, useMemo } from 'react';
import Link from 'next/link';
import { PATHS } from '@/app/config/routes';
import { appendEntry, SingleValueEntry } from '@/app/config/storage';
import { RecentEntries } from '@/app/components/RecentEntries';
import { ExportImport } from '@/app/components/ExportImport';

function getTodayDateString(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function NewHangout() {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const todayDate = useMemo(() => getTodayDateString(), []);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    const formData = new FormData(e.currentTarget);
    const dateInput = formData.get('date') as string;
    const count = parseInt(formData.get('count') as string, 10);
    const notes = formData.get('notes') as string;

    // Validation
    if (count <= 0) {
      setError('Hangouts count must be greater than 0');
      return;
    }

    const entry: SingleValueEntry = {
      dateISO: dateInput,
      value: count,
      notes: notes || undefined,
      createdAtISO: new Date().toISOString(),
    };

    appendEntry('hangouts', entry);
    setSuccess(true);
    setRefreshKey((k) => k + 1);

    // Clear inputs
    const form = e.currentTarget;
    (form.querySelector('[name="count"]') as HTMLInputElement).value = '1';
    (form.querySelector('[name="notes"]') as HTMLTextAreaElement).value = '';

    setTimeout(() => setSuccess(false), 2000);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-green-600 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold">Log Hangout</h1>
          <p className="text-green-100 text-sm mt-1">Enter your hangout details</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-medium">Error</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
              </div>
            )}

            {success && (
              <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-medium">Entry saved!</p>
              </div>
            )}

            <div className="space-y-6">
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">
                  Date *
                </label>
                <input
                  type="date"
                  id="date"
                  name="date"
                  required
                  defaultValue={todayDate}
                  max={todayDate}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="count" className="block text-sm font-medium text-gray-700 mb-2">
                  Hangouts *
                </label>
                <input
                  type="number"
                  id="count"
                  name="count"
                  min="1"
                  required
                  defaultValue="1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Number of hangouts to log
                </p>
              </div>

              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                  Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="mt-8 flex gap-4">
              <button
                type="submit"
                className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 focus:ring-4 focus:ring-green-200"
              >
                Save entry
              </button>
            </div>

            <div className="mt-4">
              <Link
                href={PATHS.home}
                className="text-green-600 hover:underline text-sm"
              >
                Back to Goal Tracking
              </Link>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <ExportImport goalId="hangouts" onImport={() => setRefreshKey((k) => k + 1)} />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <RecentEntries goalId="hangouts" refreshKey={refreshKey} />
        </div>
      </main>
    </div>
  );
}

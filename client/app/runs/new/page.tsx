'use client';

import { useState, FormEvent, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createRun } from '@/lib/api';
import { milesToMeters, paceMinPerMileToSecPerKm, isValidPaceFormat } from '@/lib/conversions';

/**
 * Get today's date in YYYY-MM-DD format for the date picker default.
 * Uses local timezone to match user expectations.
 */
function getTodayDateString(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function NewRun() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Memoize today's date to avoid hydration mismatch
  const todayDate = useMemo(() => getTodayDateString(), []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    const dateInput = formData.get('date') as string;
    const distanceMiles = parseFloat(formData.get('distance_miles') as string);
    const paceStr = formData.get('pace_min_per_mile') as string;
    const notes = formData.get('notes') as string;

    try {
      // Validate inputs
      if (distanceMiles <= 0) {
        throw new Error('Distance must be greater than 0');
      }

      if (!isValidPaceFormat(paceStr)) {
        throw new Error('Pace must be in mm:ss format (e.g., 8:30) with seconds 00-59');
      }

      // Convert units
      const distanceMeters = milesToMeters(distanceMiles);
      const avgPaceSecPerKm = paceMinPerMileToSecPerKm(paceStr);

      // Create timestamp at 12:00 UTC
      const runDate = new Date(dateInput);
      runDate.setUTCHours(12, 0, 0, 0);
      const startAt = runDate.toISOString();

      // Call API
      await createRun({
        title: `Run - ${distanceMiles} mi`,
        notes: notes || null,
        start_at: startAt,
        end_at: null,
        duration_min: null,
        tags: null,
        distance_meters: distanceMeters,
        moving_time_sec: null,
        avg_pace_sec_per_km: avgPaceSecPerKm,
        elevation_gain_m: null,
        rpe: null,
        workout_type: 'easy', // Default
        surface: null,
        shoe: null,
        splits: null,
      });

      setSuccess(true);
      setTimeout(() => router.push('/'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold">Add Run</h1>
          <p className="text-blue-100 text-sm mt-1">Enter your run details</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          {success ? (
            <div className="text-center py-8">
              <div className="text-green-600 text-5xl mb-4">✓</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Run Created!</h2>
              <p className="text-gray-600">Redirecting to home...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {error && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800 font-medium">Error</p>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
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
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Select the date of your run (defaults to today)
                  </p>
                </div>

                <div>
                  <label htmlFor="distance_miles" className="block text-sm font-medium text-gray-700 mb-2">
                    Distance (miles) *
                  </label>
                  <input
                    type="number"
                    id="distance_miles"
                    name="distance_miles"
                    step="0.01"
                    min="0.01"
                    required
                    placeholder="5.5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">Example: 5.5</p>
                </div>

                <div>
                  <label htmlFor="pace_min_per_mile" className="block text-sm font-medium text-gray-700 mb-2">
                    Pace (min/mile) *
                  </label>
                  <input
                    type="text"
                    id="pace_min_per_mile"
                    name="pace_min_per_mile"
                    pattern="\d+:[0-5]\d"
                    placeholder="8:30"
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Format: mm:ss (e.g., 8:30 for 8 minutes 30 seconds per mile)
                  </p>
                </div>

                <div>
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    id="notes"
                    name="notes"
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Saving...' : 'Save Run'}
                </button>
                <Link
                  href="/"
                  className="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 text-center"
                >
                  Cancel
                </Link>
              </div>

              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Unit Conversions</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Distance will be stored as meters (1 mile = 1609.344 meters)</li>
                  <li>• Pace will be converted to seconds per kilometer for storage</li>
                  <li>• Workout type defaults to "easy"</li>
                </ul>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}

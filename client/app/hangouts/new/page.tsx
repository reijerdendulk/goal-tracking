'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createHangout } from '@/lib/api';

export default function NewHangout() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    const title = formData.get('title') as string;
    const locationName = formData.get('location_name') as string;
    const locationType = formData.get('location_type') as string;
    const moodStr = formData.get('mood') as string;
    const participantsStr = formData.get('participants') as string;
    const notes = formData.get('notes') as string;

    try {
      // Parse mood
      const mood = moodStr ? parseInt(moodStr, 10) : null;
      if (mood && (mood < 1 || mood > 5)) {
        throw new Error('Mood must be between 1 and 5');
      }

      // Parse participants (comma-separated names)
      const participants = participantsStr
        ? participantsStr
            .split(',')
            .map((name) => name.trim())
            .filter((name) => name.length > 0)
            .map((name) => ({ name }))
        : null;

      // Use current timestamp
      const startAt = new Date().toISOString();

      // Call API
      await createHangout({
        title,
        notes: notes || null,
        start_at: startAt,
        end_at: null,
        duration_min: null,
        tags: null,
        location_name: locationName || null,
        location_type: locationType || null,
        cost_estimate: null,
        mood,
        participants,
      });

      setSuccess(true);
      setTimeout(() => router.push('/'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create hangout');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-green-600 text-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold">Add Hangout</h1>
          <p className="text-green-100 text-sm mt-1">Enter your hangout details</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          {success ? (
            <div className="text-center py-8">
              <div className="text-green-600 text-5xl mb-4">✓</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Hangout Created!</h2>
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
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label htmlFor="location_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Location Name
                  </label>
                  <input
                    type="text"
                    id="location_name"
                    name="location_name"
                    placeholder="Blue Bottle Coffee"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label htmlFor="location_type" className="block text-sm font-medium text-gray-700 mb-2">
                    Location Type
                  </label>
                  <input
                    type="text"
                    id="location_type"
                    name="location_type"
                    placeholder="cafe, restaurant, park"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label htmlFor="mood" className="block text-sm font-medium text-gray-700 mb-2">
                    Mood (1-5)
                  </label>
                  <input
                    type="number"
                    id="mood"
                    name="mood"
                    min="1"
                    max="5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">1 = worst, 5 = best</p>
                </div>

                <div>
                  <label htmlFor="participants" className="block text-sm font-medium text-gray-700 mb-2">
                    Participants
                  </label>
                  <input
                    type="text"
                    id="participants"
                    name="participants"
                    placeholder="Alice, Bob, Charlie"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">Comma-separated names</p>
                </div>

                <div>
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    id="notes"
                    name="notes"
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 focus:ring-4 focus:ring-green-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Saving...' : 'Save Hangout'}
                </button>
                <Link
                  href="/"
                  className="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 text-center"
                >
                  Cancel
                </Link>
              </div>

              <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-900 mb-2">Important Notes</h4>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Timestamp will be set to current time (UTC)</li>
                  <li>• Participants will be created if they don't exist</li>
                  <li>• Existing participants will be matched by name</li>
                </ul>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}

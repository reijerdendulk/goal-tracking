'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getRecentActivities, type RecentActivity, checkHealth } from '@/lib/api';
import { metersToMiles, secPerKmToPaceStr } from '@/lib/conversions';

export default function Home() {
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dbStatus, setDbStatus] = useState<'checking' | 'ok' | 'error'>('checking');

  useEffect(() => {
    async function fetchData() {
      try {
        // Check health
        const health = await checkHealth();
        setDbStatus(health.ok ? 'ok' : 'error');

        // Fetch recent activities
        const data = await getRecentActivities(10);
        setActivities(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setDbStatus('error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const runs = activities.filter((a) => a.type === 'run');
  const hangouts = activities.filter((a) => a.type === 'hangout');
  const workSessions = activities.filter((a) => a.type === 'work');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Goal Tracking</h1>
              <p className="text-blue-100 text-sm mt-1">Track your runs, hangouts, and work sessions</p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  dbStatus === 'ok'
                    ? 'bg-green-100 text-green-800'
                    : dbStatus === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full mr-2 ${
                    dbStatus === 'ok'
                      ? 'bg-green-500'
                      : dbStatus === 'error'
                      ? 'bg-red-500'
                      : 'bg-yellow-500'
                  }`}
                ></span>
                {dbStatus === 'ok' ? 'Connected' : dbStatus === 'error' ? 'Disconnected' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Link */}
        <section className="mb-6">
          <Link
            href="/dashboard"
            className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow"
          >
            <span className="mr-2">📊</span> View Run Dashboard
          </Link>
        </section>

        {/* Quick Actions */}
        <section className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/runs/new"
              className="flex items-center justify-center px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              🏃 Add Run
            </Link>
            <Link
              href="/hangouts/new"
              className="flex items-center justify-center px-6 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              👥 Add Hangout
            </Link>
            <Link
              href="/work/new"
              className="flex items-center justify-center px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              💼 Add Work Session
            </Link>
          </div>
        </section>

        {/* Recent Activities */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading activities...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-red-800 font-semibold text-lg">Error</h2>
            <p className="text-red-600 mt-2">{error}</p>
            <p className="text-red-500 text-sm mt-4">
              Make sure your API is running at http://localhost:8000
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Recent Runs */}
            <section className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Runs</h3>
              {runs.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Title</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-600">Distance</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-600">Pace</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map((run) => (
                        <tr key={run.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-900">
                            {new Date(run.start_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 text-gray-900 font-medium">{run.title}</td>
                          <td className="py-3 px-4 text-right text-gray-900">
                            {run.run_detail ? `${metersToMiles(run.run_detail.distance_meters)} mi` : '-'}
                          </td>
                          <td className="py-3 px-4 text-right text-gray-900">
                            {run.run_detail?.avg_pace_sec_per_km
                              ? `${secPerKmToPaceStr(run.run_detail.avg_pace_sec_per_km)}/mi`
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No runs yet. <Link href="/runs/new" className="text-blue-600 hover:underline">Add your first run!</Link>
                </p>
              )}
            </section>

            {/* Recent Hangouts */}
            <section className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Hangouts</h3>
              {hangouts.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Title</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Participants</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">Mood</th>
                      </tr>
                    </thead>
                    <tbody>
                      {hangouts.map((hangout) => (
                        <tr key={hangout.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-900">
                            {new Date(hangout.start_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 text-gray-900 font-medium">{hangout.title}</td>
                          <td className="py-3 px-4 text-gray-900">
                            {hangout.participants && hangout.participants.length > 0
                              ? hangout.participants.map((p) => p.person.name).join(', ')
                              : '-'}
                          </td>
                          <td className="py-3 px-4 text-center text-gray-900">
                            {hangout.hangout_detail?.mood ? '⭐'.repeat(hangout.hangout_detail.mood) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No hangouts yet. <Link href="/hangouts/new" className="text-green-600 hover:underline">Add your first hangout!</Link>
                </p>
              )}
            </section>

            {/* Recent Work Sessions */}
            <section className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Work Sessions</h3>
              {workSessions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Title</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Project</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">Duration</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-600">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {workSessions.map((work) => (
                        <tr key={work.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-gray-900">
                            {new Date(work.start_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 text-gray-900 font-medium">{work.title}</td>
                          <td className="py-3 px-4 text-gray-900">{work.work_detail?.project || '-'}</td>
                          <td className="py-3 px-4 text-center text-gray-900">
                            {work.duration_min ? `${work.duration_min} min` : '-'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                                work.work_detail?.status === 'done'
                                  ? 'bg-green-100 text-green-800'
                                  : work.work_detail?.status === 'in_progress'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : work.work_detail?.status === 'blocked'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {work.work_detail?.status || '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No work sessions yet. <Link href="/work/new" className="text-purple-600 hover:underline">Add your first session!</Link>
                </p>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

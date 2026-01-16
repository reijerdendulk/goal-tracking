'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { listRuns, RunListItem } from '@/lib/api';
import { PATHS } from '@/app/config/routes';

/**
 * Convert meters to miles.
 */
function metersToMiles(meters: number): number {
  return meters / 1609.344;
}

/**
 * Convert seconds per km to minutes per mile, returning mm:ss format.
 */
function secPerKmToMinPerMile(secPerKm: number): string {
  // sec/km * 1.609344 = sec/mile
  const secPerMile = secPerKm * 1.609344;
  const minutes = Math.floor(secPerMile / 60);
  const seconds = Math.round(secPerMile % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Format date as MM/DD.
 */
function formatDateShort(dateStr: string): string {
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

/**
 * Get current month's start and end dates.
 */
function getCurrentMonthRange(): { start: Date; end: Date } {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
  return { start, end };
}

export default function Dashboard() {
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRuns() {
      try {
        const data = await listRuns(500);
        setRuns(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load runs');
      } finally {
        setLoading(false);
      }
    }
    fetchRuns();
  }, []);

  // Filter runs for current month
  const currentMonthRuns = useMemo(() => {
    const { start, end } = getCurrentMonthRange();
    return runs.filter((run) => {
      const runDate = new Date(run.start_at);
      return runDate >= start && runDate <= end;
    });
  }, [runs]);

  // Calculate metrics
  const metrics = useMemo(() => {
    if (currentMonthRuns.length === 0) {
      return {
        totalMiles: 0,
        numRuns: 0,
        avgPace: null as string | null,
      };
    }

    const totalMeters = currentMonthRuns.reduce(
      (sum, run) => sum + run.distance_meters,
      0
    );
    const totalMiles = metersToMiles(totalMeters);

    // Weighted average pace: total time / total distance
    // pace (sec/km) * distance (km) = time (sec)
    let totalTimeSec = 0;
    let totalDistanceKm = 0;
    for (const run of currentMonthRuns) {
      if (run.avg_pace_sec_per_km) {
        const distanceKm = run.distance_meters / 1000;
        totalTimeSec += run.avg_pace_sec_per_km * distanceKm;
        totalDistanceKm += distanceKm;
      }
    }

    const avgPace =
      totalDistanceKm > 0
        ? secPerKmToMinPerMile(totalTimeSec / totalDistanceKm)
        : null;

    return {
      totalMiles: Math.round(totalMiles * 10) / 10,
      numRuns: currentMonthRuns.length,
      avgPace,
    };
  }, [currentMonthRuns]);

  // Chart data: runs sorted by date
  const chartData = useMemo(() => {
    return [...currentMonthRuns]
      .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
      .map((run) => ({
        date: formatDateShort(run.start_at),
        miles: Math.round(metersToMiles(run.distance_meters) * 10) / 10,
        fullDate: new Date(run.start_at).toLocaleDateString(),
        title: run.title,
      }));
  }, [currentMonthRuns]);

  const currentMonth = new Date().toLocaleString('default', {
    month: 'long',
    year: 'numeric',
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error}</p>
          <Link
            href={PATHS.home}
            className="mt-4 inline-block text-blue-600 hover:underline"
          >
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Run Dashboard</h1>
              <p className="text-blue-100 text-sm mt-1">{currentMonth}</p>
            </div>
            <Link
              href={PATHS.home}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-400 rounded-lg transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Total Miles
            </h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {metrics.totalMiles}
            </p>
            <p className="text-sm text-gray-500 mt-1">this month</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Number of Runs
            </h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {metrics.numRuns}
            </p>
            <p className="text-sm text-gray-500 mt-1">this month</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Average Pace
            </h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {metrics.avgPace ? `${metrics.avgPace}` : '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">min/mile (weighted)</p>
          </div>
        </section>

        {/* Chart */}
        <section className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Distance Per Run
          </h2>
          {chartData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    stroke="#374151"
                    tick={{ fill: '#374151' }}
                  />
                  <YAxis
                    stroke="#374151"
                    tick={{ fill: '#374151' }}
                    label={{
                      value: 'Miles',
                      angle: -90,
                      position: 'insideLeft',
                      fill: '#374151',
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      color: '#111827',
                    }}
                    labelStyle={{ color: '#111827', fontWeight: 'bold' }}
                    formatter={(value) => [`${value} miles`, 'Distance']}
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return `${payload[0].payload.fullDate} - ${payload[0].payload.title}`;
                      }
                      return label;
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="miles"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, fill: '#1d4ed8' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No runs recorded this month.{' '}
              <Link href={PATHS.newRun} className="text-blue-600 hover:underline ml-1">
                Add your first run
              </Link>
            </div>
          )}
        </section>

        {/* Recent Runs Table */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Recent Runs This Month
          </h2>
          {currentMonthRuns.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Title
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Distance
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Pace
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {currentMonthRuns.slice(0, 10).map((run) => (
                    <tr key={run.id}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {new Date(run.start_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {run.title}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {(metersToMiles(run.distance_meters)).toFixed(1)} mi
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {run.avg_pace_sec_per_km
                          ? secPerKmToMinPerMile(run.avg_pace_sec_per_km)
                          : '—'}{' '}
                        /mi
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 capitalize">
                        {run.workout_type}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">No runs recorded this month.</p>
          )}
        </section>
      </main>
    </div>
  );
}

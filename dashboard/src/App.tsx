import { useEffect, useState } from 'react';
import { format, subDays } from 'date-fns';
import { getWeeklyStats, getHealth, type WeeklyStats } from './api';
import { StatCard } from './components/StatCard';
import { WeeklyChart } from './components/WeeklyChart';
import { DistanceChart } from './components/DistanceChart';
import { WorkHoursChart } from './components/WorkHoursChart';

function App() {
  const [stats, setStats] = useState<WeeklyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dbStatus, setDbStatus] = useState<'checking' | 'ok' | 'error'>('checking');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Check health first
        const health = await getHealth();
        setDbStatus(health.ok ? 'ok' : 'error');

        // Fetch stats for last 30 days
        const endDate = format(new Date(), 'yyyy-MM-dd');
        const startDate = format(subDays(new Date(), 30), 'yyyy-MM-dd');
        const data = await getWeeklyStats(startDate, endDate);
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        setDbStatus('error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-semibold text-lg">Error</h2>
          <p className="text-red-600 mt-2">{error}</p>
          <p className="text-red-500 text-sm mt-4">
            Make sure your API is running at http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}m`;
    return mins === 0 ? `${hours}h` : `${hours}h ${mins}m`;
  };

  const formatDistance = (meters: number) => {
    return `${(meters / 1000).toFixed(1)} km`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Goal Tracking Dashboard</h1>
              <p className="text-gray-500 text-sm mt-1">Last 30 days overview</p>
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Runs"
            value={stats?.total_runs ?? 0}
            subtitle={formatDistance(stats?.total_distance_meters ?? 0)}
            icon="🏃"
            color="blue"
          />
          <StatCard
            title="Running Time"
            value={formatDuration(stats?.total_run_duration_min ?? 0)}
            subtitle={`${stats?.total_runs ?? 0} sessions`}
            icon="⏱️"
            color="orange"
          />
          <StatCard
            title="Hangouts"
            value={stats?.total_hangouts ?? 0}
            subtitle="Social activities"
            icon="👥"
            color="green"
          />
          <StatCard
            title="Work Sessions"
            value={stats?.total_work_sessions ?? 0}
            subtitle={formatDuration(stats?.total_work_minutes ?? 0)}
            icon="💼"
            color="purple"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <WeeklyChart weeks={stats?.weeks ?? []} />
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <DistanceChart weeks={stats?.weeks ?? []} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <WorkHoursChart weeks={stats?.weeks ?? []} />
          </div>

          {/* Weekly Summary Table */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Summary</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-2 font-medium text-gray-600">Week</th>
                    <th className="text-center py-3 px-2 font-medium text-gray-600">Runs</th>
                    <th className="text-center py-3 px-2 font-medium text-gray-600">Distance</th>
                    <th className="text-center py-3 px-2 font-medium text-gray-600">Hangouts</th>
                    <th className="text-center py-3 px-2 font-medium text-gray-600">Work</th>
                  </tr>
                </thead>
                <tbody>
                  {[...(stats?.weeks ?? [])]
                    .sort((a, b) => new Date(b.week_start).getTime() - new Date(a.week_start).getTime())
                    .map((week) => (
                      <tr key={week.week_start} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-2 font-medium text-gray-900">
                          {format(new Date(week.week_start), 'MMM d')}
                        </td>
                        <td className="py-3 px-2 text-center text-blue-600 font-medium">
                          {week.runs_count}
                        </td>
                        <td className="py-3 px-2 text-center text-gray-600">
                          {(week.distance_meters / 1000).toFixed(1)} km
                        </td>
                        <td className="py-3 px-2 text-center text-green-600 font-medium">
                          {week.hangouts_count}
                        </td>
                        <td className="py-3 px-2 text-center text-purple-600 font-medium">
                          {formatDuration(week.work_minutes)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

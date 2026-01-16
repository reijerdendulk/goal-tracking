import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';
import type { WeeklyBreakdown } from '../api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface WeeklyChartProps {
  weeks: WeeklyBreakdown[];
}

export function WeeklyChart({ weeks }: WeeklyChartProps) {
  const sortedWeeks = [...weeks].sort(
    (a, b) => new Date(a.week_start).getTime() - new Date(b.week_start).getTime()
  );

  const labels = sortedWeeks.map((w) =>
    format(parseISO(w.week_start), 'MMM d')
  );

  const data = {
    labels,
    datasets: [
      {
        label: 'Runs',
        data: sortedWeeks.map((w) => w.runs_count),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderRadius: 4,
      },
      {
        label: 'Hangouts',
        data: sortedWeeks.map((w) => w.hangouts_count),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderRadius: 4,
      },
      {
        label: 'Work Sessions',
        data: sortedWeeks.map((w) => w.work_sessions_count),
        backgroundColor: 'rgba(168, 85, 247, 0.8)',
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Activities by Week',
        font: { size: 16 },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="h-80">
      <Bar data={data} options={options} />
    </div>
  );
}

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';
import type { WeeklyBreakdown } from '../api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface WorkHoursChartProps {
  weeks: WeeklyBreakdown[];
}

export function WorkHoursChart({ weeks }: WorkHoursChartProps) {
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
        label: 'Work Hours',
        data: sortedWeeks.map((w) => Math.round(w.work_minutes / 60 * 10) / 10),
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
        display: false,
      },
      title: {
        display: true,
        text: 'Weekly Work Hours',
        font: { size: 16 },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Hours',
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

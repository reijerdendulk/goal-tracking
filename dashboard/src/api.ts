import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export interface WeeklyBreakdown {
  week_start: string;
  runs_count: number;
  distance_meters: number;
  run_duration_min: number;
  hangouts_count: number;
  work_sessions_count: number;
  work_minutes: number;
}

export interface WeeklyStats {
  total_runs: number;
  total_distance_meters: number;
  total_run_duration_min: number;
  total_hangouts: number;
  total_work_sessions: number;
  total_work_minutes: number;
  weeks: WeeklyBreakdown[];
}

export interface HealthResponse {
  ok: boolean;
  db: string;
}

export const getWeeklyStats = async (startDate: string, endDate: string): Promise<WeeklyStats> => {
  const response = await api.get<WeeklyStats>('/stats/weekly', {
    params: { start_date: startDate, end_date: endDate },
  });
  return response.data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

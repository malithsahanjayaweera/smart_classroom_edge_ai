import type { HistoryResponse, LiveMetrics } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000/api/v1';

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getLiveMetrics() {
  return readJson<LiveMetrics>('/dashboard/live');
}

export function getHistory() {
  return readJson<HistoryResponse>('/dashboard/history');
}

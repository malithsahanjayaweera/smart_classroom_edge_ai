import { useEffect, useMemo, useState } from 'react';
import { getHistory, getLiveMetrics } from '../services/api';
import type { HistoryResponse, LiveMetrics } from '../types';

type DashboardData = {
  live: LiveMetrics | null;
  history: HistoryResponse;
  isLoading: boolean;
  error: string;
};

const EMPTY_HISTORY: HistoryResponse = {
  occupancyHistory: [],
  temperatureHistory: [],
};

export function useLiveMetrics() {
  const [state, setState] = useState<DashboardData>({
    live: null,
    history: EMPTY_HISTORY,
    isLoading: true,
    error: '',
  });

  useEffect(() => {
    let alive = true;

    const loadData = async () => {
      try {
        const [live, history] = await Promise.all([getLiveMetrics(), getHistory()]);
        if (!alive) {
          return;
        }

        setState({
          live,
          history,
          isLoading: false,
          error: '',
        });
      } catch (error) {
        if (!alive) {
          return;
        }

        setState((previous) => ({
          ...previous,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unable to load dashboard data',
        }));
      }
    };

    loadData();
    const intervalId = window.setInterval(loadData, 5000);

    return () => {
      alive = false;
      window.clearInterval(intervalId);
    };
  }, []);

  return useMemo(() => state, [state]);
}

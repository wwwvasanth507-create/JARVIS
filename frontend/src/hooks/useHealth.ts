/**
 * Hook for polling and managing API server connection health.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../services/apiClient';
import type { ConnectionStatus } from '../types/api';

export function useHealth(pollIntervalMs: number = 20000) {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const check = useCallback(async () => {
    try {
      const res = await apiClient.checkHealth();
      if (res.status === 'ok') {
        setStatus('connected');
      } else {
        setStatus('disconnected');
      }
    } catch {
      setStatus('disconnected');
    } finally {
      setLastCheck(new Date());
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    const run = async () => {
      try {
        const res = await apiClient.checkHealth();
        if (!ignore) {
          setStatus(res.status === 'ok' ? 'connected' : 'disconnected');
          setLastCheck(new Date());
        }
      } catch {
        if (!ignore) {
          setStatus('disconnected');
          setLastCheck(new Date());
        }
      }
    };

    run();
    const timer = setInterval(run, pollIntervalMs);
    return () => {
      ignore = true;
      clearInterval(timer);
    };
  }, [pollIntervalMs]);

  return {
    status,
    lastCheck,
    retry: check,
  };
}

/**
 * Hook for fetching and caching model introspection metadata.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../services/apiClient';
import type { ModelInfo, ConnectionStatus } from '../types/api';

export function useModelInfo(connectionStatus: ConnectionStatus) {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInfo = useCallback(async () => {
    if (connectionStatus !== 'connected') return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getModelInfo();
      setModelInfo(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch model info');
    } finally {
      setLoading(false);
    }
  }, [connectionStatus]);

  useEffect(() => {
    let ignore = false;
    if (connectionStatus === 'connected') {
      apiClient
        .getModelInfo()
        .then((data) => {
          if (!ignore) setModelInfo(data);
        })
        .catch((err: any) => {
          if (!ignore) setError(err.message || 'Failed to fetch model info');
        });
    }
    return () => {
      ignore = true;
    };
  }, [connectionStatus]);

  return {
    modelInfo,
    loading,
    error,
    refresh: fetchInfo,
  };
}

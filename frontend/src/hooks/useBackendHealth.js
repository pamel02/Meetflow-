import { useEffect, useState } from 'react';
import { monitoringService } from '../services';

/** Surveille GET /api/health en arriere-plan pour signaler un backend indisponible. */
export function useBackendHealth(intervalMs = 30000) {
  const [health, setHealth] = useState({ state: 'checking', components: null });

  useEffect(() => {
    let cancelled = false;
    let timer;

    const check = async () => {
      try {
        const data = await monitoringService.health();
        if (cancelled) return;
        setHealth({ state: data.status === 'ok' ? 'ok' : 'degraded', components: data.components });
      } catch {
        if (cancelled) return;
        setHealth({ state: 'unreachable', components: null });
      } finally {
        if (!cancelled) timer = setTimeout(check, intervalMs);
      }
    };

    check();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [intervalMs]);

  return health;
}

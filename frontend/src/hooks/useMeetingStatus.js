import { useEffect, useRef, useState } from 'react';
import { meetingService } from '../services';

/**
 * Interroge GET /api/meetings/{id}/status toutes les intervalMs tant que le
 * statut n'est pas "completed" ou "error". S'arrete proprement au demontage.
 */
export function useMeetingStatus(meetingId, { active = true, intervalMs = 2500 } = {}) {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!meetingId || !active) return undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await meetingService.status(meetingId);
        if (cancelled) return;
        setProgress(data);
        setError(null);
        if (data.status !== 'completed' && data.status !== 'error') {
          timerRef.current = setTimeout(poll, intervalMs);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err);
        timerRef.current = setTimeout(poll, intervalMs * 2);
      }
    };

    poll();
    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [meetingId, active, intervalMs]);

  return { progress, error };
}

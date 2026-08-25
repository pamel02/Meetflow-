import { useCallback, useEffect, useRef, useState } from 'react';
import { audioService } from '../services';

const SEGMENT_DURATION_MS = 60000; // chaque segment dure exactement 60s
const SEGMENT_OVERLAP_MS = 5000; // chevauchement de 5s entre deux segments
const SEGMENT_START_INTERVAL_MS = SEGMENT_DURATION_MS - SEGMENT_OVERLAP_MS; // 55s
const MAX_UPLOAD_ATTEMPTS = 5;

/**
 * Enregistre l'audio du microphone en le decoupant en segments de 60s qui se
 * chevauchent de 5s, et envoie chaque segment des qu'il est termine. Chaque
 * segment est poste vers POST /api/audio/upload-segment des sa fin : c'est
 * cet appel qui declenche cote backend la transcription Whisper du segment,
 * pendant que la reunion continue (le chevauchement de 5s permet au backend
 * de recoller les morceaux sans perdre de mots aux jonctions). Si l'envoi
 * echoue, le segment reste dans une file d'attente locale et est retente
 * automatiquement. Chaque segment est aussi garde localement (URL objet)
 * pour permettre une ecoute immediate dans l'onglet "Segments audio", dans
 * l'ordre chronologique, sans attendre le serveur.
 */
export function useAudioRecorder(meetingId) {
  const [micState, setMicState] = useState('idle'); // idle | requesting | granted | denied
  const [recordingState, setRecordingState] = useState('idle'); // idle | recording | paused | stopped
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [segmentsCreated, setSegmentsCreated] = useState(0);
  const [estimatedBytes, setEstimatedBytes] = useState(0);
  const [pendingUploads, setPendingUploads] = useState(0);
  const [lastError, setLastError] = useState(null);
  const [localSegments, setLocalSegments] = useState([]); // { segmentNumber, url, size } tries dans l'ordre

  const streamRef = useRef(null);
  const startIntervalRef = useRef(null);
  const clockIntervalRef = useRef(null);
  const activeRecordersRef = useRef([]); // { recorder, segmentNumber, stopTimer }
  const segmentCounterRef = useRef(0);
  const pausedRef = useRef(false);
  const mimeTypeRef = useRef('audio/webm');
  const objectUrlsRef = useRef([]);
  const failedUploadsRef = useRef(0);

  // Libere les URL objet crees pour la lecture locale quand le composant se demonte.
  useEffect(() => {
    const objectUrls = objectUrlsRef.current;
    return () => {
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  const pickMimeType = () => {
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
    for (const c of candidates) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(c)) return c;
    }
    return '';
  };

  const uploadWithRetry = useCallback(
    async (segmentNumber, blob) => {
      setPendingUploads((n) => n + 1);
      const extension = mimeTypeRef.current.includes('ogg') ? 'ogg' : mimeTypeRef.current.includes('mp4') ? 'm4a' : 'webm';
      const filename = `segment_${String(segmentNumber).padStart(4, '0')}.${extension}`;
      try {
        for (let attempt = 0; attempt < MAX_UPLOAD_ATTEMPTS; attempt += 1) {
          try {
            await audioService.uploadSegment(meetingId, segmentNumber, blob, filename);
            return;
          } catch (error) {
            if (attempt === MAX_UPLOAD_ATTEMPTS - 1) throw error;
            setLastError("Un segment n'a pas pu etre envoye, nouvelle tentative en cours.");
            const delay = Math.min(30000, 2000 * 2 ** attempt);
            await new Promise((resolve) => setTimeout(resolve, delay));
          }
        }
      } finally {
        setPendingUploads((n) => Math.max(0, n - 1));
      }
    },
    [meetingId]
  );

  const startOneSegment = useCallback(() => {
    if (!streamRef.current) return;
    const segmentNumber = segmentCounterRef.current;
    segmentCounterRef.current += 1;

    const recorder = new MediaRecorder(streamRef.current, mimeTypeRef.current ? { mimeType: mimeTypeRef.current } : undefined);
    const chunks = [];
    let resolveCompletion;
    const completionPromise = new Promise((resolve) => {
      resolveCompletion = resolve;
    });
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunks.push(e.data);
    };
    recorder.onstop = async () => {
      const blob = new Blob(chunks, { type: mimeTypeRef.current || 'audio/webm' });
      setEstimatedBytes((b) => b + blob.size);
      setSegmentsCreated((n) => n + 1);

      const url = URL.createObjectURL(blob);
      objectUrlsRef.current.push(url);
      setLocalSegments((prev) =>
        [...prev, { segmentNumber, url, size: blob.size }].sort((a, b) => a.segmentNumber - b.segmentNumber)
      );

      try {
        await uploadWithRetry(segmentNumber, blob);
      } catch {
        failedUploadsRef.current += 1;
        setLastError("Un segment n'a pas pu etre envoye apres plusieurs tentatives.");
      } finally {
        activeRecordersRef.current = activeRecordersRef.current.filter((r) => r.segmentNumber !== segmentNumber);
        resolveCompletion();
      }
    };
    recorder.start();

    const stopTimer = setTimeout(() => {
      if (recorder.state !== 'inactive') recorder.stop();
    }, SEGMENT_DURATION_MS);

    activeRecordersRef.current.push({ recorder, segmentNumber, stopTimer, completionPromise });
  }, [uploadWithRetry]);

  const start = useCallback(async () => {
    setLastError(null);
    setMicState('requesting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      mimeTypeRef.current = pickMimeType();
      setMicState('granted');
    } catch {
      setMicState('denied');
      setLastError("Acces au microphone refuse. Autorisez le microphone pour demarrer la reunion.");
      return;
    }

    setRecordingState('recording');
    pausedRef.current = false;
    segmentCounterRef.current = 0;
    failedUploadsRef.current = 0;
    setSegmentsCreated(0);
    setEstimatedBytes(0);
    setElapsedSeconds(0);
    setLocalSegments([]);

    startOneSegment();
    startIntervalRef.current = setInterval(startOneSegment, SEGMENT_START_INTERVAL_MS);
    clockIntervalRef.current = setInterval(() => {
      if (!pausedRef.current) setElapsedSeconds((s) => s + 1);
    }, 1000);
  }, [startOneSegment]);

  const pause = useCallback(() => {
    pausedRef.current = true;
    setRecordingState('paused');
    if (startIntervalRef.current) clearInterval(startIntervalRef.current);
    activeRecordersRef.current.forEach(({ recorder }) => {
      if (recorder.state === 'recording' && recorder.pause) recorder.pause();
    });
  }, []);

  const resume = useCallback(() => {
    pausedRef.current = false;
    setRecordingState('recording');
    activeRecordersRef.current.forEach(({ recorder }) => {
      if (recorder.state === 'paused' && recorder.resume) recorder.resume();
    });
    startIntervalRef.current = setInterval(startOneSegment, SEGMENT_START_INTERVAL_MS);
  }, [startOneSegment]);

  const stop = useCallback(async () => {
    setRecordingState('stopped');
    if (startIntervalRef.current) clearInterval(startIntervalRef.current);
    if (clockIntervalRef.current) clearInterval(clockIntervalRef.current);
    const activeSegments = [...activeRecordersRef.current];
    activeSegments.forEach(({ recorder, stopTimer }) => {
      clearTimeout(stopTimer);
      if (recorder.state !== 'inactive') recorder.stop();
    });
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    await Promise.all(activeSegments.map(({ completionPromise }) => completionPromise));
    if (failedUploadsRef.current > 0) {
      throw new Error("Certains segments audio n'ont pas pu etre envoyes.");
    }
    try {
      await audioService.endMeeting(meetingId);
    } catch (err) {
      setLastError("La fin de reunion n'a pas pu etre signalee au serveur. Reessayez.");
      throw err;
    }
  }, [meetingId]);

  return {
    micState,
    recordingState,
    elapsedSeconds,
    segmentsCreated,
    estimatedBytes,
    pendingUploads,
    lastError,
    localSegments,
    start,
    pause,
    resume,
    stop,
  };
}

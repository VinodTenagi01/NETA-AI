import { useState, useEffect, useRef, useCallback } from 'react';

export function useAutoRefresh(callback, intervalSeconds = 60) {
  const [countdown, setCountdown] = useState(intervalSeconds);
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    const tick = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          cbRef.current();
          return intervalSeconds;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [intervalSeconds]);

  const triggerNow = useCallback(() => {
    cbRef.current();
    setCountdown(intervalSeconds);
  }, [intervalSeconds]);

  return { countdown, triggerNow };
}

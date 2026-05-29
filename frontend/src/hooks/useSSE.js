import { useEffect, useRef, useCallback } from 'react';
import { getAccessToken } from '../api/client';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

/**
 * Subscribe to a Server-Sent Events endpoint.
 *
 * @param {string} path - API path e.g. '/sse/alerts'
 * @param {Object.<string, function>} handlers - Event type → handler fn
 * @param {object} options - { enabled: bool, reconnectMs: number }
 */
export function useSSE(path, handlers, { enabled = true, reconnectMs = 5000 } = {}) {
  const esRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(false);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    const token = getAccessToken();
    if (!token || !path) return;

    cleanup();

    const url = `${API_BASE}/api${path}?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onerror = () => {
      es.close();
      esRef.current = null;
      if (mountedRef.current) {
        reconnectTimerRef.current = setTimeout(connect, reconnectMs);
      }
    };

    Object.keys(handlersRef.current).forEach(eventType => {
      es.addEventListener(eventType, e => {
        try {
          const data = JSON.parse(e.data);
          handlersRef.current[eventType]?.(data);
        } catch {
          handlersRef.current[eventType]?.(e.data);
        }
      });
    });
  }, [path, reconnectMs, cleanup]);

  useEffect(() => {
    if (!enabled) return;
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [enabled, connect, cleanup]);

  return {
    close: cleanup,
  };
}

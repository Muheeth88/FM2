import { useState, useEffect, useRef, useCallback } from 'react';
import type { WSProgressMessage } from '../types';

const WS_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'ws://127.0.0.1:8000'
    : `ws://${window.location.hostname}:8000`;

interface AnalysisStreamState {
    step: string;
    progress: number;
    logs: string[];
    error: string | null;
    trace: string | null;
    isComplete: boolean;
    isConnected: boolean;
}

export function useAnalysisStream(sessionId: string | null, enabled: boolean) {
    const [state, setState] = useState<AnalysisStreamState>({
        step: '',
        progress: 0,
        logs: [],
        error: null,
        trace: null,
        isComplete: false,
        isConnected: false,
    });

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const connect = useCallback(() => {
        if (!sessionId || !enabled) return;

        // Clean up any existing connection
        if (wsRef.current) {
            console.log('Closing existing WebSocket connection before creating new one');
            wsRef.current.close(1000, 'Intentional closure');
            wsRef.current = null;
        }

        console.log(`Connecting to WebSocket: ${WS_BASE_URL}/ws/sessions/${sessionId}`);
        const ws = new WebSocket(`${WS_BASE_URL}/ws/sessions/${sessionId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            if (wsRef.current !== ws) return;
            console.log('WebSocket connection established');
            setState(prev => ({ ...prev, isConnected: true }));
        };

        ws.onmessage = (event) => {
            if (wsRef.current !== ws) return;
            try {
                const msg: WSProgressMessage = JSON.parse(event.data);

                switch (msg.type) {
                    case 'progress':
                        setState(prev => ({
                            ...prev,
                            step: msg.step || prev.step,
                            progress: msg.progress ?? prev.progress,
                            logs: msg.message
                                ? [...prev.logs, `[${msg.step}] ${msg.message}`]
                                : prev.logs,
                        }));
                        break;

                    case 'log':
                        setState(prev => ({
                            ...prev,
                            logs: msg.message
                                ? [...prev.logs, msg.message]
                                : prev.logs,
                        }));
                        break;

                    case 'error':
                        setState(prev => ({
                            ...prev,
                            error: msg.error || 'Unknown error',
                            trace: msg.trace || null,
                            logs: [...prev.logs, `❌ Error: ${msg.error}`],
                        }));
                        break;

                    case 'complete':
                        setState(prev => ({
                            ...prev,
                            step: 'Complete',
                            progress: 100,
                            isComplete: true,
                            logs: [...prev.logs, '✅ Analysis completed successfully'],
                        }));
                        break;
                }
            } catch (e) {
                console.error('Failed to parse WS message:', e);
            }
        };

        ws.onclose = (event) => {
            if (wsRef.current === ws) {
                console.log(`WebSocket connection closed: ${event.reason || 'No reason'}`);
                setState(prev => ({ ...prev, isConnected: false }));
                wsRef.current = null;

                // Auto-reconnect if not intentionally closed, not complete, and no error
                if (enabled && event.code !== 1000) {
                    setState(prev => {
                        if (!prev.isComplete && !prev.error) {
                            console.log('Scheduling WebSocket reconnection in 2s...');
                            reconnectTimeoutRef.current = setTimeout(connect, 2000);
                        }
                        return prev;
                    });
                }
            } else {
                console.log('Ignoring onclose for inactive WebSocket');
            }
        };

        ws.onerror = (error) => {
            if (wsRef.current !== ws) return;
            console.error('WebSocket error:', error);
        };
    }, [sessionId, enabled]);

    useEffect(() => {
        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connect]);

    const reset = useCallback(() => {
        setState({
            step: '',
            progress: 0,
            logs: [],
            error: null,
            trace: null,
            isComplete: false,
            isConnected: false,
        });
    }, []);

    return { ...state, reset };
}

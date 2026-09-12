'use client';

import { useEffect, useRef, useState } from 'react';
import { Account, CustomerInteraction } from '@/types/pipeline';

interface WebSocketMessage {
  event: string;
  data: CustomerInteraction | Account | Record<string, unknown>;
}

interface UseWebSocketOptions {
  onInteractionCreated?: (interaction: CustomerInteraction) => void;
  onInteractionProcessing?: (interaction: CustomerInteraction) => void;
  onInteractionCompleted?: (interaction: CustomerInteraction) => void;
  onInteractionFailed?: (interaction: CustomerInteraction) => void;
  onAccountUpdated?: (account: Account) => void;
  onInboxCleared?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const optionsRef = useRef(options);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/inbox';

    function connect() {
      try {
        const socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const msg: WebSocketMessage = JSON.parse(event.data);
            switch (msg.event) {
              case 'INTERACTION_CREATED':
                optionsRef.current.onInteractionCreated?.(msg.data as CustomerInteraction);
                break;
              case 'INTERACTION_PROCESSING':
                optionsRef.current.onInteractionProcessing?.(msg.data as CustomerInteraction);
                break;
              case 'INTERACTION_COMPLETED':
                optionsRef.current.onInteractionCompleted?.(msg.data as CustomerInteraction);
                break;
              case 'INTERACTION_FAILED':
                optionsRef.current.onInteractionFailed?.(msg.data as CustomerInteraction);
                break;
              case 'ACCOUNT_UPDATED':
                optionsRef.current.onAccountUpdated?.(msg.data as Account);
                break;
              case 'INBOX_CLEARED':
                optionsRef.current.onInboxCleared?.();
                break;
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e);
          }
        };

        socket.onclose = () => {
          setIsConnected(false);
          // Auto reconnect after 2 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 2000);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch (err) {
        console.warn('WebSocket connection error:', err);
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { isConnected };
}

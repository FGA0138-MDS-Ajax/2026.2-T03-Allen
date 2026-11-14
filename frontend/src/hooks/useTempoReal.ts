import { useEffect, useRef } from 'react';
import { obterToken } from '../servicos/api';

export interface EventoTransacaoCriada {
  tipo: 'transacao_criada';
  dados: {
    id: string;
    valor: string;
    tipo: 'gasto' | 'entrada';
    categoria: string;
    criado_em: string;
  };
}

export function useTempoReal(
  aoReceberTransacao?: (evento: EventoTransacaoCriada) => void
) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = obterToken();
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host =
      import.meta.env.VITE_WS_URL ||
      `${protocol}//${window.location.hostname}:8000/ws`;

    try {
      const ws = new WebSocket(host);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ token }));
      };

      ws.onmessage = (event) => {
        try {
          const mensagem = JSON.parse(event.data);
          if (mensagem.tipo === 'transacao_criada' && aoReceberTransacao) {
            aoReceberTransacao(mensagem);
          }
        } catch {
          // Ignora mensagens malformadas
        }
      };

      ws.onerror = () => {
        // Conexão silenciosa caso o backend/ws não esteja rodando
      };

      return () => {
        ws.close();
      };
    } catch {
      // Falha silenciosa se WebSocket não estiver disponível
    }
  }, [aoReceberTransacao]);

  return wsRef;
}

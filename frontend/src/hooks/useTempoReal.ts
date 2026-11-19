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
  const aoReceberRef = useRef(aoReceberTransacao);

  useEffect(() => {
    aoReceberRef.current = aoReceberTransacao;
  }, [aoReceberTransacao]);

  useEffect(() => {
    const token = obterToken();
    if (!token) return;

    let ativo = true;
    let reconexao: number | undefined;

    const criarUrl = () => {
      if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;

      const apiUrl = import.meta.env.VITE_API_URL;
      if (apiUrl && /^https?:/.test(apiUrl)) {
        const api = new URL(apiUrl);
        return `${api.protocol === 'https:' ? 'wss:' : 'ws:'}//${api.host}/ws`;
      }

      const protocol =
        window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}/ws`;
    };

    const conectar = () => {
      if (!ativo) return;
    
      try {
        const ws = new WebSocket(criarUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          ws.send(JSON.stringify({ token }));
        };

        ws.onmessage = (event) => {
          try {
            const mensagem = JSON.parse(event.data);
            if (mensagem.tipo === 'transacao_criada' && aoReceberRef.current) {
              aoReceberRef.current(mensagem);
            }
          } catch {

          }
        };

        ws.onclose = () => {
          if (wsRef.current === ws) wsRef.current = null;
          if (ativo) reconexao = window.setTimeout(conectar, 3000);
        };

        ws.onerror = () => { 

        };
      } catch {

      }
    };

    conectar();

    return () => {
      ativo = false;
      if (reconexao !== undefined) window.clearTimeout(reconexao);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  return wsRef;
}

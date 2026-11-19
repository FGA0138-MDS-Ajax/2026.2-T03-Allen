/**
 * Gastos e recebimentos do usuário, gravados na API (RF08, RF10, RF19).
 * O app não guarda dados financeiros no aparelho (Documento de Arquitetura).
 */

import { requisicao } from './api';

export type TipoTransacaoApi = 'entrada' | 'saida';
export type OrigemApp = 'manual' | 'qrcode_nf';

export interface TransacaoSaida {
  id: string;
  tipo: TipoTransacaoApi;
  valor: string; // decimal em reais, ex.: "35.00"
  data: string; // AAAA-MM-DD
  descricao: string | null;
  categoria_id: number | null;
  origem: string;
  criado_em: string;
}

export interface TransacaoEntrada {
  tipo: TipoTransacaoApi;
  valor: string;
  origem?: OrigemApp;
  data?: string;
  descricao?: string | null;
  categoria_id?: number | null;
}

export interface TransacaoEdicao {
  valor?: string;
  data?: string;
  descricao?: string | null;
  categoria_id?: number | null;
}

/** Totais do mês em reais (texto decimal). O saldo pode ser negativo. */
export interface SaldoMes {
  mes: string;
  entradas: string;
  gastos: string;
  contas: string;
  saldo: string;
}

/** Centavos inteiros para o texto decimal que a API espera ("1234" → "12.34"). */
export const centavosParaValor = (centavos: number): string =>
  (Math.round(centavos) / 100).toFixed(2);

/** Texto decimal da API para centavos inteiros ("12.34" → 1234). */
export const valorParaCentavos = (valor: string | number): number =>
  Math.round(Number(valor) * 100);

export const listarTransacoes = (): Promise<TransacaoSaida[]> =>
  requisicao<TransacaoSaida[]>('/api/v1/transacoes');

export const anotarTransacao = (
  dados: TransacaoEntrada
): Promise<TransacaoSaida> =>
  requisicao<TransacaoSaida>('/api/v1/transacoes', {
    method: 'POST',
    body: JSON.stringify(dados),
  });

export const editarTransacao = (
  id: string,
  dados: TransacaoEdicao
): Promise<TransacaoSaida> =>
  requisicao<TransacaoSaida>(`/api/v1/transacoes/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(dados),
  });

export const excluirTransacao = async (id: string): Promise<void> => {
  await requisicao(`/api/v1/transacoes/${id}`, { method: 'DELETE' });
};

/** Saldo de um mês (AAAA-MM). Sem mês, a API usa o mês atual de Brasília. */
export const obterSaldoMes = (mes?: string): Promise<SaldoMes> =>
  requisicao<SaldoMes>(
    `/api/v1/transacoes/saldo${mes ? `?mes=${encodeURIComponent(mes)}` : ''}`
  );

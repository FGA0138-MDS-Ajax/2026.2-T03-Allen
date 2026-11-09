/**
 * Serviço de contas a pagar (RF25, RF30 / US09, US10).
 * Integração com os endpoints GET, POST e PATCH /api/v1/contas.
 */

import { requisicao } from './api';

export type StatusConta = 'a_vencer' | 'paga' | 'em_atraso';

export interface ContaSaida {
  id: string;
  descricao: string | null;
  valor: number | string;
  vencimento_em: string;
  categoria_id: number | null;
  status: StatusConta;
  pagamento_em?: string | null;
  criado_em: string;
}

export interface ContaCadastroEntrada {
  vencimento_em: string; // formato YYYY-MM-DD
  valor: number;
  descricao?: string | null;
  categoria_id?: number | null;
}

export interface ContaPagamentoEntrada {
  paga: boolean;
}

/**
 * Lista as contas a pagar do usuário autenticado (RF25 / US09).
 */
export const listarContas = async (): Promise<ContaSaida[]> => {
  return await requisicao<ContaSaida[]>('/api/v1/contas', {
    method: 'GET',
  });
};

/**
 * Cadastra uma nova conta a pagar (RF25 / US09).
 */
export const cadastrarConta = async (
  dados: ContaCadastroEntrada
): Promise<ContaSaida> => {
  return await requisicao<ContaSaida>('/api/v1/contas', {
    method: 'POST',
    body: JSON.stringify(dados),
  });
};

/**
 * Marca ou desfaz o pagamento de uma conta (RF30 / US10).
 * Endpoint: PATCH /api/v1/contas/{id}/pagamento
 */
export const definirPagamentoConta = async (
  id: string,
  paga: boolean
): Promise<ContaSaida> => {
  return await requisicao<ContaSaida>(`/api/v1/contas/${id}/pagamento`, {
    method: 'PATCH',
    body: JSON.stringify({ paga }),
  });
};

/**
 * Serviço de contas a pagar (RF25 / US09).
 * Integração com os endpoints GET e POST /api/v1/contas.
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
  criado_em: string;
}

export interface ContaCadastroEntrada {
  vencimento_em: string; // formato YYYY-MM-DD
  valor: number;
  descricao?: string | null;
  categoria_id?: number | null;
}

/**
 * Lista as contas a pagar do usuário autenticado.
 */
export const listarContas = async (): Promise<ContaSaida[]> => {
  return await requisicao<ContaSaida[]>('/api/v1/contas', {
    method: 'GET',
  });
};

/**
 * Cadastra uma nova conta a pagar.
 */
export const cadastrarConta = async (
  dados: ContaCadastroEntrada
): Promise<ContaSaida> => {
  return await requisicao<ContaSaida>('/api/v1/contas', {
    method: 'POST',
    body: JSON.stringify(dados),
  });
};

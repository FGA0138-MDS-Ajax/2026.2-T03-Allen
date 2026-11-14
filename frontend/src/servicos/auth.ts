/**
 * Serviço de autenticação com o backend do Vero.
 * Integração com os endpoints de autenticação e cadastro (US01 / US02 / RF01 / RF03).
 */

import { extrairDigitos } from '../utils/telefone';
import { ErroApi, requisicao, salvarToken } from './api';

export interface RespostaToken {
  access_token: string;
  token_type: string;
  expira_em: number;
}

export interface CadastroEntrada {
  nome: string;
  telefone: string;
  pin: string;
  email?: string;
}

export interface RespostaUsuario {
  id: string;
  nome: string;
  telefone: string;
  email?: string | null;
  tem_pin?: boolean;
}

export const cadastrarUsuario = async (
  dados: CadastroEntrada
): Promise<RespostaUsuario> => {
  const digitosTelefone = extrairDigitos(dados.telefone);

  const resposta = await requisicao<RespostaUsuario>('/api/v1/auth/cadastro', {
    method: 'POST',
    body: JSON.stringify({
      nome: dados.nome,
      telefone: digitosTelefone,
      pin: dados.pin,
      ...(dados.email ? { email: dados.email } : {}),
    }),
  });

  return resposta;
};

export const entrarComPin = async (
  telefone: string,
  pin: string
): Promise<RespostaToken> => {
  const digitosTelefone = extrairDigitos(telefone);
  const corpo = JSON.stringify({
    telefone: digitosTelefone,
    pin,
  });

  try {
    const resposta = await requisicao<RespostaToken>('/api/v1/auth/pin', {
      method: 'POST',
      body: corpo,
    });
    salvarToken(resposta.access_token);
    return resposta;
  } catch (erro) {
    // Compatibilidade: se /api/v1/auth/pin retornar 404, tenta /api/v1/auth/login (PR #65 / #66)
    if (erro instanceof ErroApi && erro.status === 404) {
      const resposta = await requisicao<RespostaToken>('/api/v1/auth/login', {
        method: 'POST',
        body: corpo,
      });
      salvarToken(resposta.access_token);
      return resposta;
    }
    throw erro;
  }
};

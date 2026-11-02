/**
 * Serviço de autenticação com o backend do Vero.
 * Integração com o endpoint POST /api/v1/auth/pin (US02 / RF01).
 */

import { extrairDigitos } from '../utils/telefone';
import { requisicao, salvarToken } from './api';

export interface RespostaToken {
  access_token: string;
  token_type: string;
  expira_em: number;
}

export const entrarComPin = async (
  telefone: string,
  pin: string
): Promise<RespostaToken> => {
  const digitosTelefone = extrairDigitos(telefone);

  const resposta = await requisicao<RespostaToken>('/api/v1/auth/pin', {
    method: 'POST',
    body: JSON.stringify({
      telefone: digitosTelefone,
      pin,
    }),
  });

  salvarToken(resposta.access_token);
  return resposta;
};

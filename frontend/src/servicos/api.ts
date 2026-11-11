/**
 * Cliente HTTP base para comunicação com o backend FastAPI do Vero.
 */

export class ErroApi extends Error {
  public status: number;
  public detalhe: string;

  constructor(status: number, detalhe: string) {
    super(detalhe);
    this.name = 'ErroApi';
    this.status = status;
    this.detalhe = detalhe;
  }
}

const CHAVE_TOKEN = 'vero_token';
const CHAVE_SESSAO = 'vero_sessao_ativa';

export const obterToken = (): string | null => {
  return localStorage.getItem(CHAVE_TOKEN);
};

export const salvarToken = (token: string): void => {
  localStorage.setItem(CHAVE_TOKEN, token);
  localStorage.setItem(CHAVE_SESSAO, 'true');
  document.cookie = `vero_session=true; path=/; max-age=604800`;
};

export const limparSessao = (): void => {
  localStorage.removeItem(CHAVE_TOKEN);
  localStorage.removeItem(CHAVE_SESSAO);
  document.cookie =
    'vero_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
};

export const estaAutenticado = (): boolean => {
  return !!obterToken();
};

export const requisicao = async <T>(
  caminho: string,
  opcoes: RequestInit = {}
): Promise<T> => {
  const token = obterToken();
  const headers = new Headers(opcoes.headers || {});

  if (!headers.has('Content-Type') && !(opcoes.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const url = caminho.startsWith('http')
    ? caminho
    : `${import.meta.env.VITE_API_URL || ''}${caminho}`;

  let resposta: Response;
  try {
    resposta = await fetch(url, {
      ...opcoes,
      headers,
    });
  } catch {
    throw new ErroApi(
      0,
      'Não foi possível conectar ao servidor. Verifique sua conexão com a internet.'
    );
  }

  if (!resposta.ok) {
    let mensagemErro =
      'Ocorreu um erro inesperado ao processar sua solicitação.';
    try {
      const corpoErro = await resposta.json();
      if (typeof corpoErro?.detail === 'string') {
        mensagemErro = corpoErro.detail;
      } else if (
        Array.isArray(corpoErro?.detail) &&
        corpoErro.detail.length > 0
      ) {
        mensagemErro = corpoErro.detail[0]?.msg || mensagemErro;
      }
    } catch {
      // Se não for JSON (ex.: erro de proxy 500/502 do Vite com ECONNREFUSED)
      if (
        resposta.status === 502 ||
        resposta.status === 503 ||
        resposta.status === 504
      ) {
        mensagemErro =
          'O servidor backend (porta 8000) não está em execução neste computador. Inicie o backend ou verifique a conexão.';
      } else if (resposta.status === 500) {
        mensagemErro =
          'Ocorreu um erro interno no servidor (500). Verifique os logs do backend.';
      } else if (resposta.statusText) {
        mensagemErro = resposta.statusText;
      }
    }

    if (resposta.status === 401) {
      limparSessao();
    }

    throw new ErroApi(resposta.status, mensagemErro);
  }

  if (resposta.status === 204) {
    return {} as T;
  }

  return (await resposta.json()) as T;
};

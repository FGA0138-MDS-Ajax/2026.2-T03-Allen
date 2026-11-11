import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  obterToken,
  salvarToken,
  limparSessao,
  estaAutenticado,
  requisicao,
  ErroApi,
} from './api';
import { entrarComPin } from './auth';
import { listarContas, cadastrarConta, definirPagamentoConta } from './contas';

describe('Serviços de API e Autenticação', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('gerencia o token e estado de autenticação no localStorage', () => {
    expect(estaAutenticado()).toBe(false);
    expect(obterToken()).toBeNull();

    salvarToken('token-jwt-teste');
    expect(estaAutenticado()).toBe(true);
    expect(obterToken()).toBe('token-jwt-teste');

    limparSessao();
    expect(estaAutenticado()).toBe(false);
    expect(obterToken()).toBeNull();
  });

  it('injeta Authorization Bearer quando autenticado', async () => {
    salvarToken('meu-token-secreto');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'sucesso' }),
    });
    global.fetch = mockFetch;

    const resultado = await requisicao<{ status: string }>('/api/v1/teste');

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/teste',
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );

    const headersChamados = mockFetch.mock.calls[0][1].headers as Headers;
    expect(headersChamados.get('Authorization')).toBe('Bearer meu-token-secreto');
    expect(resultado).toEqual({ status: 'sucesso' });
  });

  it('lança ErroApi com mensagem de erro do backend', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'PIN incorreto.' }),
    });

    try {
      await entrarComPin('61999998888', '1234');
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(ErroApi);
      expect((e as ErroApi).detalhe).toBe('PIN incorreto.');
      expect((e as ErroApi).status).toBe(401);
    }
  });

  it('faz login com PIN e salva o token com sucesso', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: 'token-gerado',
        token_type: 'bearer',
        expira_em: 3600,
      }),
    });

    const resposta = await entrarComPin('(61) 99999-8888', '1234');
    expect(resposta.access_token).toBe('token-gerado');
    expect(obterToken()).toBe('token-gerado');
  });

  it('faz fallback para /api/v1/auth/login quando /api/v1/auth/pin retorna 404', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not Found' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: 'token-fallback-login',
          token_type: 'bearer',
          expira_em: 7200,
        }),
      });

    const resposta = await entrarComPin('(61) 99999-8888', '1234');
    expect(resposta.access_token).toBe('token-fallback-login');
    expect(obterToken()).toBe('token-fallback-login');
  });

  it('lista e cadastra contas a pagar (RF25)', async () => {
    salvarToken('token-valido');

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [
        {
          id: '123',
          descricao: 'Conta de Luz',
          valor: 150.5,
          vencimento_em: '2026-11-10',
          categoria_id: null,
          status: 'a_vencer',
          pagamento_em: null,
          criado_em: '2026-11-01T10:00:00',
        },
      ],
    });

    const contas = await listarContas();
    expect(contas).toHaveLength(1);
    expect(contas[0].descricao).toBe('Conta de Luz');

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({
        id: '124',
        descricao: 'Conta de Água',
        valor: 80.0,
        vencimento_em: '2026-11-15',
        categoria_id: null,
        status: 'a_vencer',
        pagamento_em: null,
        criado_em: '2026-11-01T10:00:00',
      }),
    });

    const novaConta = await cadastrarConta({
      descricao: 'Conta de Água',
      valor: 80.0,
      vencimento_em: '2026-11-15',
    });
    expect(novaConta.id).toBe('124');
  });

  it('marca e desfaz o pagamento de uma conta (RF30)', async () => {
    salvarToken('token-valido');

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: '123',
        descricao: 'Conta de Luz',
        valor: 150.5,
        vencimento_em: '2026-11-10',
        categoria_id: null,
        status: 'paga',
        pagamento_em: '2026-11-09T10:00:00',
        criado_em: '2026-11-01T10:00:00',
      }),
    });

    const contaPaga = await definirPagamentoConta('123', true);
    expect(contaPaga.status).toBe('paga');
    expect(contaPaga.pagamento_em).toBe('2026-11-09T10:00:00');

    // Desfaz o pagamento
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: '123',
        descricao: 'Conta de Luz',
        valor: 150.5,
        vencimento_em: '2026-11-10',
        categoria_id: null,
        status: 'a_vencer',
        pagamento_em: null,
        criado_em: '2026-11-01T10:00:00',
      }),
    });

    const contaNaoPaga = await definirPagamentoConta('123', false);
    expect(contaNaoPaga.status).toBe('a_vencer');
    expect(contaNaoPaga.pagamento_em).toBeNull();
  });
});

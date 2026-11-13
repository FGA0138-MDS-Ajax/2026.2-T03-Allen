import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  render,
  screen,
  waitFor,
  fireEvent,
  act,
} from '@testing-library/react';
import App from './App';
import * as servicos from './servicos';

vi.mock('./servicos', async () => {
  const actual = await vi.importActual('./servicos');
  return {
    ...actual,
    estaAutenticado: vi.fn(),
    listarContas: vi.fn().mockResolvedValue([]),
  };
});

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('deve renderizar a tela de boas-vindas Vero quando não estiver autenticado', () => {
    vi.mocked(servicos.estaAutenticado).mockReturnValue(false);
    render(<App />);
    expect(screen.getByText('Vero')).toBeInTheDocument();
    expect(
      screen.getByText('Suas finanças na palma da sua mão.')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /fazer login/i })
    ).toBeInTheDocument();
  });

  it('deve exibir a tela de contas a pagar quando estiver autenticado', async () => {
    vi.mocked(servicos.estaAutenticado).mockReturnValue(true);
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/minhas contas a pagar/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole('button', { name: /cadastrar nova conta/i })
    ).toBeInTheDocument();
  });

  it('abre a explicação em áudio no primeiro acesso e permite reabrir (US13)', async () => {
    vi.mocked(servicos.estaAutenticado).mockReturnValue(true);
    const { unmount } = render(<App />);
    // Deixa a tela de contas terminar de carregar
    await act(async () => {});

    expect(
      await screen.findByRole('dialog', { name: /boas-vindas ao vero/i })
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole('button', { name: /sair da explicação/i })
    );
    expect(screen.queryByRole('dialog', { name: /boas-vindas/i })).toBeNull();
    unmount();

    // Já ouviu: não abre sozinha de novo, mas o botão reabre
    render(<App />);
    await act(async () => {});
    expect(screen.queryByRole('dialog', { name: /boas-vindas/i })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /ouvir explicação/i }));
    expect(
      screen.getByRole('dialog', { name: /boas-vindas ao vero/i })
    ).toBeInTheDocument();
  });

  it('não abre a explicação antes do login', () => {
    vi.mocked(servicos.estaAutenticado).mockReturnValue(false);
    render(<App />);
    expect(screen.queryByRole('dialog', { name: /boas-vindas/i })).toBeNull();
  });
});

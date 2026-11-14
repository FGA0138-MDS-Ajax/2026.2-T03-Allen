import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
});

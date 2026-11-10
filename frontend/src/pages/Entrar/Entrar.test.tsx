import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Entrar } from './Entrar';
import * as servicos from '../../servicos';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/entrar',
  }),
}));

vi.mock('../../servicos', () => ({
  entrarComPin: vi.fn(),
  estaAutenticado: vi.fn(),
  limparSessao: vi.fn(),
  ErroApi: class ErroApi extends Error {
    detalhe: string;
    constructor(detalhe: string) {
      super(detalhe);
      this.detalhe = detalhe;
    }
  },
}));

describe('Página Entrar (Login no Vero com Teclado Físico)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('permite digitar o PIN usando o teclado físico do computador', async () => {
    vi.mocked(servicos.entrarComPin).mockResolvedValue({
      access_token: 'fake-token',
      token_type: 'bearer',
      expira_em: 7200,
    });

    render(<Entrar />);

    // Simula a digitação de 1, 2, 3, 4 no teclado físico
    fireEvent.keyDown(window, { key: '1' });
    fireEvent.keyDown(window, { key: '2' });
    fireEvent.keyDown(window, { key: '3' });
    fireEvent.keyDown(window, { key: '4' });

    // O PIN deve ter 4 dígitos
    const pinDisplay = screen.getByLabelText(/PIN: 4 de 4 dígitos/i);
    expect(pinDisplay).toBeInTheDocument();

    // Pressiona Enter no teclado físico para autenticar
    fireEvent.keyDown(window, { key: 'Enter' });

    await waitFor(() => {
      expect(servicos.entrarComPin).toHaveBeenCalledWith('(61) 99999-8888', '1234');
      expect(mockNavegar).toHaveBeenCalledWith('/inicio');
    });
  });

  it('permite apagar dígitos do PIN com a tecla Backspace', () => {
    render(<Entrar />);

    fireEvent.keyDown(window, { key: '1' });
    fireEvent.keyDown(window, { key: '2' });
    expect(screen.getByLabelText(/PIN: 2 de 4 dígitos/i)).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Backspace' });
    expect(screen.getByLabelText(/PIN: 1 de 4 dígitos/i)).toBeInTheDocument();
  });
});

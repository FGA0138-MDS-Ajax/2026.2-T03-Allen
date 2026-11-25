import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Cadastro } from './Cadastro';
import * as servicos from '../../servicos';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/cadastro',
  }),
}));

vi.mock('../../servicos', () => ({
  cadastrarUsuario: vi.fn(),
  ErroApi: class ErroApi extends Error {
    detalhe: string;
    constructor(detalhe: string) {
      super(detalhe);
      this.detalhe = detalhe;
    }
  },
}));

describe('Página Cadastro (RF04 - Direcionamento ao WhatsApp)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('exibe botão de falar com assistente no WhatsApp com link e mensagem pré-preenchida ao concluir cadastro', async () => {
    vi.mocked(servicos.cadastrarUsuario).mockResolvedValue({
      id: 'user-1',
      nome: 'Dona Maria',
      telefone: '61999998888',
      email: 'maria@email.com',
      tem_pin: true,
    });

    render(<Cadastro />);

    // Informações cadastrais
    fireEvent.change(screen.getByLabelText(/seu nome completo/i), {
      target: { value: 'Dona Maria' },
    });
    fireEvent.change(screen.getByLabelText(/número de celular/i), {
      target: { value: '(61) 99999-8888' },
    });
    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: { value: 'maria@email.com' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^continuar$/i }));

    // Digitar PIN
    expect(screen.getByText(/crie seu pin numérico/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '1' }));
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    fireEvent.click(screen.getByRole('button', { name: '3' }));
    fireEvent.click(screen.getByRole('button', { name: '4' }));

    fireEvent.click(screen.getByRole('button', { name: /^continuar$/i }));

    // Confirmar PIN
    expect(screen.getByText(/confirme seu pin/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '1' }));
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    fireEvent.click(screen.getByRole('button', { name: '3' }));
    fireEvent.click(screen.getByRole('button', { name: '4' }));

    fireEvent.click(
      screen.getByRole('button', { name: /confirmar e salvar/i })
    );

    // Tela de sucesso e direcionamento ao WhatsApp
    await waitFor(() => {
      expect(screen.getByText('Cadastro concluído!')).toBeInTheDocument();
    });

    const linkWhatsApp = screen.getByRole('link', {
      name: /falar com o assistente no whatsapp/i,
    });
    expect(linkWhatsApp).toBeInTheDocument();
    expect(linkWhatsApp).toHaveAttribute('target', '_blank');
    expect(linkWhatsApp).toHaveAttribute('rel', 'noopener noreferrer');
    expect(linkWhatsApp.getAttribute('href')).toContain('https://wa.me/');
    expect(linkWhatsApp.getAttribute('href')).toContain(
      encodeURIComponent('Olá! Acabei de criar minha conta no Vero.')
    );
  });
});

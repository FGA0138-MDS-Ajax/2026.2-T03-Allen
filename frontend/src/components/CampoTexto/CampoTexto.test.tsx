import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CampoTexto } from './CampoTexto';

describe('Componente CampoTexto', () => {
  it('deve associar o rótulo ao campo de entrada via htmlFor/id', () => {
    render(<CampoTexto rotulo="Nome completo" placeholder="Digite seu nome" />);
    const input = screen.getByLabelText(/nome completo/i);
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'Digite seu nome');
  });

  it('deve exibir mensagem de erro acessível com role alert', () => {
    render(<CampoTexto rotulo="Celular" erro="Número de celular inválido" />);
    const input = screen.getByLabelText(/celular/i);
    expect(input).toHaveAttribute('aria-invalid', 'true');
    const erro = screen.getByRole('alert');
    expect(erro).toHaveTextContent(/número de celular inválido/i);
  });

  it('deve exibir texto de ajuda descritivo', () => {
    render(
      <CampoTexto
        rotulo="Código de verificação"
        ajuda="Enviamos um SMS com 6 números"
      />
    );
    expect(
      screen.getByText(/enviamos um sms com 6 números/i)
    ).toBeInTheDocument();
  });
});

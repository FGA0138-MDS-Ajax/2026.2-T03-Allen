import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AlertaStatus } from './AlertaStatus';

describe('Componente AlertaStatus', () => {
  it('deve renderizar status de sucesso com ícone e texto acessível', () => {
    render(
      <AlertaStatus tipo="sucesso">Gasto salvo com sucesso!</AlertaStatus>
    );
    const status = screen.getByRole('status');
    expect(status).toHaveTextContent(/gasto salvo com sucesso!/i);
    expect(screen.getByLabelText('Sucesso')).toBeInTheDocument();
  });

  it('deve renderizar alerta de erro quando tipo for erro', () => {
    render(
      <AlertaStatus tipo="erro" role="alert">
        Senha incorreta
      </AlertaStatus>
    );
    const alerta = screen.getByRole('alert');
    expect(alerta).toHaveTextContent(/senha incorreta/i);
    expect(screen.getByLabelText('Erro')).toBeInTheDocument();
  });

  it('região viva continua a mesma quando o texto muda (#100)', () => {
    const { rerender } = render(
      <AlertaStatus tipo="sucesso">Primeira mensagem</AlertaStatus>
    );
    const regiao = screen.getByRole('status');
    expect(regiao).toHaveAttribute('aria-live', 'polite');

    rerender(<AlertaStatus tipo="sucesso">Segunda mensagem</AlertaStatus>);
    expect(screen.getByRole('status')).toBe(regiao);
    expect(regiao).toHaveTextContent('Segunda mensagem');
  });
});

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
});

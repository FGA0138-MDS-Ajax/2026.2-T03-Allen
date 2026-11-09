import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmacaoSucesso } from './ConfirmacaoSucesso';

describe('Componente ConfirmacaoSucesso', () => {
  it('não renderiza nada quando aberta for false', () => {
    const { container } = render(
      <ConfirmacaoSucesso
        aberta={false}
        mensagem="Sucesso"
        onIrParaInicio={() => {}}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renderiza título, mensagem e botões quando aberta for true', () => {
    const mockInicio = vi.fn();
    const mockDesfazer = vi.fn();

    render(
      <ConfirmacaoSucesso
        aberta={true}
        mensagem="Gasto de R$ 25,00 salvo com sucesso."
        onIrParaInicio={mockInicio}
        onDesfazer={mockDesfazer}
      />
    );

    expect(screen.getByText('Tudo certo!')).toBeInTheDocument();
    expect(screen.getByText('Gasto de R$ 25,00 salvo com sucesso.')).toBeInTheDocument();

    const btnInicio = screen.getByRole('button', { name: /ir para a tela inicial/i });
    fireEvent.click(btnInicio);
    expect(mockInicio).toHaveBeenCalledTimes(1);

    const btnDesfazer = screen.getByRole('button', { name: /desfazer/i });
    fireEvent.click(btnDesfazer);
    expect(mockDesfazer).toHaveBeenCalledTimes(1);
  });
});

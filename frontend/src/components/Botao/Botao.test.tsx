import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Botao } from './Botao';

describe('Componente Botao', () => {
  it('deve renderizar o texto do botão corretamente', () => {
    render(<Botao>Continuar</Botao>);
    expect(
      screen.getByRole('button', { name: /continuar/i })
    ).toBeInTheDocument();
  });

  it('deve chamar a função onClick quando clicado', () => {
    const handleClique = vi.fn();
    render(<Botao onClick={handleClique}>Confirmar</Botao>);

    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(handleClique).toHaveBeenCalledTimes(1);
  });

  it('deve exibir indicador de carregamento e desabilitar o botão', () => {
    render(
      <Botao carregando textoCarregando="Salvando...">
        Salvar
      </Botao>
    );
    const botao = screen.getByRole('button');
    expect(botao).toBeDisabled();
    expect(botao).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByText('Salvando...')).toBeInTheDocument();
  });

  it('não deve disparar onClick quando estiver desabilitado', () => {
    const handleClique = vi.fn();
    render(
      <Botao disabled onClick={handleClique}>
        Avançar
      </Botao>
    );

    fireEvent.click(screen.getByRole('button', { name: /avançar/i }));
    expect(handleClique).not.toHaveBeenCalled();
  });
});

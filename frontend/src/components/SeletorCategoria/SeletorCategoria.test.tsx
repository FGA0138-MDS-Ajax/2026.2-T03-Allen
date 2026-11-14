import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SeletorCategoria } from './SeletorCategoria';

describe('Componente SeletorCategoria', () => {
  it('deve listar as categorias com botões e ícones acessíveis', () => {
    const handleSelecionar = vi.fn();
    render(<SeletorCategoria onSelecionar={handleSelecionar} />);

    expect(screen.getByRole('radio', { name: /mercado/i })).toBeInTheDocument();
    expect(
      screen.getByRole('radio', { name: /farmácia/i })
    ).toBeInTheDocument();
  });

  it('deve disparar onSelecionar quando uma categoria é escolhida', () => {
    const handleSelecionar = vi.fn();
    render(<SeletorCategoria onSelecionar={handleSelecionar} />);

    fireEvent.click(screen.getByRole('radio', { name: /mercado/i }));
    expect(handleSelecionar).toHaveBeenCalledWith('mercado');
  });

  it('deve marcar aria-checked na categoria ativa', () => {
    const handleSelecionar = vi.fn();
    render(
      <SeletorCategoria
        categoriaSelecionada="farmacia"
        onSelecionar={handleSelecionar}
      />
    );

    const farmacia = screen.getByRole('radio', { name: /farmácia/i });
    expect(farmacia).toHaveAttribute('aria-checked', 'true');

    const mercado = screen.getByRole('radio', { name: /mercado/i });
    expect(mercado).toHaveAttribute('aria-checked', 'false');
  });
});

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TecladoNumerico } from './TecladoNumerico';

describe('Componente TecladoNumerico', () => {
  it('deve conter todos os dígitos de 0 a 9 com acessibilidade por papel e nome exato', () => {
    const handleDigito = vi.fn();
    const handleApagar = vi.fn();

    render(<TecladoNumerico onDigito={handleDigito} onApagar={handleApagar} />);

    for (let i = 0; i <= 9; i++) {
      const btn = screen.getByRole('button', { name: String(i) });
      expect(btn).toBeInTheDocument();
    }
  });

  it('deve disparar onDigito ao clicar nos números', () => {
    const handleDigito = vi.fn();
    const handleApagar = vi.fn();

    render(<TecladoNumerico onDigito={handleDigito} onApagar={handleApagar} />);

    fireEvent.click(screen.getByRole('button', { name: '1' }));
    expect(handleDigito).toHaveBeenCalledWith('1');

    fireEvent.click(screen.getByRole('button', { name: '5' }));
    expect(handleDigito).toHaveBeenCalledWith('5');
  });

  it('deve disparar onApagar ao clicar no botão de apagar', () => {
    const handleDigito = vi.fn();
    const handleApagar = vi.fn();

    render(<TecladoNumerico onDigito={handleDigito} onApagar={handleApagar} />);

    fireEvent.click(screen.getByRole('button', { name: /apagar/i }));
    expect(handleApagar).toHaveBeenCalledTimes(1);
  });
});

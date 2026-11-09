import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Inicio } from './Inicio';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/inicio',
  }),
}));

describe('Página Inicio (Dashboard do Vero)', () => {
  it('renderiza o saldo disponível, nível do saldo e atalhos principais', () => {
    render(<Inicio />);

    expect(screen.getByText('Você ainda tem disponível no mês:')).toBeInTheDocument();
    expect(screen.getByTestId('saldo-disponivel')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /registrar novo gasto/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ver minhas contas a pagar/i })).toBeInTheDocument();
  });

  it('navega para a tela de anotar gasto ao clicar no botão de registrar gasto', () => {
    render(<Inicio />);

    const btnRegistrar = screen.getByRole('button', { name: /registrar novo gasto/i });
    fireEvent.click(btnRegistrar);

    expect(mockNavegar).toHaveBeenCalledWith('/anotar-gasto');
  });

  it('exibe os últimos gastos anotados com suas respectivas descrições e ícones', () => {
    render(<Inicio />);

    expect(screen.getByText('Compras de Mercado')).toBeInTheDocument();
    expect(screen.getByText('Farmácia Popular')).toBeInTheDocument();
  });
});

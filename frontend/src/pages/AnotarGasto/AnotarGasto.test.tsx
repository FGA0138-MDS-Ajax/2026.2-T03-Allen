import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnotarGasto } from './AnotarGasto';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/anotar-gasto',
  }),
}));

describe('Página AnotarGasto', () => {
  it('renderiza o formulário com display monetário e seletor de categorias com ícones', () => {
    render(<AnotarGasto />);

    expect(screen.getByText('Anotar novo gasto')).toBeInTheDocument();
    expect(screen.getByText('Escolha a categoria:')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /mercado/i })).toBeInTheDocument();
    expect(
      screen.getByRole('radio', { name: /farmácia/i })
    ).toBeInTheDocument();
  });

  it('permite digitar valor e salvar novo gasto exibindo mensagem de sucesso', () => {
    render(<AnotarGasto />);

    // Digita 2, 5, 0, 0 -> R$ 25,00
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    fireEvent.click(screen.getByRole('button', { name: '5' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));

    // Seleciona Farmácia
    fireEvent.click(screen.getByRole('radio', { name: /farmácia/i }));

    // Clica em Salvar gasto
    const btnSalvar = screen.getByRole('button', { name: /salvar gasto/i });
    fireEvent.click(btnSalvar);

    expect(screen.getByText('Tudo certo!')).toBeInTheDocument();
    expect(
      screen.getByText(/gasto de r\$\s*25,00 registrado com sucesso no vero/i)
    ).toBeInTheDocument();
  });

  it('permite alternar para entrada e salvar uma nova entrada de dinheiro', () => {
    render(<AnotarGasto />);

    // Alterna para entrada
    fireEvent.click(
      screen.getByRole('button', { name: /\+ entrou dinheiro/i })
    );

    expect(screen.getByText('Anotar recebimento')).toBeInTheDocument();
    expect(screen.getByText('De onde veio esse dinheiro?')).toBeInTheDocument();

    // Digita 1, 0, 0, 0, 0 -> R$ 100,00
    fireEvent.click(screen.getByRole('button', { name: '1' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));

    // Clica em Salvar recebimento
    const btnSalvar = screen.getByRole('button', {
      name: /salvar recebimento/i,
    });
    fireEvent.click(btnSalvar);

    expect(screen.getByText('Tudo certo!')).toBeInTheDocument();
    expect(
      screen.getByText(
        /recebimento de r\$\s*100,00 registrado com sucesso no vero/i
      )
    ).toBeInTheDocument();
  });
});

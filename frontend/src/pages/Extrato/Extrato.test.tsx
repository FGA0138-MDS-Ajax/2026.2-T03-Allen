import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Extrato } from './Extrato';
import * as servicos from '../../servicos';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/extrato',
  }),
}));

vi.mock('../../servicos', () => ({
  listarContas: vi.fn(),
  estaAutenticado: vi.fn().mockReturnValue(true),
  limparSessao: vi.fn(),
}));

const mockContas: servicos.ContaSaida[] = [
  {
    id: '1',
    descricao: 'Conta de Luz',
    valor: 185.5,
    vencimento_em: '2026-11-20',
    categoria_id: null,
    status: 'a_vencer',
    pagamento_em: null,
    criado_em: '2026-11-01T10:00:00',
  },
];

describe('Página Extrato de Movimentações', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(servicos.listarContas).mockResolvedValue(mockContas);
    const data = new Date();
    const mes = `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, '0')}`;
    localStorage.setItem(
      'vero-dados-do-mes',
      JSON.stringify({
        mes,
        meta: 200000,
        entradasFixas: 330000,
        itens: [
          {
            id: 1,
            dia: 1,
            tipo: 'entrada',
            centavos: 330000,
            categoria: 'Salário / Renda',
          },
          {
            id: 2,
            dia: 2,
            tipo: 'gasto',
            centavos: 5000,
            categoria: 'Mercado',
          },
        ],
      })
    );
  });

  it('renderiza o cabeçalho, resumo consolidado e movimentações unificadas', async () => {
    render(<Extrato />);

    expect(
      screen.getByRole('heading', { name: /extrato de movimentações/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /entradas/i })).toBeInTheDocument();
    expect(screen.getByText('Saldo que Sobra')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });
  });

  it('filtra as movimentações ao alternar entre as abas', async () => {
    render(<Extrato />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    const abaGastos = screen.getByRole('tab', { name: /gastos/i });
    fireEvent.click(abaGastos);

    // Na aba de gastos não deve exibir Conta de Luz (que é conta)
    expect(screen.queryByText('Conta de Luz')).not.toBeInTheDocument();
  });

  it('permite apagar um gasto com o botão de excluir', async () => {
    render(<Extrato />);

    const botoesApagar = screen.getAllByTitle(/apagar este/i);
    expect(botoesApagar.length).toBeGreaterThan(0);

    fireEvent.click(botoesApagar[0]);

    const botaoConfirmar = screen.getByRole('button', {
      name: /sim, apagar lançamento/i,
    });
    fireEvent.click(botaoConfirmar);

    await waitFor(() => {
      expect(
        screen.getByText(/apagado com sucesso do vero/i)
      ).toBeInTheDocument();
    });
  });
});

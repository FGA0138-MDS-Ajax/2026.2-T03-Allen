import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Inicio } from './Inicio';
import * as servicos from '../../servicos';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/inicio',
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
  {
    id: '2',
    descricao: 'Aluguel Atrasado',
    valor: 1200.0,
    vencimento_em: '2026-10-15',
    categoria_id: null,
    status: 'em_atraso',
    pagamento_em: null,
    criado_em: '2026-10-01T10:00:00',
  },
];

describe('Página Inicio (Dashboard do Vero com Gráfico e Origem do Saldo)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(servicos.listarContas).mockResolvedValue(mockContas);
  });

  it('renderiza o saldo disponível, barra de nível e detalhamento de origem do saldo', async () => {
    render(<Inicio />);

    expect(screen.getByText('Você ainda tem disponível no mês:')).toBeInTheDocument();
    expect(screen.getByTestId('saldo-disponivel')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Detalhamento de onde sai o saldo
    expect(screen.getByText('De onde sai esse saldo:')).toBeInTheDocument();
    expect(screen.getByText('Salário e entradas do mês')).toBeInTheDocument();
    expect(screen.getByText('Contas a pagar cadastradas')).toBeInTheDocument();
    expect(screen.getByText('Gastos anotados no dia a dia')).toBeInTheDocument();
  });

  it('exibe as contas mais próximas de vencer com seus status e valores', async () => {
    render(<Inicio />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
      expect(screen.getByText('Aluguel Atrasado')).toBeInTheDocument();
    });

    expect(screen.getByText(/contas mais próximas de vencer/i)).toBeInTheDocument();
  });

  it('exibe o dashboard com meta de saldo e gráfico de evolução diária', () => {
    render(<Inicio />);

    expect(screen.getByText('Meta de saldo do mês')).toBeInTheDocument();
    expect(screen.getByText('Seu saldo no mês')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /gráfico de linha/i })).toBeInTheDocument();
  });

  it('navega para a tela de anotar gasto ao clicar no botão de registrar gasto', () => {
    render(<Inicio />);

    const btnRegistrar = screen.getByRole('button', { name: /anotar novo gasto ou entrada/i });
    fireEvent.click(btnRegistrar);

    expect(mockNavegar).toHaveBeenCalledWith('/anotar-gasto');
  });
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Extrato } from './Extrato';
import * as servicos from '../../servicos';
import * as transacoes from '../../servicos/transacoes';
import { mesAtual, prepararApiFalsa, transacao } from '../../test/apiFalsa';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/extrato',
  }),
}));

vi.mock('../../servicos', () => ({
  listarContas: vi.fn(),
  excluirConta: vi.fn(),
  estaAutenticado: vi.fn().mockReturnValue(true),
  limparSessao: vi.fn(),
  ErroApi: class ErroApi extends Error {
    status: number;
    detalhe: string;
    constructor(status: number, detalhe: string) {
      super(detalhe);
      this.status = status;
      this.detalhe = detalhe;
    }
  },
}));

vi.mock('../../servicos/transacoes', async (original) => ({
  ...(await original<typeof import('../../servicos/transacoes')>()),
  listarTransacoes: vi.fn(),
  anotarTransacao: vi.fn(),
  editarTransacao: vi.fn(),
  excluirTransacao: vi.fn(),
  obterSaldoMes: vi.fn(),
}));

vi.mock('../../servicos/categorias', () => ({
  listarCategorias: vi.fn(),
}));

const mockContas: servicos.ContaSaida[] = [
  {
    id: '1',
    descricao: 'Conta de Luz',
    valor: 185.5,
    vencimento_em: '2026-11-20',
    categoria_id: null,
    status: 'paga',
    pagamento_em: '2026-11-10T10:00:00',
    criado_em: '2026-11-01T10:00:00',
  },
];

const GASTO = transacao({
  id: 'gasto-1',
  tipo: 'saida',
  valor: '50.00',
  data: `${mesAtual()}-02`,
  categoria_id: 2,
});
const ENTRADA = transacao({
  id: 'entrada-1',
  tipo: 'entrada',
  valor: '3300.00',
  data: `${mesAtual()}-01`,
  descricao: 'Salário / Renda',
});

describe('Página Extrato de Movimentações', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(servicos.listarContas).mockResolvedValue(mockContas);
    prepararApiFalsa([GASTO, ENTRADA], {
      entradas: '3300.00',
      gastos: '50.00',
      contas: '185.50',
      saldo: '3064.50',
    });
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
      expect(screen.getByText('Mercado')).toBeInTheDocument();
      expect(screen.getByText('Salário / Renda')).toBeInTheDocument();
    });
  });

  it('usa o saldo da API: conta paga continua descontada (#77)', async () => {
    render(<Extrato />);

    expect(await screen.findByText(/=\s*R\$\s*3\.064,50/)).toBeInTheDocument();
    // No resumo "Contas a Pagar" e na linha da conta paga
    expect(screen.getAllByText(/−\s*R\$\s*185,50/)).toHaveLength(2);
  });

  it('mostra saldo negativo em vez de zero', async () => {
    prepararApiFalsa([], { saldo: '-30.50' });
    render(<Extrato />);

    expect(await screen.findByText(/=\s*−\s*R\$\s*30,50/)).toBeInTheDocument();
  });

  it('filtra as movimentações ao alternar entre as abas', async () => {
    render(<Extrato />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('tab', { name: /gastos/i }));

    expect(screen.queryByText('Conta de Luz')).not.toBeInTheDocument();
  });

  it('pede confirmação e apaga o gasto na API', async () => {
    render(<Extrato />);

    fireEvent.click(
      await screen.findByRole('button', { name: /apagar gasto de mercado/i })
    );
    fireEvent.click(
      screen.getByRole('button', { name: /sim, apagar lançamento/i })
    );

    expect(
      await screen.findByText(/apagado com sucesso do vero/i)
    ).toBeInTheDocument();
    expect(transacoes.excluirTransacao).toHaveBeenCalledWith('gasto-1');
  });

  it('altera valor, data e categoria do gasto (RF10)', async () => {
    render(<Extrato />);

    fireEvent.click(
      await screen.findByRole('button', { name: /alterar gasto de mercado/i })
    );
    expect(screen.getByLabelText(/valor/i)).toHaveValue('50,00');

    fireEvent.change(screen.getByLabelText(/valor/i), {
      target: { value: '45,90' },
    });
    fireEvent.change(screen.getByLabelText(/data/i), {
      target: { value: `${mesAtual()}-03` },
    });
    fireEvent.click(screen.getByRole('radio', { name: /farmácia/i }));
    fireEvent.click(screen.getByRole('button', { name: /salvar alteração/i }));

    expect(
      await screen.findByText(/gasto alterado com sucesso/i)
    ).toBeInTheDocument();
    expect(transacoes.editarTransacao).toHaveBeenCalledWith('gasto-1', {
      valor: '45.90',
      data: `${mesAtual()}-03`,
      categoria_id: 3,
    });
  });

  it('não salva a edição com valor inválido', async () => {
    render(<Extrato />);

    fireEvent.click(
      await screen.findByRole('button', { name: /alterar gasto de mercado/i })
    );
    fireEvent.change(screen.getByLabelText(/valor/i), {
      target: { value: '0' },
    });
    fireEvent.click(screen.getByRole('button', { name: /salvar alteração/i }));

    expect(
      screen.getByText(/digite um valor maior que zero/i)
    ).toBeInTheDocument();
    expect(transacoes.editarTransacao).not.toHaveBeenCalled();
  });
});

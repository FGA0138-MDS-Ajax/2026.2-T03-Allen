import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Inicio } from './Inicio';
import * as servicos from '../../servicos';
import * as transacoes from '../../servicos/transacoes';
import { mesAtual, prepararApiFalsa, transacao } from '../../test/apiFalsa';

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
    prepararApiFalsa(
      [
        transacao({
          id: 'g1',
          valor: '120.00',
          data: `${mesAtual()}-03`,
          categoria_id: 2,
        }),
      ],
      {
        entradas: '1000.00',
        gastos: '120.00',
        contas: '600.00',
        saldo: '280.00',
      }
    );
  });

  it('renderiza o saldo disponível, barra de nível e detalhamento de origem do saldo', async () => {
    render(<Inicio />);

    expect(
      screen.getByText('Você ainda tem disponível no mês:')
    ).toBeInTheDocument();
    expect(screen.getByTestId('saldo-disponivel')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Detalhamento de onde sai o saldo
    expect(screen.getByText('De onde sai esse saldo:')).toBeInTheDocument();
    expect(screen.getByText('Salário e entradas do mês')).toBeInTheDocument();
    expect(
      screen.getByText('Contas do mês (pagas ou não)')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Gastos anotados no dia a dia')
    ).toBeInTheDocument();
  });

  it('exibe as contas mais próximas de vencer com seus status e valores', async () => {
    render(<Inicio />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
      expect(screen.getByText('Aluguel Atrasado')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/contas mais próximas de vencer/i)
    ).toBeInTheDocument();
  });

  it('exibe o dashboard com meta de saldo e gráfico de evolução diária', () => {
    render(<Inicio />);

    expect(screen.getByText('Meta de saldo do mês')).toBeInTheDocument();
    expect(screen.getByText('Seu saldo no mês')).toBeInTheDocument();
    expect(
      screen.getByRole('img', { name: /gráfico de linha/i })
    ).toBeInTheDocument();
  });

  it('navega para a tela de anotar gasto ao clicar no botão de registrar gasto', () => {
    render(<Inicio />);

    const [btnRegistrar] = screen.getAllByRole('button', {
      name: /anotar gasto\/recebimento/i,
    });

    fireEvent.click(btnRegistrar);

    expect(mockNavegar).toHaveBeenCalledWith('/anotar-gasto');
  });

  it('exibe o link para o WhatsApp com número e mensagem pré-preenchida (RF04)', () => {
    render(<Inicio />);

    const linkWhatsApp = screen.getByRole('link', {
        name: /anotar gasto pelo whatsapp/i,
    });

    expect(linkWhatsApp).toBeInTheDocument();
    expect(linkWhatsApp).toHaveAttribute('target', '_blank');
    expect(linkWhatsApp).toHaveAttribute('rel', 'noopener noreferrer');
    expect(linkWhatsApp.getAttribute('href')).toContain('https://wa.me/');
    expect(linkWhatsApp.getAttribute('href')).toContain(
      encodeURIComponent('Olá! Gostaria de anotar um gasto no Vero.')
    );
  });
  
  it('mostra o saldo calculado pela API e o percentual já gasto', async () => {
    render(<Inicio />);

    await waitFor(() =>
      expect(screen.getByTestId('saldo-disponivel')).toHaveTextContent(
        /R\$\s*280,00/
      )
    );
    // 280 de 1000 ainda disponíveis: 72% já gasto
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuetext',
      'Você já gastou 72% do dinheiro do mês'
    );
    expect(screen.getByText('Mercado')).toBeInTheDocument();
  });

  it('mostra saldo negativo quando os gastos passam das entradas', async () => {
    prepararApiFalsa([], {
      entradas: '100.00',
      gastos: '130.50',
      saldo: '-30.50',
    });
    render(<Inicio />);

    await waitFor(() =>
      expect(screen.getByTestId('saldo-disponivel')).toHaveTextContent(
        /-\s*R\$\s*30,50/
      )
    );
  });

  it('apaga o gasto na API depois de confirmar', async () => {
    render(<Inicio />);

    fireEvent.click(
      await screen.findByRole('button', { name: /apagar gasto de mercado/i })
    );
    fireEvent.click(screen.getByRole('button', { name: /sim, apagar/i }));

    await waitFor(() =>
      expect(transacoes.excluirTransacao).toHaveBeenCalledWith('g1')
    );
    // RF20 / #100: apagar também mostra a confirmação padrão
    expect(
      await screen.findByText(/gasto de r\$\s*[\d.,]+ com mercado apagado/i)
    ).toBeVisible();
  });

  it('avisa quando não consegue carregar os dados', async () => {
    vi.mocked(transacoes.listarTransacoes).mockRejectedValueOnce(
      new Error('fora do ar')
    );
    render(<Inicio />);

    expect(
      await screen.findByText(/não foi possível carregar seus dados/i)
    ).toBeInTheDocument();
  });
});

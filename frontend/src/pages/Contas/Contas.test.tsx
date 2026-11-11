import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Contas } from './Contas';
import * as servicos from '../../servicos';

vi.mock('../../servicos', () => ({
  listarContas: vi.fn(),
  cadastrarConta: vi.fn(),
  definirPagamentoConta: vi.fn(),
  excluirConta: vi.fn(),
  limparSessao: vi.fn(),
  estaAutenticado: vi.fn(),
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

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: vi.fn(),
    rota: '/contas',
  }),
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
  {
    id: '3',
    descricao: 'Internet Fibra',
    valor: 99.9,
    vencimento_em: '2026-11-05',
    categoria_id: null,
    status: 'paga',
    pagamento_em: '2026-11-05T14:30:00',
    criado_em: '2026-11-01T10:00:00',
  },
];

describe('Página de Contas a Pagar (RF25, RF30, RF32)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(servicos.estaAutenticado).mockReturnValue(true);
    vi.mocked(servicos.listarContas).mockResolvedValue(mockContas);
  });

  it('renderiza o cabeçalho e os resumos de contas', async () => {
    render(<Contas />);

    expect(screen.getByText('Minhas Contas a Pagar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
      expect(screen.getByText('Aluguel Atrasado')).toBeInTheDocument();
      expect(screen.getByText('Internet Fibra')).toBeInTheDocument();
    });

    // Badges acessíveis (RF32: cor + ícone + texto)
    expect(screen.getByText('A vencer')).toBeInTheDocument();
    expect(screen.getByText('Em atraso')).toBeInTheDocument();
    expect(screen.getByText('Paga')).toBeInTheDocument();
  });

  it('filtra as contas por situação ao clicar nos botões de filtro', async () => {
    render(<Contas />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    // Clica no filtro "Em atraso"
    const filtroAtraso = screen.getByRole('tab', { name: /Em atraso/i });
    fireEvent.click(filtroAtraso);

    expect(screen.getByText('Aluguel Atrasado')).toBeInTheDocument();
    expect(screen.queryByText('Conta de Luz')).not.toBeInTheDocument();
    expect(screen.queryByText('Internet Fibra')).not.toBeInTheDocument();

    // Clica no filtro "Pagas"
    const filtroPagas = screen.getByRole('tab', { name: /Pagas/i });
    fireEvent.click(filtroPagas);

    expect(screen.getByText('Internet Fibra')).toBeInTheDocument();
    expect(screen.queryByText('Aluguel Atrasado')).not.toBeInTheDocument();
  });

  it('abre o formulário e permite cadastrar nova conta (RF25)', async () => {
    vi.mocked(servicos.cadastrarConta).mockResolvedValue({
      id: '4',
      descricao: 'Conta de Água',
      valor: 75.0,
      vencimento_em: '2026-11-25',
      categoria_id: null,
      status: 'a_vencer',
      pagamento_em: null,
      criado_em: '2026-11-02T10:00:00',
    });

    render(<Contas />);

    const btnNovo = screen.getByRole('button', { name: /Cadastrar Nova Conta/i });
    fireEvent.click(btnNovo);

    expect(screen.getByText('Cadastrar Nova Conta a Pagar')).toBeInTheDocument();

    // Digita 7500 centavos = R$ 75,00 no teclado numérico
    fireEvent.click(screen.getByRole('button', { name: '7' }));
    fireEvent.click(screen.getByRole('button', { name: '5' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));

    // Clica na sugestão rápida "Água"
    const chipAgua = screen.getByRole('button', { name: '+ Água' });
    fireEvent.click(chipAgua);

    // Salva a conta
    const btnSalvar = screen.getByRole('button', { name: /Salvar Conta/i });
    fireEvent.click(btnSalvar);

    await waitFor(() => {
      expect(servicos.cadastrarConta).toHaveBeenCalledWith({
        valor: 75.0,
        vencimento_em: expect.any(String),
        descricao: 'Água',
        recorrente: false,
      });
    });
  });

  it('permite cadastrar conta com recorrência ativada (RF26)', async () => {
    vi.mocked(servicos.cadastrarConta).mockResolvedValueOnce({
      id: '99',
      descricao: 'Aluguel',
      valor: 1200.0,
      vencimento_em: '2026-11-15',
      categoria_id: null,
      status: 'a_vencer',
      pagamento_em: null,
      recorrente: true,
      criado_em: '2026-11-01T10:00:00',
    });

    render(<Contas />);

    fireEvent.click(screen.getByRole('button', { name: /Cadastrar Nova Conta/i }));

    // Digita 120000 = R$ 1.200,00
    fireEvent.click(screen.getByRole('button', { name: '1' }));
    fireEvent.click(screen.getByRole('button', { name: '2' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));

    // Sugestão Aluguel
    fireEvent.click(screen.getByRole('button', { name: '+ Aluguel' }));

    // Marca o checkbox de recorrência
    const checkboxRecorrente = screen.getByLabelText(/Repetir todo mês/i);
    fireEvent.click(checkboxRecorrente);

    fireEvent.click(screen.getByRole('button', { name: /Salvar Conta/i }));

    await waitFor(() => {
      expect(servicos.cadastrarConta).toHaveBeenCalledWith({
        valor: 1200.0,
        vencimento_em: expect.any(String),
        descricao: 'Aluguel',
        recorrente: true,
      });
    });
  });

  it('permite apagar uma conta com modal de confirmação', async () => {
    vi.mocked(servicos.excluirConta).mockResolvedValueOnce();

    render(<Contas />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    // Clica no botão de lixeira da Conta de Luz
    const btnExcluir = screen.getByRole('button', {
      name: /Apagar conta Conta de Luz/i,
    });
    fireEvent.click(btnExcluir);

    // Modal de confirmação deve aparecer
    expect(screen.getByText('Tem certeza que deseja apagar?')).toBeInTheDocument();

    // Clica em confirmar
    const btnConfirmar = screen.getByRole('button', { name: /Sim, apagar conta/i });
    fireEvent.click(btnConfirmar);

    await waitFor(() => {
      expect(servicos.excluirConta).toHaveBeenCalledWith('1');
      expect(screen.getByText(/Conta "Conta de Luz" apagada com sucesso do Vero/i)).toBeInTheDocument();
    });
  });

  it('permite marcar uma conta como paga e desfazer o pagamento (RF30)', async () => {
    vi.mocked(servicos.definirPagamentoConta).mockResolvedValueOnce({
      id: '1',
      descricao: 'Conta de Luz',
      valor: 185.5,
      vencimento_em: '2026-11-20',
      categoria_id: null,
      status: 'paga',
      pagamento_em: '2026-11-09T10:00:00',
      criado_em: '2026-11-01T10:00:00',
    });

    render(<Contas />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    // Clica no botão "Marcar como paga" da Conta de Luz
    const btnPagar = screen.getByRole('button', {
      name: /Marcar a conta Conta de Luz como paga/i,
    });
    fireEvent.click(btnPagar);

    await waitFor(() => {
      expect(servicos.definirPagamentoConta).toHaveBeenCalledWith('1', true);
      expect(
        screen.getByText(/Conta "Conta de Luz" marcada como paga!/i)
      ).toBeInTheDocument();
    });

    // Agora desfaz o pagamento da conta Internet Fibra (que já estava paga)
    vi.mocked(servicos.definirPagamentoConta).mockResolvedValueOnce({
      id: '3',
      descricao: 'Internet Fibra',
      valor: 99.9,
      vencimento_em: '2026-11-05',
      categoria_id: null,
      status: 'a_vencer',
      pagamento_em: null,
      criado_em: '2026-11-01T10:00:00',
    });

    const btnDesfazer = screen.getByRole('button', {
      name: /Desfazer pagamento da conta Internet Fibra/i,
    });
    fireEvent.click(btnDesfazer);

    await waitFor(() => {
      expect(servicos.definirPagamentoConta).toHaveBeenCalledWith('3', false);
      expect(
        screen.getByText(/Pagamento da conta "Internet Fibra" desfeito./i)
      ).toBeInTheDocument();
    });
  });
});

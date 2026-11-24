import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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
  afterEach(() => {
    vi.useRealTimers();
  });

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

    const btnNovo = screen.getByRole('button', {
      name: /Cadastrar Nova Conta/i,
    });
    fireEvent.click(btnNovo);

    expect(
      screen.getByText('Cadastrar Nova Conta a Pagar')
    ).toBeInTheDocument();

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
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 10, 23, 10, 0));
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

    fireEvent.click(
      screen.getByRole('button', { name: /Cadastrar Nova Conta/i })
    );

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

    // Conta fixa pede só dia e mês, sem ano (#120)
    expect(
      screen.queryByLabelText('Data de Vencimento')
    ).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Dia'), { target: { value: '15' } });
    fireEvent.change(screen.getByLabelText('Mês'), { target: { value: '12' } });
    expect(
      screen.getByText('Vence todo dia 15, a partir de 15 de dezembro.')
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Salvar Conta/i }));

    await waitFor(() => {
      expect(servicos.cadastrarConta).toHaveBeenCalledWith({
        valor: 1200.0,
        vencimento_em: '2026-12-15',
        descricao: 'Aluguel',
        recorrente: true,
      });
    });
  });

  it('cadastra compra parcelada com o número de vezes (RF37, #134)', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 10, 23, 10, 0));
    vi.mocked(servicos.cadastrarConta).mockResolvedValueOnce({
      ...mockContas[0],
      id: '50',
      descricao: 'Geladeira',
    });

    render(<Contas />);
    fireEvent.click(
      screen.getByRole('button', { name: /Cadastrar Nova Conta/i })
    );
    // R$ 2.500,01 = 250001 centavos
    for (const d of '250001') {
      fireEvent.click(screen.getByRole('button', { name: d }));
    }
    fireEvent.change(screen.getByLabelText(/Nome da conta/i), {
      target: { value: 'Geladeira' },
    });

    // Marcar "parcelada" desmarca "todo mês": não podem ir juntas
    fireEvent.click(screen.getByLabelText(/Repetir todo mês/i));
    fireEvent.click(screen.getByLabelText(/Compra parcelada/i));
    expect(screen.getByLabelText(/Repetir todo mês/i)).not.toBeChecked();

    fireEvent.change(screen.getByLabelText('Em quantas vezes?'), {
      target: { value: '10' },
    });
    // Mesma regra da API: o centavo que sobra vai na 1ª parcela
    expect(
      screen.getByText(
        /1 parcela de R\$\s?250,01 e 9 de R\$\s?250,00\. A primeira vence no mês seguinte/
      )
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Data da compra')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Data da compra'), {
      target: { value: '2026-11-23' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Salvar Conta/i }));

    await waitFor(() => {
      expect(servicos.cadastrarConta).toHaveBeenCalledWith({
        valor: 2500.01,
        vencimento_em: '2026-11-23',
        descricao: 'Geladeira',
        recorrente: false,
        parcelas: 10,
      });
    });
  });

  it('mostra o número da parcela e não soma parcelas futuras em "a vencer este mês" (#134)', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 10, 23, 10, 0));
    const parcela = (n: number, venc: string): servicos.ContaSaida => ({
      ...mockContas[0],
      id: `p${n}`,
      descricao: 'Geladeira',
      valor: 250,
      vencimento_em: venc,
      parcela: n,
      total_parcelas: 10,
    });
    vi.mocked(servicos.listarContas).mockResolvedValue([
      { ...mockContas[0], valor: 120, vencimento_em: '2026-11-30' },
      parcela(1, '2026-12-23'),
      parcela(2, '2027-01-23'),
    ]);

    render(<Contas />);

    expect(await screen.findByText(/Parcela 1 de 10/)).toBeInTheDocument();
    expect(screen.getByText(/Parcela 2 de 10/)).toBeInTheDocument();
    expect(
      screen.getByRole('button', {
        name: 'Marcar a conta Geladeira, parcela 2 de 10 como paga',
      })
    ).toBeInTheDocument();
    const resumo = screen.getByRole('region', {
      name: /Resumo geral das contas/i,
    });
    expect(resumo).toHaveTextContent(/A vencer este mês\s*R\$\s?120,00/);
  });

  it('recusa vencimento de anos atrás sem chamar a API (#121)', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 10, 23, 10, 0));

    render(<Contas />);

    fireEvent.click(
      screen.getByRole('button', { name: /Cadastrar Nova Conta/i })
    );
    fireEvent.click(screen.getByRole('button', { name: '5' }));
    fireEvent.click(screen.getByRole('button', { name: '0' }));

    const campoData = screen.getByLabelText('Data de Vencimento');
    expect(campoData).toHaveAttribute('min', '2026-10-01');
    fireEvent.change(campoData, { target: { value: '2021-03-10' } });
    fireEvent.click(screen.getByRole('button', { name: /Salvar Conta/i }));

    await waitFor(() => {
      expect(
        screen.getByText(
          'Essa data de vencimento já passou faz tempo. Use uma data a partir de 01/10/2026.'
        )
      ).toBeInTheDocument();
    });
    expect(servicos.cadastrarConta).not.toHaveBeenCalled();
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
    expect(
      screen.getByText('Tem certeza que deseja apagar?')
    ).toBeInTheDocument();

    // Clica em confirmar
    const btnConfirmar = screen.getByRole('button', {
      name: /Sim, apagar conta/i,
    });
    fireEvent.click(btnConfirmar);

    await waitFor(() => {
      expect(servicos.excluirConta).toHaveBeenCalledWith('1');
      expect(
        screen.getByText(/Conta "Conta de Luz" apagada com sucesso do Vero/i)
      ).toBeInTheDocument();
    });
  });

  it('não diz "apagada" quando a API não apaga a conta (#133)', async () => {
    vi.mocked(servicos.excluirConta).mockRejectedValueOnce(
      new servicos.ErroApi(
        409,
        'Essa conta já virou um gasto no seu extrato. Para apagar, apague o gasto no Extrato primeiro.'
      )
    );

    render(<Contas />);
    fireEvent.click(
      await screen.findByRole('button', { name: /Apagar conta Conta de Luz/i })
    );
    fireEvent.click(screen.getByRole('button', { name: /Sim, apagar conta/i }));

    expect(
      await screen.findByText(/apague o gasto no Extrato primeiro/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/apagada com sucesso/i)).not.toBeInTheDocument();
    expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
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

  it('alterna para o calendário mensal e filtra as contas ao tocar em um dia (RF34)', async () => {
    render(<Contas />);

    await waitFor(() => {
      expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Calendário' }));

    const dia20 = screen.getByRole('button', {
      name: /20 de novembro de 2026: 1 a vencer/i,
    });
    fireEvent.click(dia20);

    expect(screen.getByText('Conta de Luz')).toBeInTheDocument();
    expect(screen.queryByText('Internet Fibra')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Ver todas as datas' }));
    expect(screen.getByText('Internet Fibra')).toBeInTheDocument();
  });
});

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Contas } from './Contas';
import * as servicos from '../../servicos';

vi.mock('../../servicos', () => ({
  listarContas: vi.fn(),
  cadastrarConta: vi.fn(),
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
    criado_em: '2026-11-01T10:00:00',
  },
  {
    id: '2',
    descricao: 'Aluguel Atrasado',
    valor: 1200.0,
    vencimento_em: '2026-10-15',
    categoria_id: null,
    status: 'em_atraso',
    criado_em: '2026-10-01T10:00:00',
  },
  {
    id: '3',
    descricao: 'Internet Fibra',
    valor: 99.9,
    vencimento_em: '2026-11-05',
    categoria_id: null,
    status: 'paga',
    criado_em: '2026-11-01T10:00:00',
  },
];

describe('Página de Contas a Pagar (RF25, RF32)', () => {
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
      });
    });
  });
});

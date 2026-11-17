import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnotarGasto } from './AnotarGasto';
import * as transacoes from '../../servicos/transacoes';
import { ErroApi } from '../../servicos/api';
import { mesAtual, prepararApiFalsa } from '../../test/apiFalsa';

const mockNavegar = vi.fn();

vi.mock('../../router', () => ({
  useNavegacao: () => ({
    navegar: mockNavegar,
    rota: '/anotar-gasto',
  }),
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

vi.mock('../../components/LeitorQrCode/LeitorQrCode', () => ({
  LeitorQrCode: ({
    aoLerCodigo,
    aoFechar,
  }: {
    aoLerCodigo: (texto: string) => void;
    aoFechar: () => void;
  }) => (
    <div data-testid="mock-leitor-qr">
      <button
        type="button"
        onClick={() =>
          aoLerCodigo(
            'https://www.fazenda.df.gov.br/nfce/qrcode?p=53261112345678000199650010000123451123456789|2|1|1|HASH'
          )
        }
      >
        Simular QR v2
      </button>
      <button
        type="button"
        onClick={() =>
          aoLerCodigo(
            'https://nfce.fazenda.sp.gov.br/consulta?chNFe=35261098765432000111650010000123451123456789&nVersao=100&tpAmb=1&dhEmi=323032362d31302d3238&vNF=89.90'
          )
        }
      >
        Simular QR mes passado
      </button>
      <button type="button" onClick={aoFechar}>
        Fechar leitor
      </button>
    </div>
  ),
}));

const digitar = (...digitos: string[]) => {
  for (const d of digitos) {
    fireEvent.click(screen.getByRole('button', { name: d }));
  }
};

describe('Página AnotarGasto', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prepararApiFalsa();
  });

  it('renderiza o formulário com display monetário e seletor de categorias com ícones', () => {
    render(<AnotarGasto />);

    expect(screen.getByText('Anotar novo gasto')).toBeInTheDocument();
    expect(screen.getByText('Escolha a categoria:')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /mercado/i })).toBeInTheDocument();
    expect(
      screen.getByRole('radio', { name: /farmácia/i })
    ).toBeInTheDocument();
  });

  it('grava o gasto na API com a categoria escolhida e só então confirma', async () => {
    render(<AnotarGasto />);

    digitar('2', '5', '0', '0');
    fireEvent.click(screen.getByRole('radio', { name: /farmácia/i }));
    fireEvent.click(screen.getByRole('button', { name: /salvar gasto/i }));

    expect(await screen.findByText('Tudo certo!')).toBeInTheDocument();
    expect(
      screen.getByText(/gasto de r\$\s*25,00 registrado com sucesso no vero/i)
    ).toBeInTheDocument();
    expect(transacoes.anotarTransacao).toHaveBeenCalledWith({
      tipo: 'saida',
      valor: '25.00',
      origem: 'manual',
      data: undefined,
      descricao: null,
      categoria_id: 3,
    });
  });

  it('grava o recebimento com o motivo na descrição e sem categoria de gasto', async () => {
    render(<AnotarGasto />);

    fireEvent.click(
      screen.getByRole('button', { name: /\+ entrou dinheiro/i })
    );
    expect(screen.getByText('Anotar recebimento')).toBeInTheDocument();
    expect(screen.getByText('De onde veio esse dinheiro?')).toBeInTheDocument();

    digitar('1', '0', '0', '0', '0');
    fireEvent.click(screen.getByRole('button', { name: /aposentadoria/i }));
    fireEvent.click(
      screen.getByRole('button', { name: /salvar recebimento/i })
    );

    expect(
      await screen.findByText(
        /recebimento de r\$\s*100,00 registrado com sucesso no vero/i
      )
    ).toBeInTheDocument();
    expect(transacoes.anotarTransacao).toHaveBeenCalledWith(
      expect.objectContaining({
        tipo: 'entrada',
        valor: '100.00',
        descricao: 'Aposentadoria',
        categoria_id: null,
      })
    );
  });

  it('mostra o erro e não diz "Tudo certo!" quando a API não grava', async () => {
    vi.mocked(transacoes.anotarTransacao).mockRejectedValueOnce(
      new ErroApi(0, 'sem conexão')
    );
    render(<AnotarGasto />);

    digitar('5', '0', '0');
    fireEvent.click(screen.getByRole('button', { name: /salvar gasto/i }));

    expect(
      await screen.findByText(/não foi possível salvar agora/i)
    ).toBeInTheDocument();
    expect(screen.queryByText('Tudo certo!')).not.toBeInTheDocument();
  });

  it('mostra a mensagem do servidor quando ele recusa o valor', async () => {
    vi.mocked(transacoes.anotarTransacao).mockRejectedValueOnce(
      new ErroApi(422, 'O valor é muito alto. Confira e tente novamente.')
    );
    render(<AnotarGasto />);

    digitar('9', '9');
    fireEvent.click(screen.getByRole('button', { name: /salvar gasto/i }));

    expect(
      await screen.findByText(/o valor é muito alto/i)
    ).toBeInTheDocument();
  });

  it('desfazer apaga o lançamento na API', async () => {
    render(<AnotarGasto />);

    digitar('1', '0', '0');
    fireEvent.click(screen.getByRole('button', { name: /salvar gasto/i }));
    fireEvent.click(await screen.findByRole('button', { name: /desfazer/i }));

    await vi.waitFor(() =>
      expect(transacoes.excluirTransacao).toHaveBeenCalledTimes(1)
    );
  });

  it('abre o leitor de QR Code, exibe confirmação e salva valor com separador de milhar', async () => {
    render(<AnotarGasto />);

    fireEvent.click(
      screen.getByRole('button', { name: /ler qr code da nota fiscal/i })
    );
    expect(screen.getByTestId('mock-leitor-qr')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /simular qr v2/i }));

    expect(
      screen.getByText('Confira os dados da nota fiscal')
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/nome do estabelecimento/i)).toHaveValue('');
    expect(
      screen.getByText(/nota identificada \(df · cnpj 12\.345\.678\/0001-99\)/i)
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/valor total da nota/i), {
      target: { value: '1.234,56' },
    });
    fireEvent.change(screen.getByLabelText(/nome do estabelecimento/i), {
      target: { value: 'Mercado do Zé' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: /confirmar e salvar gasto/i })
    );

    expect(
      await screen.findByText(
        /gasto de r\$\s*1\.234,56 registrado com sucesso no vero/i
      )
    ).toBeInTheDocument();
    expect(transacoes.anotarTransacao).toHaveBeenCalledWith(
      expect.objectContaining({
        tipo: 'saida',
        valor: '1234.56',
        origem: 'qrcode_nf',
        descricao: 'Mercado do Zé',
      })
    );
    const enviado = vi.mocked(transacoes.anotarTransacao).mock.calls[0][0];
    expect(enviado.data?.startsWith(mesAtual())).toBe(true);
  });

  it('avisa e bloqueia salvamento se a data da nota estiver fora do mês atual', () => {
    render(<AnotarGasto />);

    fireEvent.click(
      screen.getByRole('button', { name: /ler qr code da nota fiscal/i })
    );
    fireEvent.click(
      screen.getByRole('button', { name: /simular qr mes passado/i })
    );

    expect(
      screen.getByText(/a data desta nota não pertence ao mês atual/i)
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole('button', { name: /confirmar e salvar gasto/i })
    );

    expect(
      screen.getByText(
        /a data da nota precisa estar dentro do mês atual até hoje/i
      )
    ).toBeInTheDocument();
    expect(screen.queryByText('Tudo certo!')).not.toBeInTheDocument();
    expect(transacoes.anotarTransacao).not.toHaveBeenCalled();
  });
});

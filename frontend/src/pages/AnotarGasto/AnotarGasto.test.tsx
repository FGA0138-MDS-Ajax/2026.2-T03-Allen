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

  it('abre o leitor de QR Code, exibe confirmação e salva valor com separador de milhar', () => {
    render(<AnotarGasto />);

    const btnQr = screen.getByRole('button', {
      name: /ler qr code da nota fiscal/i,
    });
    fireEvent.click(btnQr);

    expect(screen.getByTestId('mock-leitor-qr')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /simular qr v2/i }));

    expect(
      screen.getByText('Confira os dados da nota fiscal')
    ).toBeInTheDocument();

    const inputLoja = screen.getByLabelText(/nome do estabelecimento/i);
    expect(inputLoja).toHaveValue('');
    expect(
      screen.getByText(/nota identificada \(df · cnpj 12\.345\.678\/0001-99\)/i)
    ).toBeInTheDocument();

    const inputValor = screen.getByLabelText(/valor total da nota/i);
    fireEvent.change(inputValor, { target: { value: '1.234,56' } });

    fireEvent.click(
      screen.getByRole('button', { name: /confirmar e salvar gasto/i })
    );

    expect(screen.getByText('Tudo certo!')).toBeInTheDocument();
    expect(
      screen.getByText(
        /gasto de r\$\s*1\.234,56 registrado com sucesso no vero/i
      )
    ).toBeInTheDocument();
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
  });
});

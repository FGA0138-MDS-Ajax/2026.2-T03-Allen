import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CalendarioVencimentos } from './CalendarioVencimentos';
import { ContaSaida } from '../../servicos';

const contasExemplo: ContaSaida[] = [
  {
    id: '1',
    descricao: 'Luz',
    valor: 150,
    vencimento_em: '2026-11-20',
    categoria_id: null,
    status: 'a_vencer',
    pagamento_em: null,
    criado_em: '2026-11-01T10:00:00',
  },
  {
    id: '2',
    descricao: 'Água',
    valor: 80,
    vencimento_em: '2026-11-05',
    categoria_id: null,
    status: 'paga',
    pagamento_em: '2026-11-05T12:00:00',
    criado_em: '2026-11-01T10:00:00',
  },
];

describe('CalendarioVencimentos (RF34)', () => {
  it('marca os dias com vencimento e permite tocar para selecionar um dia', () => {
    const aoSelecionar = vi.fn();

    render(
      <CalendarioVencimentos
        contas={contasExemplo}
        mesInicial="2026-11"
        diaSelecionado={null}
        aoSelecionarDia={aoSelecionar}
      />
    );

    expect(screen.getByText('Novembro de 2026')).toBeInTheDocument();

    const dia20 = screen.getByRole('button', {
      name: /20 de novembro de 2026: 1 a vencer/i,
    });
    expect(dia20).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(dia20);
    expect(aoSelecionar).toHaveBeenCalledWith('2026-11-20');
  });

  it('permite navegar para o próximo mês e mês anterior', () => {
    render(
      <CalendarioVencimentos
        contas={contasExemplo}
        mesInicial="2026-11"
        diaSelecionado={null}
        aoSelecionarDia={() => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /próximo mês/i }));
    expect(screen.getByText('Dezembro de 2026')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /mês anterior/i }));
    expect(screen.getByText('Novembro de 2026')).toBeInTheDocument();
  });
});

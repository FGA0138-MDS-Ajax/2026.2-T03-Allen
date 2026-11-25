/**
 * Dados falsos da API de transações e categorias para os testes das telas.
 * Cada teste chama `vi.mock` dos módulos e depois `prepararApiFalsa`.
 */
import { vi } from 'vitest';
import * as transacoes from '../servicos/transacoes';
import * as categorias from '../servicos/categorias';

export const CATEGORIAS_TESTE: categorias.CategoriaApi[] = [
  { id: 1, codigo: 'casa', nome: 'Casa' },
  { id: 2, codigo: 'mercado', nome: 'Mercado' },
  { id: 3, codigo: 'farmacia', nome: 'Farmácia' },
  { id: 7, codigo: 'contas', nome: 'Contas' },
];

export const mesAtual = (): string => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

export const transacao = (
  dados: Partial<transacoes.TransacaoSaida>
): transacoes.TransacaoSaida => ({
  id: 'id-' + Math.random().toString(36).slice(2),
  tipo: 'saida',
  valor: '10.00',
  data: `${mesAtual()}-01`,
  descricao: null,
  categoria_id: null,
  origem: 'manual',
  criado_em: new Date().toISOString(),
  ...dados,
});

export function prepararApiFalsa(
  lista: transacoes.TransacaoSaida[] = [],
  saldo: Partial<transacoes.SaldoMes> = {}
) {
  vi.mocked(categorias.listarCategorias).mockResolvedValue(CATEGORIAS_TESTE);
  vi.mocked(transacoes.listarTransacoes).mockResolvedValue(lista);
  vi.mocked(transacoes.obterSaldoMes).mockResolvedValue({
    mes: mesAtual(),
    entradas: '0.00',
    gastos: '0.00',
    contas: '0.00',
    saldo: '0.00',
    ...saldo,
  });
  vi.mocked(transacoes.anotarTransacao).mockImplementation(async (dados) =>
    transacao({
      ...dados,
      data: dados.data ?? `${mesAtual()}-01`,
      descricao: dados.descricao ?? null,
      categoria_id: dados.categoria_id ?? null,
      origem: dados.origem ?? 'manual',
    })
  );
  vi.mocked(transacoes.excluirTransacao).mockResolvedValue();
  vi.mocked(transacoes.editarTransacao).mockImplementation(async (id, dados) =>
    transacao({ id, ...dados })
  );
}

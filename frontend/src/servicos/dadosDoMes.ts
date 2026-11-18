/**
 * Dados do mês do usuário: lançamentos, saldo e meta (RF08, RF10, RF19, RF22).
 *
 * Lançamentos e saldo vêm da API. O aparelho guarda só a meta de saldo, que é uma
 * preferência, e não um dado financeiro (Documento de Arquitetura).
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  anotarTransacao,
  centavosParaValor,
  editarTransacao,
  excluirTransacao,
  listarTransacoes,
  obterSaldoMes,
  OrigemApp,
  SaldoMes,
  TransacaoSaida,
  valorParaCentavos,
} from './transacoes';
import { CategoriaApi, listarCategorias } from './categorias';

export type TipoLancamento = 'gasto' | 'entrada';

export interface Lancamento {
  id: string;
  data: string; // AAAA-MM-DD
  dia: number;
  tipo: TipoLancamento;
  centavos: number;
  /** Nome para mostrar: a categoria, ou o motivo do recebimento. */
  categoria: string;
  categoriaId: number | null;
  /** Código da categoria (escolhe o ícone), se houver. */
  categoriaCodigo?: string;
  descricao?: string;
  origem: string;
}

export interface PontoSaldo {
  dia: number;
  saldo: number;
}

export interface Hoje {
  mes: string;
  dia: number;
  diasNoMes: number;
}

/** Totais do mês em centavos. */
export interface ResumoMes {
  entradas: number;
  gastos: number;
  contas: number;
  saldo: number;
}

export interface EstadoMes {
  mes: string;
  meta: number; // centavos
  itens: Lancamento[];
}

export interface NovoLancamento {
  tipo: TipoLancamento;
  centavos: number;
  /** Código da categoria de gasto (ex.: "mercado"). */
  categoriaCodigo?: string;
  /** Texto livre: motivo do recebimento ou nome do estabelecimento. */
  descricao?: string;
  data?: string;
  origem?: OrigemApp;
}

export interface MudancaLancamento {
  centavos?: number;
  data?: string;
  categoriaCodigo?: string;
}

const CHAVE_META = 'vero-meta-do-mes';
// Versões antigas guardavam os lançamentos no aparelho; não guardamos mais
const CHAVE_ANTIGA = 'vero-dados-do-mes';
export const PASSO_ESCALA = 10000; // R$ 100,00 entre marcas

export function calcularHoje(): Hoje {
  const data = new Date();
  return {
    mes: `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, '0')}`,
    dia: data.getDate(),
    diasNoMes: new Date(data.getFullYear(), data.getMonth() + 1, 0).getDate(),
  };
}

function lerMeta(mes: string): number {
  try {
    localStorage.removeItem(CHAVE_ANTIGA);
    const salvo = JSON.parse(localStorage.getItem(CHAVE_META) || 'null');
    if (salvo && salvo.mes === mes && Number.isFinite(salvo.centavos)) {
      return salvo.centavos;
    }
  } catch {
    // Armazenamento indisponível: segue sem meta
  }
  return 0;
}

function gravarMeta(mes: string, centavos: number): void {
  try {
    localStorage.setItem(CHAVE_META, JSON.stringify({ mes, centavos }));
  } catch {
    // Armazenamento indisponível: a meta vale só nesta visita
  }
}

/** Converte a transação da API para o formato das telas. */
export function paraLancamento(
  t: TransacaoSaida,
  categorias: CategoriaApi[]
): Lancamento {
  const categoria = categorias.find((c) => c.id === t.categoria_id);
  const tipo: TipoLancamento = t.tipo === 'entrada' ? 'entrada' : 'gasto';
  return {
    id: t.id,
    data: t.data,
    dia: Number(t.data.slice(8, 10)),
    tipo,
    centavos: valorParaCentavos(t.valor),
    categoria:
      categoria?.nome ||
      t.descricao ||
      (tipo === 'entrada' ? 'Recebimento' : 'Gasto'),
    categoriaId: t.categoria_id,
    categoriaCodigo: categoria?.codigo,
    descricao: categoria && t.descricao ? t.descricao : undefined,
    origem: t.origem,
  };
}

function paraResumo(s: SaldoMes): ResumoMes {
  return {
    entradas: valorParaCentavos(s.entradas),
    gastos: valorParaCentavos(s.gastos),
    contas: valorParaCentavos(s.contas),
    saldo: valorParaCentavos(s.saldo),
  };
}

const MENSAGEM_FALHA =
  'Não foi possível carregar seus dados agora. Verifique a internet e tente de novo.';

export function saldoPorDia(itens: Lancamento[], ateDia: number): PontoSaldo[] {
  const pontos: PontoSaldo[] = [];
  let saldo = 0;
  for (let dia = 1; dia <= ateDia; dia++) {
    for (const item of itens) {
      if (item.dia !== dia) continue;
      saldo += item.tipo === 'entrada' ? item.centavos : -item.centavos;
    }
    pontos.push({ dia, saldo });
  }
  return pontos;
}

export function totalEntradas(itens: Lancamento[]): number {
  return itens
    .filter((i) => i.tipo === 'entrada')
    .reduce((total, i) => total + i.centavos, 0);
}

export function totalGastos(itens: Lancamento[]): number {
  return itens
    .filter((i) => i.tipo === 'gasto')
    .reduce((total, i) => total + i.centavos, 0);
}

export function fracaoDisponivel(saldo: number, entradas: number): number {
  if (entradas <= 0) return 0;
  return Math.max(0, Math.min(1, saldo / entradas));
}

export function nivelDisponivel(fracao: number): 'bom' | 'atencao' | 'critico' {
  if (fracao > 0.5) return 'bom';
  if (fracao > 0.25) return 'atencao';
  return 'critico';
}

export function mensagemDisponivel(fracao: number): string {
  if (fracao > 0.5)
    return 'Mais da metade do seu dinheiro continua disponível no Vero.';
  if (fracao > 0.25)
    return 'Menos da metade do seu dinheiro continua disponível.';
  if (fracao > 0) return 'Atenção: seu dinheiro do mês está diminuindo.';
  return 'Você já gastou todo o saldo disponível do mês.';
}

export function escalaDoGrafico(valores: number[]): {
  minimo: number;
  maximo: number;
  passos: number;
} {
  const menor = valores.length ? Math.min(...valores) : 0;
  const maior = valores.length ? Math.max(...valores) : 200000;
  let minimo = Math.floor(menor / PASSO_ESCALA) * PASSO_ESCALA - PASSO_ESCALA;
  if (menor >= 0) minimo = Math.max(0, minimo);
  const maximo = Math.ceil(maior / PASSO_ESCALA) * PASSO_ESCALA + PASSO_ESCALA;
  const passos = Math.max(1, Math.round((maximo - minimo) / PASSO_ESCALA));
  return { minimo, maximo, passos };
}

export function puloDosRotulos(
  alturaPx: number,
  passos: number,
  minimoPx = 24
): number {
  return (
    [1, 2, 5, 10, 20, 50].find((k) => (alturaPx / passos) * k >= minimoPx) ?? 10
  );
}

export function useDadosDoMes() {
  const [hoje] = useState<Hoje>(() => calcularHoje());
  const [itens, setItens] = useState<Lancamento[]>([]);
  const [resumo, setResumo] = useState<ResumoMes>({
    entradas: 0,
    gastos: 0,
    contas: 0,
    saldo: 0,
  });
  const [meta, setMeta] = useState<number>(() => lerMeta(calcularHoje().mes));
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const categoriasRef = useRef<CategoriaApi[]>([]);

  const recarregar = useCallback(async () => {
    try {
      const [categorias, transacoes, saldo] = await Promise.all([
        listarCategorias().catch(() => categoriasRef.current),
        listarTransacoes(),
        obterSaldoMes(hoje.mes),
      ]);
      categoriasRef.current = categorias;
      setItens(
        transacoes
          .filter((t) => t.data.startsWith(hoje.mes))
          .map((t) => paraLancamento(t, categorias))
      );
      setResumo(paraResumo(saldo));
      setErro(null);
    } catch {
      setErro(MENSAGEM_FALHA);
    } finally {
      setCarregando(false);
    }
  }, [hoje.mes]);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const idDaCategoria = useCallback(
    async (codigo?: string): Promise<number | null> => {
      if (!codigo) return null;
      if (!categoriasRef.current.length) {
        categoriasRef.current = await listarCategorias();
      }
      return categoriasRef.current.find((c) => c.codigo === codigo)?.id ?? null;
    },
    []
  );

  /** Grava na API e atualiza a tela. Lança `ErroApi` se a gravação falhar. */
  const adicionarLancamento = useCallback(
    async (novo: NovoLancamento): Promise<Lancamento> => {
      const categoriaId =
        novo.tipo === 'gasto'
          ? await idDaCategoria(novo.categoriaCodigo)
          : null;
      const salva = await anotarTransacao({
        tipo: novo.tipo === 'entrada' ? 'entrada' : 'saida',
        valor: centavosParaValor(novo.centavos),
        origem: novo.origem ?? 'manual',
        data: novo.data,
        descricao: novo.descricao?.trim() || null,
        categoria_id: categoriaId,
      });
      await recarregar();
      return paraLancamento(salva, categoriasRef.current);
    },
    [idDaCategoria, recarregar]
  );

  const editarLancamento = useCallback(
    async (id: string, mudanca: MudancaLancamento): Promise<void> => {
      await editarTransacao(id, {
        ...(mudanca.centavos !== undefined
          ? { valor: centavosParaValor(mudanca.centavos) }
          : {}),
        ...(mudanca.data ? { data: mudanca.data } : {}),
        ...(mudanca.categoriaCodigo
          ? { categoria_id: await idDaCategoria(mudanca.categoriaCodigo) }
          : {}),
      });
      await recarregar();
    },
    [idDaCategoria, recarregar]
  );

  const removerLancamento = useCallback(
    async (id: string): Promise<void> => {
      await excluirTransacao(id);
      await recarregar();
    },
    [recarregar]
  );

  const definirMeta = useCallback(
    (centavos: number) => {
      setMeta(centavos);
      gravarMeta(hoje.mes, centavos);
    },
    [hoje.mes]
  );

  const estado: EstadoMes = { mes: hoje.mes, meta, itens };

  return {
    hoje,
    estado,
    resumo,
    carregando,
    erro,
    recarregar,
    adicionarLancamento,
    editarLancamento,
    removerLancamento,
    definirMeta,
  };
}

import { useState, useEffect, useCallback } from 'react';

export type TipoLancamento = 'gasto' | 'entrada';

export interface Lancamento {
  id: number;
  dia: number;
  tipo: TipoLancamento;
  centavos: number;
  categoria: string;
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

export interface EstadoMes {
  mes: string;
  meta: number; // centavos
  entradasFixas: number; // centavos da renda mensal do usuário
  itens: Lancamento[];
}

const CHAVE_ARMAZENAMENTO = 'vero-dados-do-mes';
export const PASSO_ESCALA = 10000; // R$ 100,00 entre marcas

export function calcularHoje(): Hoje {
  const data = new Date();
  return {
    mes: `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, '0')}`,
    dia: data.getDate(),
    diasNoMes: new Date(data.getFullYear(), data.getMonth() + 1, 0).getDate(),
  };
}

export function estadoPadraoVazio(hoje: Hoje): EstadoMes {
  return {
    mes: hoje.mes,
    meta: 0,
    entradasFixas: 0,
    itens: [],
  };
}

export function estadoPadraoExemplo(hoje: Hoje): EstadoMes {
  const diaMax = (d: number) => Math.min(d, hoje.dia);
  return {
    mes: hoje.mes,
    meta: 200000, // R$ 2.000,00 de meta
    entradasFixas: 330000, // R$ 3.300,00 de salário/renda mensal
    itens: [
      { id: 1, dia: diaMax(1), tipo: 'entrada', centavos: 330000, categoria: 'Salário / Renda' },
      { id: 2, dia: diaMax(3), tipo: 'gasto', centavos: 25000, categoria: 'Contas' },
      { id: 3, dia: diaMax(5), tipo: 'gasto', centavos: 18000, categoria: 'Mercado' },
      { id: 4, dia: diaMax(7), tipo: 'gasto', centavos: 9000, categoria: 'Transporte' },
      { id: 5, dia: Math.max(1, hoje.dia - 1), tipo: 'gasto', centavos: 4500, categoria: 'Farmácia' },
      { id: 6, dia: hoje.dia, tipo: 'gasto', centavos: 12000, categoria: 'Mercado' },
    ],
  };
}

export function carregarEstadoMes(hoje: Hoje): EstadoMes {
  try {
    const salvo = localStorage.getItem(CHAVE_ARMAZENAMENTO);
    if (salvo) {
      const parsed = JSON.parse(salvo) as EstadoMes;
      if (parsed.mes === hoje.mes && Array.isArray(parsed.itens)) {
        return parsed;
      }
    }
  } catch {
    // Caso localStorage não esteja acessível
  }
  return estadoPadraoVazio(hoje);
}

export function salvarEstadoMes(estado: EstadoMes): void {
  try {
    localStorage.setItem(CHAVE_ARMAZENAMENTO, JSON.stringify(estado));
  } catch {
    // Falha silenciosa
  }
}

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
  if (fracao > 0.5) return 'Mais da metade do seu dinheiro continua disponível no Vero.';
  if (fracao > 0.25) return 'Menos da metade do seu dinheiro continua disponível.';
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

export function puloDosRotulos(alturaPx: number, passos: number, minimoPx = 24): number {
  return [1, 2, 5, 10, 20, 50].find((k) => (alturaPx / passos) * k >= minimoPx) ?? 10;
}

export function useDadosDoMes() {
  const [hoje, setHoje] = useState<Hoje>(() => calcularHoje());
  const [estado, setEstado] = useState<EstadoMes>(() => carregarEstadoMes(calcularHoje()));

  useEffect(() => {
    const agora = calcularHoje();
    setHoje(agora);
    setEstado(carregarEstadoMes(agora));
  }, []);

  const atualizar = useCallback((mudar: (atual: EstadoMes) => EstadoMes) => {
    setEstado((atual) => {
      const novo = mudar(atual);
      salvarEstadoMes(novo);
      return novo;
    });
  }, []);

  const adicionarLancamento = useCallback(
    (tipo: TipoLancamento, centavos: number, categoria: string) => {
      const id = Date.now();
      const dia = calcularHoje().dia;
      atualizar((atual) => ({
        ...atual,
        itens: [...atual.itens, { id, dia, tipo, centavos, categoria }],
      }));
      return id;
    },
    [atualizar]
  );

  const definirMeta = useCallback(
    (centavos: number) => {
      atualizar((atual) => ({ ...atual, meta: centavos }));
    },
    [atualizar]
  );

  const definirRenda = useCallback(
    (centavos: number) => {
      atualizar((atual) => {
        // Atualiza a renda fixa e ajusta a entrada do dia 1
        const itensAtualizados = atual.itens.map((item) =>
          item.id === 1 && item.tipo === 'entrada' ? { ...item, centavos } : item
        );
        return {
          ...atual,
          entradasFixas: centavos,
          itens: itensAtualizados,
        };
      });
    },
    [atualizar]
  );

  const removerLancamento = useCallback(
    (id: number) => {
      atualizar((atual) => ({
        ...atual,
        itens: atual.itens.filter((i) => i.id !== id),
      }));
    },
    [atualizar]
  );

  return {
    hoje,
    estado,
    adicionarLancamento,
    removerLancamento,
    definirMeta,
    definirRenda,
  };
}

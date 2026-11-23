import { describe, it, expect } from 'vitest';
import {
  isoParaBr,
  mensagemVencimentoAntigo,
  paraIso,
  vencimentoMinimo,
  vencimentoPorDiaEMes,
} from './vencimento';

const em = (ano: number, mes: number, dia: number) =>
  new Date(ano, mes - 1, dia, 23, 30);

describe('vencimento das contas', () => {
  it('usa a data local, não a UTC', () => {
    // 23h30 em Brasília já é o dia seguinte em UTC
    expect(paraIso(em(2026, 11, 23))).toBe('2026-11-23');
  });

  it('vencimento mínimo é o dia 1º do mês anterior (#121)', () => {
    expect(vencimentoMinimo(em(2026, 11, 23))).toBe('2026-10-01');
    expect(vencimentoMinimo(em(2027, 1, 10))).toBe('2026-12-01');
  });

  it('mensagem cita a data mínima em formato brasileiro', () => {
    expect(isoParaBr('2026-10-01')).toBe('01/10/2026');
    expect(mensagemVencimentoAntigo(em(2026, 11, 23))).toContain('01/10/2026');
  });

  describe('conta fixa por dia e mês (#120)', () => {
    const hoje = em(2026, 11, 23);

    it('mês atual: fica neste ano, mesmo com o dia já passado', () => {
      expect(vencimentoPorDiaEMes(10, 11, hoje)).toBe('2026-11-10');
    });

    it('próximo mês: fica neste ano', () => {
      expect(vencimentoPorDiaEMes(5, 12, hoje)).toBe('2026-12-05');
    });

    it('mês anterior: ainda neste ano (conta atrasada do mês passado)', () => {
      expect(vencimentoPorDiaEMes(1, 10, hoje)).toBe('2026-10-01');
    });

    it('mês que já ficou para trás: vai para o ano que vem', () => {
      expect(vencimentoPorDiaEMes(5, 9, hoje)).toBe('2027-09-05');
      expect(vencimentoPorDiaEMes(15, 1, hoje)).toBe('2027-01-15');
    });

    it('em janeiro, dezembro é o mês anterior (ano passado)', () => {
      expect(vencimentoPorDiaEMes(20, 12, em(2027, 1, 10))).toBe('2026-12-20');
    });

    it('dia que não existe no mês vira o último dia', () => {
      expect(vencimentoPorDiaEMes(31, 2, hoje)).toBe('2027-02-28');
      expect(vencimentoPorDiaEMes(31, 2, em(2028, 1, 5))).toBe('2028-02-29');
    });
  });
});

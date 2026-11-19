import { describe, it, expect, beforeEach } from 'vitest';
import { PASSOS_TOUR, marcarTourVisto, tourJaVisto } from './tourAudio';
import { limparSessao, salvarToken } from './api';

/** Token no formato JWT só com o `sub`; a assinatura não é conferida no app. */
const tokenDe = (sub: string) => {
  const corpo = btoa(JSON.stringify({ sub }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `cabecalho.${corpo}.assinatura`;
};

describe('Tour em áudio do primeiro acesso (US13)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('começa como não visto e fica visto depois de marcado', () => {
    expect(tourJaVisto()).toBe(false);
    marcarTourVisto();
    expect(tourJaVisto()).toBe(true);
  });

  it('guarda "tour visto" por pessoa, não por aparelho (#102)', () => {
    salvarToken(tokenDe('pessoa-a'));
    marcarTourVisto();
    expect(tourJaVisto()).toBe(true);

    limparSessao();
    salvarToken(tokenDe('pessoa-b'));
    expect(tourJaVisto()).toBe(false);

    marcarTourVisto();
    limparSessao();
    salvarToken(tokenDe('pessoa-a'));
    expect(tourJaVisto()).toBe(true);
  });

  it('token ilegível cai na marca do aparelho, sem quebrar', () => {
    salvarToken('nao-e-jwt');
    expect(tourJaVisto()).toBe(false);
    marcarTourVisto();
    expect(tourJaVisto()).toBe(true);
  });

  it('explica as telas e os botões principais', () => {
    const textos = PASSOS_TOUR.map((p) => `${p.titulo} ${p.texto}`).join(' ');
    for (const assunto of [
      /saldo/i,
      /ouvir/i,
      /anotar gasto ou recebimento/i,
      /extrato/i,
      /contas a pagar/i,
      /whatsapp/i,
      /ouvir explicação/i,
    ]) {
      expect(textos).toMatch(assunto);
    }
  });
});

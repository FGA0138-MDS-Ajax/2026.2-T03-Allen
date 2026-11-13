import { describe, it, expect, beforeEach } from 'vitest';
import { PASSOS_TOUR, marcarTourVisto, tourJaVisto } from './tourAudio';

describe('Tour em áudio do primeiro acesso (US13)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('começa como não visto e fica visto depois de marcado', () => {
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

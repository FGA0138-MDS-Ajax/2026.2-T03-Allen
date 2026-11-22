import { describe, it, expect } from 'vitest';
import { inteiroPorExtenso, reaisPorExtenso } from './valorPorExtenso';

describe('valores por extenso para leitura em voz alta (RF21 / #101)', () => {
  it('lê o exemplo do critério de aceite', () => {
    expect(reaisPorExtenso(125000)).toBe('mil duzentos e cinquenta reais');
  });

  it('usa "e" entre os grupos como se fala', () => {
    expect(inteiroPorExtenso(1200)).toBe('mil e duzentos');
    expect(inteiroPorExtenso(1050)).toBe('mil e cinquenta');
    expect(inteiroPorExtenso(2001)).toBe('dois mil e um');
    expect(inteiroPorExtenso(3300)).toBe('três mil e trezentos');
    expect(inteiroPorExtenso(1999)).toBe('mil novecentos e noventa e nove');
    expect(inteiroPorExtenso(100)).toBe('cem');
    expect(inteiroPorExtenso(101)).toBe('cento e um');
    expect(inteiroPorExtenso(15)).toBe('quinze');
    expect(inteiroPorExtenso(1_000_000)).toBe('um milhão');
    expect(inteiroPorExtenso(2_500_000)).toBe('dois milhões e quinhentos mil');
  });

  it('lê reais, centavos, singular e negativo', () => {
    expect(reaisPorExtenso(100)).toBe('um real');
    expect(reaisPorExtenso(1)).toBe('um centavo');
    expect(reaisPorExtenso(50)).toBe('cinquenta centavos');
    expect(reaisPorExtenso(3550)).toBe(
      'trinta e cinco reais e cinquenta centavos'
    );
    expect(reaisPorExtenso(0)).toBe('zero reais');
    expect(reaisPorExtenso(-3050)).toBe(
      'menos trinta reais e cinquenta centavos'
    );
    expect(reaisPorExtenso(100_000_000)).toBe('um milhão de reais');
  });

  it('não lê símbolo nem separadores', () => {
    expect(reaisPorExtenso(123456)).not.toMatch(/R\$|\d|[.,]/);
  });
});

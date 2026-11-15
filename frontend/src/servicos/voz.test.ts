import { describe, it, expect } from 'vitest';
import { escolherVozPtBr } from './voz';

const voz = (name: string, lang: string, localService = true) =>
  ({ name, lang, localService }) as SpeechSynthesisVoice;

describe('Escolha da voz de leitura (US13)', () => {
  it('prefere a voz natural em português do Brasil', () => {
    const vozes = [
      voz('Microsoft Maria - Portuguese (Brazil)', 'pt-BR'),
      voz('Microsoft Jenny Online (Natural) - English', 'en-US', false),
      voz(
        'Microsoft Francisca Online (Natural) - Portuguese (Brazil)',
        'pt-BR',
        false
      ),
    ];
    expect(escolherVozPtBr(vozes)?.name).toMatch(/francisca/i);
  });

  it('usa a voz do Google quando não há voz natural', () => {
    const vozes = [
      voz('Microsoft Maria - Portuguese (Brazil)', 'pt-BR'),
      voz('Google português do Brasil', 'pt-BR', false),
    ];
    expect(escolherVozPtBr(vozes)?.name).toMatch(/google/i);
  });

  it('cai para outro português e, sem nenhum, devolve null', () => {
    expect(escolherVozPtBr([voz('Joana', 'pt-PT')])?.name).toBe('Joana');
    expect(escolherVozPtBr([voz('Samantha', 'en-US')])).toBeNull();
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BotaoAudio } from './BotaoAudio';

class FalaFalsa {
  texto: string;
  lang = '';
  rate = 1;
  voice: SpeechSynthesisVoice | null = null;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(texto: string) {
    this.texto = texto;
  }
}

const vozNatural = {
  name: 'Microsoft Francisca Online (Natural) - Portuguese (Brazil)',
  lang: 'pt-BR',
  localService: false,
} as SpeechSynthesisVoice;

const speechSynthesisFalso = {
  speak: vi.fn(),
  cancel: vi.fn(),
  getVoices: vi.fn(() => [
    { name: 'Microsoft Maria', lang: 'pt-BR', localService: true },
    vozNatural,
  ]),
};

describe('Componente BotaoAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('SpeechSynthesisUtterance', FalaFalsa);
    Object.defineProperty(window, 'speechSynthesis', {
      value: speechSynthesisFalso,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    delete (window as unknown as Record<string, unknown>).speechSynthesis;
  });

  it('lê o texto com a mesma voz natural da explicação em áudio', () => {
    render(<BotaoAudio textoParaLer="Você ainda tem R$ 100,00." />);

    fireEvent.click(screen.getByRole('button', { name: /ouvir mensagem/i }));

    const fala = speechSynthesisFalso.speak.mock.calls[0][0] as FalaFalsa;
    expect(fala.texto).toBe('Você ainda tem R$ 100,00.');
    expect(fala.lang).toBe('pt-BR');
    expect(fala.voice).toBe(vozNatural);
  });
});

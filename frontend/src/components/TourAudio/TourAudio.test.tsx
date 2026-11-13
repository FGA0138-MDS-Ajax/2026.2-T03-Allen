import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { TourAudio } from './TourAudio';

const passos = [
  { titulo: 'Primeiro passo', texto: 'Explicação do primeiro passo.' },
  { titulo: 'Segundo passo', texto: 'Explicação do segundo passo.' },
];

// O jsdom não tem leitura em voz alta: simulamos a Web Speech API.
class FalaFalsa {
  texto: string;
  lang = '';
  rate = 1;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(texto: string) {
    this.texto = texto;
  }
}

let falas: FalaFalsa[] = [];
const speechSynthesisFalso = {
  speak: vi.fn((fala: FalaFalsa) => {
    falas.push(fala);
    fala.onstart?.();
  }),
  cancel: vi.fn(),
};

const ultimaFala = () => falas[falas.length - 1];

describe('Componente TourAudio (US13)', () => {
  beforeEach(() => {
    falas = [];
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

  it('não renderiza nada quando fechado', () => {
    const { container } = render(
      <TourAudio aberto={false} onFechar={() => {}} passos={passos} />
    );
    expect(container.firstChild).toBeNull();
    expect(speechSynthesisFalso.speak).not.toHaveBeenCalled();
  });

  it('fala o passo em voz alta e mostra o mesmo texto como legenda', () => {
    render(<TourAudio aberto onFechar={() => {}} passos={passos} />);

    expect(screen.getByRole('dialog')).toHaveAccessibleName('Primeiro passo');
    expect(screen.getByText('Explicação do primeiro passo.')).toBeVisible();
    expect(screen.getByText(/passo 1 de 2/i)).toBeInTheDocument();
    expect(ultimaFala().texto).toBe('Explicação do primeiro passo.');
    expect(ultimaFala().lang).toBe('pt-BR');
  });

  it('tem controles grandes de pausar, repetir e pular', () => {
    render(<TourAudio aberto onFechar={() => {}} passos={passos} />);

    fireEvent.click(screen.getByRole('button', { name: /pausar/i }));
    expect(speechSynthesisFalso.cancel).toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /continuar/i })).toBeVisible();

    const falasAntes = falas.length;
    fireEvent.click(screen.getByRole('button', { name: /repetir/i }));
    expect(falas.length).toBe(falasAntes + 1);
    expect(ultimaFala().texto).toBe('Explicação do primeiro passo.');

    fireEvent.click(screen.getByRole('button', { name: /pular/i }));
    expect(screen.getByText('Explicação do segundo passo.')).toBeVisible();
    expect(ultimaFala().texto).toBe('Explicação do segundo passo.');
  });

  it('avança sozinho quando termina de falar um passo', () => {
    vi.useFakeTimers();
    render(
      <TourAudio
        aberto
        onFechar={() => {}}
        passos={passos}
        pausaEntrePassosMs={500}
      />
    );

    act(() => {
      ultimaFala().onend?.();
      vi.advanceTimersByTime(500);
    });
    expect(screen.getByText('Explicação do segundo passo.')).toBeVisible();
    vi.useRealTimers();
  });

  it('conclui no último passo e permite sair a qualquer momento', () => {
    const onFechar = vi.fn();
    render(<TourAudio aberto onFechar={onFechar} passos={passos} />);

    fireEvent.click(
      screen.getByRole('button', { name: /sair da explicação/i })
    );
    expect(onFechar).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /pular/i }));
    fireEvent.click(screen.getByRole('button', { name: /concluir/i }));
    expect(onFechar).toHaveBeenCalledTimes(2);
  });

  it('sem leitura em voz alta, mostra só a legenda e deixa avançar', () => {
    delete (window as unknown as Record<string, unknown>).speechSynthesis;
    render(<TourAudio aberto onFechar={() => {}} passos={passos} />);

    expect(screen.getByText(/não faz leitura em voz alta/i)).toBeVisible();
    expect(screen.getByText('Explicação do primeiro passo.')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: /pular/i }));
    expect(screen.getByText('Explicação do segundo passo.')).toBeVisible();
  });
});

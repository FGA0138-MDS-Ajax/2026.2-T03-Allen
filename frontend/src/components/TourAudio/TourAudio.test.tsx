import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { TourAudio } from './TourAudio';
import {
  ESPERA_INICIO_FALA_MS,
  tempoMaximoFalaMs,
} from '../../servicos/tourAudio';

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
  onerror: ((evento: { error: string }) => void) | null = null;
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
    const extras = speechSynthesisFalso as unknown as Record<string, unknown>;
    delete extras.getVoices;
    delete extras.addEventListener;
    delete extras.removeEventListener;
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

  describe('falhas da fala (#99)', () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it('se o navegador não deixar falar sem toque, avisa e pede Continuar', () => {
      // Safari sem interação: speak não dispara nenhum evento
      speechSynthesisFalso.speak.mockImplementationOnce((fala: FalaFalsa) => {
        falas.push(fala);
      });
      render(<TourAudio aberto onFechar={() => {}} passos={passos} />);

      act(() => {
        vi.advanceTimersByTime(ESPERA_INICIO_FALA_MS);
      });
      expect(screen.getByText(/toque em continuar/i)).toBeVisible();

      const falasAntes = falas.length;
      fireEvent.click(screen.getByRole('button', { name: /continuar/i }));
      expect(falas.length).toBe(falasAntes + 1);
      expect(ultimaFala().texto).toBe('Explicação do primeiro passo.');
      expect(screen.queryByText(/toque em continuar/i)).toBeNull();
    });

    it('erro "not-allowed" também pede Continuar', () => {
      render(<TourAudio aberto onFechar={() => {}} passos={passos} />);
      act(() => {
        ultimaFala().onerror?.({ error: 'not-allowed' });
      });
      expect(screen.getByText(/toque em continuar/i)).toBeVisible();
      expect(screen.getByText('Explicação do primeiro passo.')).toBeVisible();
    });

    it('outro erro de fala não trava: avança para o próximo passo', () => {
      render(
        <TourAudio
          aberto
          onFechar={() => {}}
          passos={passos}
          pausaEntrePassosMs={500}
        />
      );
      act(() => {
        ultimaFala().onerror?.({ error: 'synthesis-failed' });
        vi.advanceTimersByTime(500);
      });
      expect(screen.getByText('Explicação do segundo passo.')).toBeVisible();
    });

    it('se o onend nunca chegar, avança depois do tempo máximo da fala', () => {
      render(
        <TourAudio
          aberto
          onFechar={() => {}}
          passos={passos}
          pausaEntrePassosMs={500}
        />
      );
      act(() => {
        vi.advanceTimersByTime(tempoMaximoFalaMs(passos[0].texto) + 500);
      });
      expect(screen.getByText('Explicação do segundo passo.')).toBeVisible();
    });

    it('as vozes chegarem depois não reinicia a fala do passo', () => {
      let aoMudarVozes: (() => void) | undefined;
      Object.assign(speechSynthesisFalso, {
        getVoices: () => [
          { name: 'Google', lang: 'pt-BR', localService: false },
        ],
        addEventListener: (_: string, fn: () => void) => {
          aoMudarVozes = fn;
        },
        removeEventListener: () => {},
      });
      render(<TourAudio aberto onFechar={() => {}} passos={passos} />);
      const falasAntes = falas.length;

      act(() => aoMudarVozes?.());
      expect(falas.length).toBe(falasAntes);
    });
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

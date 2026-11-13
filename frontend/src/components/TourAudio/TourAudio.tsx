import React, { useEffect, useRef, useState } from 'react';
import styles from './TourAudio.module.css';
import {
  IconSpeaker,
  IconPause,
  IconPlay,
  IconRepeat,
  IconSkip,
} from '../Icones/Icones';
import { PASSOS_TOUR, PassoTour } from '../../servicos/tourAudio';
import { criarFala, escolherVozPtBr } from '../../servicos/voz';

export interface TourAudioProps {
  aberto: boolean;
  onFechar: () => void;
  passos?: PassoTour[];
  /** Pausa entre o fim da fala de um passo e o começo do próximo. */
  pausaEntrePassosMs?: number;
}

const temVoz = () =>
  typeof window !== 'undefined' && 'speechSynthesis' in window;

/**
 * Explicação guiada em áudio (US13): fala cada passo em voz alta, mostra o
 * mesmo texto como legenda e oferece controles grandes de pausar, repetir e pular.
 */
export const TourAudio: React.FC<TourAudioProps> = ({
  aberto,
  onFechar,
  passos = PASSOS_TOUR,
  pausaEntrePassosMs = 1200,
}) => {
  const [passo, setPasso] = useState(0);
  const [pausado, setPausado] = useState(false);
  const [falando, setFalando] = useState(false);
  // Muda a cada "Repetir" para falar o mesmo passo de novo
  const [repeticao, setRepeticao] = useState(0);
  const tituloRef = useRef<HTMLHeadingElement>(null);
  const [voz, setVoz] = useState<SpeechSynthesisVoice | null>(null);

  const ultimo = passo === passos.length - 1;
  const vozDisponivel = temVoz();

  // A lista de vozes do navegador chega depois de carregar a página
  useEffect(() => {
    if (!vozDisponivel) return;
    const sintese = window.speechSynthesis;
    if (typeof sintese.getVoices !== 'function') return;

    const atualizar = () => setVoz(escolherVozPtBr(sintese.getVoices()));
    atualizar();
    sintese.addEventListener?.('voiceschanged', atualizar);
    return () => sintese.removeEventListener?.('voiceschanged', atualizar);
  }, [vozDisponivel]);

  useEffect(() => {
    if (aberto) {
      setPasso(0);
      setPausado(false);
    }
  }, [aberto]);

  useEffect(() => {
    if (aberto) tituloRef.current?.focus();
  }, [aberto, passo]);

  useEffect(() => {
    if (!aberto || pausado || !vozDisponivel) return;

    const sintese = window.speechSynthesis;
    // Falas canceladas (pausar, pular, fechar) não podem avançar o tour
    let ativa = true;
    let proximo: ReturnType<typeof setTimeout> | undefined;

    sintese.cancel();
    const fala = criarFala(passos[passo].texto, voz);
    fala.onstart = () => {
      if (ativa) setFalando(true);
    };
    fala.onend = () => {
      if (!ativa) return;
      setFalando(false);
      if (passo < passos.length - 1) {
        proximo = setTimeout(() => setPasso((p) => p + 1), pausaEntrePassosMs);
      }
    };
    fala.onerror = () => {
      if (ativa) setFalando(false);
    };
    sintese.speak(fala);

    return () => {
      ativa = false;
      if (proximo) clearTimeout(proximo);
      sintese.cancel();
      setFalando(false);
    };
  }, [
    aberto,
    pausado,
    passo,
    repeticao,
    passos,
    pausaEntrePassosMs,
    vozDisponivel,
    voz,
  ]);

  if (!aberto) return null;

  const pausarOuContinuar = () => setPausado((p) => !p);

  const repetir = () => {
    setPausado(false);
    setRepeticao((r) => r + 1);
  };

  const pular = () => {
    if (ultimo) {
      onFechar();
      return;
    }
    setPasso((p) => p + 1);
  };

  const atual = passos[passo];

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="tour-titulo"
      aria-describedby="tour-legenda"
    >
      <div className={styles.janela}>
        <div className={styles.topo}>
          <span className={styles.progresso}>
            Explicação · Passo {passo + 1} de {passos.length}
          </span>
          <span
            className={`${styles.indicadorVoz} ${falando ? styles.indicadorAtivo : ''}`}
          >
            <span aria-hidden="true" className={styles.iconeInline}>
              <IconSpeaker size={20} />
            </span>
            {!vozDisponivel
              ? 'Sem áudio neste aparelho'
              : falando
                ? 'Falando…'
                : pausado
                  ? 'Pausado'
                  : 'Em espera'}
          </span>
        </div>

        <h2
          id="tour-titulo"
          ref={tituloRef}
          tabIndex={-1}
          className={styles.titulo}
        >
          {atual.titulo}
        </h2>

        {/* Legenda: o mesmo texto que é falado, para quem não ouve */}
        <p id="tour-legenda" className={styles.legenda}>
          {atual.texto}
        </p>

        {!vozDisponivel && (
          <p className={styles.avisoSemVoz}>
            Este aparelho não faz leitura em voz alta. Leia a explicação acima e
            toque em Pular para seguir.
          </p>
        )}

        <div className={styles.controles}>
          <button
            type="button"
            className={styles.controle}
            onClick={pausarOuContinuar}
            disabled={!vozDisponivel}
          >
            <span aria-hidden="true" className={styles.iconeInline}>
              {pausado ? <IconPlay size={26} /> : <IconPause size={26} />}
            </span>
            {pausado ? 'Continuar' : 'Pausar'}
          </button>
          <button
            type="button"
            className={styles.controle}
            onClick={repetir}
            disabled={!vozDisponivel}
          >
            <span aria-hidden="true" className={styles.iconeInline}>
              <IconRepeat size={26} />
            </span>
            Repetir
          </button>
          <button
            type="button"
            className={`${styles.controle} ${styles.controlePrincipal}`}
            onClick={pular}
          >
            <span aria-hidden="true" className={styles.iconeInline}>
              <IconSkip size={26} />
            </span>
            {ultimo ? 'Concluir' : 'Pular'}
          </button>
        </div>

        <button type="button" className={styles.sair} onClick={onFechar}>
          Sair da explicação
        </button>
      </div>
    </div>
  );
};

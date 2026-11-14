import React, { useState } from 'react';
import styles from './BotaoAudio.module.css';
import { IconSpeaker, IconStop } from '../Icones/Icones';

export interface BotaoAudioProps {
  textoParaLer: string;
  rotuloAcessivel?: string;
  className?: string;
}

export const BotaoAudio: React.FC<BotaoAudioProps> = ({
  textoParaLer,
  rotuloAcessivel = 'Ouvir mensagem',
  className = '',
}) => {
  const [falando, setFalando] = useState(false);

  const executarLeitura = () => {
    if (!('speechSynthesis' in window)) {
      alert('Seu navegador não suporta leitura por áudio.');
      return;
    }

    window.speechSynthesis.cancel();

    if (falando) {
      setFalando(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(textoParaLer);
    utterance.lang = 'pt-BR';
    utterance.rate = 0.9;

    utterance.onstart = () => setFalando(true);
    utterance.onend = () => setFalando(false);
    utterance.onerror = () => setFalando(false);

    window.speechSynthesis.speak(utterance);
  };

  return (
    <button
      type="button"
      onClick={executarLeitura}
      className={`${styles.botaoAudio} ${falando ? styles.falando : ''} ${className}`}
      aria-label={`${rotuloAcessivel}: ${textoParaLer}`}
      title={rotuloAcessivel}
    >
      <span aria-hidden="true" style={{ display: 'inline-flex' }}>
        {falando ? <IconStop size={20} /> : <IconSpeaker size={20} />}
      </span>
      <span>{falando ? 'Parar' : 'Ouvir'}</span>
    </button>
  );
};

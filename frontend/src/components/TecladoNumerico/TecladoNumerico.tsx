import React, { useEffect } from 'react';
import styles from './TecladoNumerico.module.css';
import { IconBackspace } from '../Icones/Icones';

export interface TecladoNumericoProps {
  onDigito: (digito: string) => void;
  onApagar: () => void;
  onLimpar?: () => void;
  desabilitado?: boolean;
  capturarTeclado?: boolean;
}

export const TecladoNumerico: React.FC<TecladoNumericoProps> = ({
  onDigito,
  onApagar,
  onLimpar,
  desabilitado = false,
  capturarTeclado = false,
}) => {
  const digitos = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];

  useEffect(() => {
    if (!capturarTeclado || desabilitado) return;

    const tratarKeyDown = (evento: KeyboardEvent) => {
      const elementoAtivo = document.activeElement;
      const estaNoInput =
        elementoAtivo &&
        (elementoAtivo.tagName === 'INPUT' ||
          elementoAtivo.tagName === 'TEXTAREA');

      if (estaNoInput) return;

      if (/^[0-9]$/.test(evento.key)) {
        evento.preventDefault();
        onDigito(evento.key);
      } else if (evento.key === 'Backspace') {
        evento.preventDefault();
        onApagar();
      } else if (
        (evento.key === 'Escape' || evento.key === 'Delete') &&
        onLimpar
      ) {
        evento.preventDefault();
        onLimpar();
      }
    };

    window.addEventListener('keydown', tratarKeyDown);
    return () => window.removeEventListener('keydown', tratarKeyDown);
  }, [capturarTeclado, desabilitado, onDigito, onApagar, onLimpar]);

  return (
    <div role="group" aria-label="Teclado numérico" className={styles.grid}>
      {digitos.map((d) => (
        <button
          key={d}
          type="button"
          disabled={desabilitado}
          onClick={() => onDigito(d)}
          className={styles.tecla}
          aria-label={d}
        >
          {d}
        </button>
      ))}

      {onLimpar ? (
        <button
          type="button"
          disabled={desabilitado}
          onClick={onLimpar}
          className={`${styles.tecla} ${styles.teclaAcao}`}
          aria-label="Limpar"
        >
          Limpar
        </button>
      ) : (
        <div aria-hidden="true" />
      )}

      <button
        type="button"
        disabled={desabilitado}
        onClick={() => onDigito('0')}
        className={styles.tecla}
        aria-label="0"
      >
        0
      </button>

      <button
        type="button"
        disabled={desabilitado}
        onClick={onApagar}
        className={`${styles.tecla} ${styles.teclaAcao}`}
        aria-label="Apagar dígito"
      >
        <span aria-hidden="true" style={{ display: 'inline-flex' }}>
          <IconBackspace size={24} />
        </span>
        <span>Apagar</span>
      </button>
    </div>
  );
};

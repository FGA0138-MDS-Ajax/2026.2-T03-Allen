import React, { useEffect, useRef, useState } from 'react';
import styles from './ConfirmacaoSucesso.module.css';
import { IconCheck } from '../Icones/Icones';

export interface ConfirmacaoSucessoProps {
  aberta: boolean;
  mensagem: string;
  onIrParaInicio: () => void;
  onDesfazer?: () => void;
  onContinuar?: () => void;
  textoContinuar?: string;
  segundosDesfazer?: number;
}

export const ConfirmacaoSucesso: React.FC<ConfirmacaoSucessoProps> = ({
  aberta,
  mensagem,
  onIrParaInicio,
  onDesfazer,
  onContinuar,
  textoContinuar = 'Anotar outro gasto',
  segundosDesfazer = 10,
}) => {
  const [tempoRestante, setTempoRestante] = useState(segundosDesfazer);
  const tituloRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!aberta) return;
    setTempoRestante(segundosDesfazer);
    tituloRef.current?.focus();

    const intervalo = setInterval(() => {
      setTempoRestante((ant) => Math.max(0, ant - 1));
    }, 1000);

    return () => clearInterval(intervalo);
  }, [aberta, segundosDesfazer]);

  if (!aberta) return null;

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmacao-titulo"
    >
      <div className={styles.modal}>
        <div className={styles.iconeCirculo} aria-hidden="true">
          <IconCheck size={48} />
        </div>

        <h2
          id="confirmacao-titulo"
          ref={tituloRef}
          tabIndex={-1}
          className={styles.titulo}
        >
          Tudo certo!
        </h2>

        <p className={styles.mensagem}>{mensagem}</p>

        <div className={styles.acoes}>
          <button
            type="button"
            className={styles.btnInicio}
            onClick={onIrParaInicio}
          >
            Ir para a tela inicial
          </button>

          {onDesfazer && tempoRestante > 0 && (
            <button
              type="button"
              className={styles.btnDesfazer}
              onClick={onDesfazer}
            >
              Desfazer ({tempoRestante}s)
            </button>
          )}

          {onContinuar && (
            <button
              type="button"
              className={styles.btnSecundario}
              onClick={onContinuar}
            >
              {textoContinuar}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

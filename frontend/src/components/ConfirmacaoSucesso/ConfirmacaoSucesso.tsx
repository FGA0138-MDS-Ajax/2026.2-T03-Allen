import React, { useEffect, useRef, useState } from 'react';
import styles from './ConfirmacaoSucesso.module.css';
import { IconCheck } from '../Icones/Icones';

export interface ConfirmacaoSucessoProps {
  aberta: boolean;
  mensagem: string;
  onIrParaInicio: () => void;
  onDesfazer?: () => void | Promise<void>;
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
  const [interagindoDesfazer, setInteragindoDesfazer] = useState(false);
  const [desfazendo, setDesfazendo] = useState(false);
  const tituloRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!aberta) {
      setInteragindoDesfazer(false);
      setDesfazendo(false);
      return;
    }
    setTempoRestante(segundosDesfazer);
    tituloRef.current?.focus();
  }, [aberta, segundosDesfazer]);

  // WCAG 2.2.1: pausa a contagem enquanto o usuário interage com o botão Desfazer
  useEffect(() => {
    if (!aberta || !onDesfazer || interagindoDesfazer || desfazendo) return;

    const intervalo = setInterval(() => {
      setTempoRestante((ant) => Math.max(0, ant - 1));
    }, 1000);

    return () => clearInterval(intervalo);
  }, [aberta, onDesfazer, interagindoDesfazer, desfazendo]);

  const aoClicarDesfazer = async () => {
    if (!onDesfazer || desfazendo) return;
    setDesfazendo(true);
    try {
      await onDesfazer();
    } finally {
      setDesfazendo(false);
    }
  };

  if (!aberta) return null;

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmacao-titulo"
      aria-describedby="confirmacao-mensagem"
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

        {/* Lida junto com o título quando o foco entra no diálogo (RF20 / #100) */}
        <p id="confirmacao-mensagem" className={styles.mensagem}>
          {mensagem}
        </p>

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
              onClick={aoClicarDesfazer}
              disabled={desfazendo}
              onMouseEnter={() => setInteragindoDesfazer(true)}
              onMouseLeave={() => setInteragindoDesfazer(false)}
              onFocus={() => setInteragindoDesfazer(true)}
              onBlur={() => setInteragindoDesfazer(false)}
              onTouchStart={() => setInteragindoDesfazer(true)}
              onTouchEnd={() => setInteragindoDesfazer(false)}
            >
              {desfazendo
                ? 'Desfazendo...'
                : interagindoDesfazer
                  ? `Desfazer (${tempoRestante}s · pausado)`
                  : `Desfazer (${tempoRestante}s)`}
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

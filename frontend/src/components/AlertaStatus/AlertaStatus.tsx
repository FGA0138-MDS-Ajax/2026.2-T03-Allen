import React, { useEffect, useState } from 'react';
import styles from './AlertaStatus.module.css';
import { IconCheck, IconClock, IconAlert } from '../Icones/Icones';

export type TipoStatus = 'sucesso' | 'aviso' | 'erro';

export interface AlertaStatusProps {
  tipo: TipoStatus;
  children: React.ReactNode;
  role?: 'status' | 'alert';
}

const CONFIG_STATUS: Record<
  TipoStatus,
  { icone: React.ReactNode; label: string }
> = {
  sucesso: { icone: <IconCheck size={22} />, label: 'Sucesso' },
  aviso: { icone: <IconClock size={22} />, label: 'Aviso' },
  erro: { icone: <IconAlert size={22} />, label: 'Erro' },
};

export const AlertaStatus: React.FC<AlertaStatusProps> = ({
  tipo,
  children,
  role = 'status',
}) => {
  const { icone, label } = CONFIG_STATUS[tipo];
  // Leitores de tela ignoram região viva que já nasce com texto: a região entra
  // vazia e o conteúdo chega logo depois, para ser anunciado (RF20 / #100)
  const [pronto, setPronto] = useState(false);
  useEffect(() => {
    setPronto(true);
  }, []);

  return (
    <div
      role={role}
      aria-live="polite"
      className={`${styles.alerta} ${styles[tipo]}`}
    >
      {pronto && (
        <>
          <span className={styles.icone} aria-label={label} role="img">
            {icone}
          </span>
          <div className={styles.conteudo}>{children}</div>
        </>
      )}
    </div>
  );
};

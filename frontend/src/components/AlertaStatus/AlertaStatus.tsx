import React from 'react';
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

  return (
    <div
      role={role}
      aria-live="polite"
      className={`${styles.alerta} ${styles[tipo]}`}
    >
      <span className={styles.icone} aria-label={label} role="img">
        {icone}
      </span>
      <div className={styles.conteudo}>{children}</div>
    </div>
  );
};

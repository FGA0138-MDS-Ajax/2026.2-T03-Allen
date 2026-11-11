import { InputHTMLAttributes, forwardRef, useId } from 'react';
import styles from './CampoTexto.module.css';
import { IconAlert } from '../Icones/Icones';

export interface CampoTextoProps extends InputHTMLAttributes<HTMLInputElement> {
  rotulo: string;
  ajuda?: string;
  erro?: string;
}

export const CampoTexto = forwardRef<HTMLInputElement, CampoTextoProps>(
  ({ rotulo, ajuda, erro, id: idProp, className = '', ...resto }, ref) => {
    const reactId = useId();
    const id = idProp || reactId;
    const ajudaId = ajuda ? `${id}-ajuda` : undefined;
    const erroId = erro ? `${id}-erro` : undefined;

    const describedBy =
      [ajudaId, erroId].filter(Boolean).join(' ') || undefined;

    return (
      <div className={styles.container}>
        <label htmlFor={id} className={styles.label}>
          {rotulo}
        </label>

        {ajuda && (
          <span id={ajudaId} className={styles.ajuda}>
            {ajuda}
          </span>
        )}

        <input
          ref={ref}
          id={id}
          className={`${styles.input} ${erro ? styles.inputErro : ''} ${className}`}
          aria-invalid={Boolean(erro)}
          aria-describedby={describedBy}
          {...resto}
        />

        {erro && (
          <span id={erroId} role="alert" className={styles.mensagemErro}>
            <span aria-hidden="true" style={{ display: 'inline-flex' }}>
              <IconAlert size={18} />
            </span>
            <span>{erro}</span>
          </span>
        )}
      </div>
    );
  }
);

CampoTexto.displayName = 'CampoTexto';

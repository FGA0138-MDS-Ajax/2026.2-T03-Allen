import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import styles from './Botao.module.css';
import { IconClock } from '../Icones/Icones';

export interface BotaoProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  fullWidth?: boolean;
  carregando?: boolean;
  textoCarregando?: string;
  icone?: React.ReactNode;
}

export const Botao = forwardRef<HTMLButtonElement, BotaoProps>(
  (
    {
      children,
      variant = 'primary',
      fullWidth = false,
      carregando = false,
      textoCarregando = 'Carregando...',
      icone,
      className = '',
      disabled,
      ...resto
    },
    ref
  ) => {
    const classes = [
      styles.botao,
      styles[variant],
      fullWidth ? styles.fullWidth : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || carregando}
        aria-busy={carregando ? 'true' : undefined}
        {...resto}
      >
        {carregando ? (
          <>
            <span aria-hidden="true" style={{ display: 'inline-flex' }}>
              <IconClock size={18} />
            </span>
            <span>{textoCarregando}</span>
          </>
        ) : (
          <>
            {icone && <span aria-hidden="true">{icone}</span>}
            <span>{children}</span>
          </>
        )}
      </button>
    );
  }
);

Botao.displayName = 'Botao';

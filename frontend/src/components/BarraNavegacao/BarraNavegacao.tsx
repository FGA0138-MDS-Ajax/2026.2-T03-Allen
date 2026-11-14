import React from 'react';
import styles from './BarraNavegacao.module.css';
import { useNavegacao } from '../../router';
import { limparSessao } from '../../servicos';
import { useTourAudio } from '../TourAudio/contextoTour';
import {
  IconVero,
  IconBills,
  IconPlus,
  IconClock,
  IconLogout,
  IconSpeaker,
} from '../Icones/Icones';

export interface BarraNavegacaoProps {
  rotaAtiva?: string;
}

export const BarraNavegacao: React.FC<BarraNavegacaoProps> = ({
  rotaAtiva,
}) => {
  const { navegar, rota } = useNavegacao();
  const { abrirTour } = useTourAudio();
  const rotaAtual = rotaAtiva || rota;

  const sair = () => {
    limparSessao();
    navegar('/entrar');
  };

  return (
    <header className={styles.navbar}>
      <div className={styles.container}>
        <a
          href="/inicio"
          className={styles.brandLogo}
          onClick={(e) => {
            e.preventDefault();
            navegar('/inicio');
          }}
          aria-label="Vero - Página inicial"
        >
          <IconVero size={32} />
          <span>Vero</span>
        </a>

        <nav className={styles.linksNavegacao} aria-label="Navegação principal">
          <button
            type="button"
            className={`${styles.navItem} ${
              rotaAtual === '/inicio' ? styles.navItemAtivo : ''
            }`}
            onClick={() => navegar('/inicio')}
            aria-current={rotaAtual === '/inicio' ? 'page' : undefined}
          >
            <span>Início</span>
          </button>

          <button
            type="button"
            className={`${styles.navItem} ${
              rotaAtual === '/extrato' ? styles.navItemAtivo : ''
            }`}
            onClick={() => navegar('/extrato')}
            aria-current={rotaAtual === '/extrato' ? 'page' : undefined}
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-flex', marginRight: 4 }}
            >
              <IconClock size={18} />
            </span>
            <span>Extrato</span>
          </button>

          <button
            type="button"
            className={`${styles.navItem} ${
              rotaAtual === '/anotar-gasto' ? styles.navItemAtivo : ''
            }`}
            onClick={() => navegar('/anotar-gasto')}
            aria-current={rotaAtual === '/anotar-gasto' ? 'page' : undefined}
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-flex', marginRight: 4 }}
            >
              <IconPlus size={18} />
            </span>
            <span>Anotar Gasto/Recebimento</span>
          </button>

          <button
            type="button"
            className={`${styles.navItem} ${
              rotaAtual === '/contas' || rotaAtual === '/'
                ? styles.navItemAtivo
                : ''
            }`}
            onClick={() => navegar('/contas')}
            aria-current={
              rotaAtual === '/contas' || rotaAtual === '/' ? 'page' : undefined
            }
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-flex', marginRight: 4 }}
            >
              <IconBills size={18} />
            </span>
            <span>Contas a Pagar</span>
          </button>
        </nav>

        <div className={styles.acoes}>
          {/* Reabre o tour em áudio do primeiro acesso (US13) */}
          <button
            type="button"
            className={styles.btnExplicacao}
            onClick={abrirTour}
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-flex', marginRight: 4 }}
            >
              <IconSpeaker size={18} />
            </span>
            <span>Ouvir explicação</span>
          </button>

          <button
            type="button"
            className={styles.btnSair}
            onClick={sair}
            aria-label="Sair da sua conta no Vero"
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-flex', marginRight: 4 }}
            >
              <IconLogout size={18} />
            </span>
            <span>Sair</span>
          </button>
        </div>
      </div>
    </header>
  );
};

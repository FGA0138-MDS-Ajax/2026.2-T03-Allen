import React from 'react';
import styles from './BarraNavegacao.module.css';
import { useNavegacao } from '../../router';
import { limparSessao } from '../../servicos';
import { useTourAudio } from '../TourAudio/contextoTour';
import {
  IconBills,
  IconPlus,
  IconClock,
  IconHome,
  IconLogout,
  IconSpeaker,
  IconProps,
} from '../Icones/Icones';
import logoVero from '../../assets/logoVero';

export interface BarraNavegacaoProps {
  rotaAtiva?: string;
}

interface ItemMenu {
  rota: string;
  /** Nome completo, lido pelo leitor de tela e mostrado no computador. */
  nome: string;
  /** Nome curto mostrado na barra de baixo do celular. */
  curto: string;
  Icone: React.FC<IconProps>;
  rotasAtivas: string[];
}

const ITENS_MENU: ItemMenu[] = [
  {
    rota: '/inicio',
    nome: 'Início',
    curto: 'Início',
    Icone: IconHome,
    rotasAtivas: ['/inicio'],
  },
  {
    rota: '/extrato',
    nome: 'Extrato',
    curto: 'Extrato',
    Icone: IconClock,
    rotasAtivas: ['/extrato'],
  },
  {
    rota: '/anotar-gasto',
    nome: 'Anotar Gasto/Recebimento',
    curto: 'Anotar',
    Icone: IconPlus,
    rotasAtivas: ['/anotar-gasto'],
  },
  {
    rota: '/contas',
    nome: 'Contas a Pagar',
    curto: 'Contas',
    Icone: IconBills,
    rotasAtivas: ['/contas', '/'],
  },
];

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
          <img src={logoVero} alt="" className={styles.logoImagem} />
        </a>

        {/* No celular vira uma barra fixa embaixo da tela, ao alcance do polegar */}
        <nav className={styles.linksNavegacao} aria-label="Navegação principal">
          {ITENS_MENU.map(
            ({ rota: destino, nome, curto, Icone, rotasAtivas }) => {
              const ativo = rotasAtivas.includes(rotaAtual);
              return (
                <button
                  key={destino}
                  type="button"
                  className={`${styles.navItem} ${ativo ? styles.navItemAtivo : ''}`}
                  onClick={() => navegar(destino)}
                  aria-current={ativo ? 'page' : undefined}
                  aria-label={nome}
                >
                  <span aria-hidden="true" className={styles.navIcone}>
                    <Icone size={22} />
                  </span>
                  <span aria-hidden="true" className={styles.rotuloCompleto}>
                    {nome}
                  </span>
                  <span aria-hidden="true" className={styles.rotuloCurto}>
                    {curto}
                  </span>
                </button>
              );
            }
          )}
        </nav>

        <div className={styles.acoes}>
          {/* Reabre o tour em áudio do primeiro acesso (US13) */}
          <button
            type="button"
            className={styles.btnExplicacao}
            onClick={abrirTour}
          >
            <span aria-hidden="true" className={styles.acaoIcone}>
              <IconSpeaker size={20} />
            </span>
            <span>Ouvir explicação</span>
          </button>

          <button
            type="button"
            className={styles.btnSair}
            onClick={sair}
            aria-label="Sair da sua conta no Vero"
          >
            <span aria-hidden="true" className={styles.acaoIcone}>
              <IconLogout size={20} />
            </span>
            <span>Sair</span>
          </button>
        </div>
      </div>
    </header>
  );
};

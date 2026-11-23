import React from 'react';
import { Botao, IconLock } from '../../components';
import { useNavegacao } from '../../router';
import logoVero from '../../assets/logoVero';
import styles from './BoasVindas.module.css';

export const BoasVindas: React.FC = () => {
  const { navegar } = useNavegacao();

  return (
    <main className={styles.container}>
      <div className={styles.contentBox}>
        <img src={logoVero} alt="Vero" className={styles.brandLogo} />

        <span className={styles.heroBadge}>
          <IconLock size={20} />
          <span>Acesso rápido e protegido</span>
        </span>

        <h1 className={styles.heroTitle}>Suas finanças na palma da sua mão.</h1>

        <p className={styles.heroSubtitle}>
          Controle seus gastos e saiba quanto tem disponível no mês, sem
          complicação ou linguagem contábil.
        </p>

        <div className={styles.acoesContainer}>
          <Botao variant="primary" fullWidth onClick={() => navegar('/entrar')}>
            Entrar
          </Botao>

          <Botao
            variant="secondary"
            fullWidth
            onClick={() => navegar('/cadastro')}
          >
            Ainda não tenho conta no Vero
          </Botao>
        </div>
      </div>
    </main>
  );
};

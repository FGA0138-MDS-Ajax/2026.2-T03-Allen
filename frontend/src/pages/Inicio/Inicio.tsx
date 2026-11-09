import React from 'react';
import styles from './Inicio.module.css';
import {
  BarraNavegacao,
  BotaoAudio,
  IconPlus,
  IconWhatsApp,
  IconBills,
  IconMarket,
  IconPharmacy,
  IconTransport,
  IconHome,
} from '../../components';
import { useNavegacao } from '../../router';

interface UltimoGasto {
  id: string;
  categoria: string;
  descricao: string;
  data: string;
  valor: number;
  icone: React.ReactNode;
}

const GASTOS_DEMO: UltimoGasto[] = [
  {
    id: '1',
    categoria: 'mercado',
    descricao: 'Compras de Mercado',
    data: 'Hoje',
    valor: 120.0,
    icone: <IconMarket size={24} />,
  },
  {
    id: '2',
    categoria: 'farmacia',
    descricao: 'Farmácia Popular',
    data: 'Ontem',
    valor: 45.0,
    icone: <IconPharmacy size={24} />,
  },
  {
    id: '3',
    categoria: 'transporte',
    descricao: 'Transporte e Ônibus',
    data: '07/11/2026',
    valor: 18.5,
    icone: <IconTransport size={24} />,
  },
  {
    id: '4',
    categoria: 'casa',
    descricao: 'Artigos para Casa',
    data: '05/11/2026',
    valor: 85.0,
    icone: <IconHome size={24} />,
  },
];

export const Inicio: React.FC = () => {
  const { navegar } = useNavegacao();
  const saldoDisponivel = 2500.0;
  const percentualDisponivel = 70; // 70% restante

  const formatarMoeda = (valor: number) => {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  const textoAudio = `Você ainda tem disponível no mês: dois mil e quinhentos reais. Mais da metade do seu dinheiro continua disponível no Vero.`;

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/inicio" />

      <main className={styles.conteudo}>
        <div className={styles.gradePrincipal}>
          {/* Coluna Principal */}
          <section aria-labelledby="titulo-saldo">
            <div className={styles.cardSaldo}>
              <div className={styles.topoSaldo}>
                <span id="titulo-saldo" className={styles.rotuloSaldo}>
                  Você ainda tem disponível no mês:
                </span>
                <BotaoAudio textoParaLer={textoAudio} />
              </div>

              <div
                className={styles.valorSaldo}
                data-testid="saldo-disponivel"
                aria-label={`Saldo disponível: ${formatarMoeda(saldoDisponivel)}`}
              >
                {formatarMoeda(saldoDisponivel)}
              </div>

              <div
                className={styles.barraProgresso}
                role="progressbar"
                aria-valuenow={percentualDisponivel}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label="Nível do saldo disponível no mês"
              >
                <div
                  className={`${styles.barraPreenchimento} ${styles.barraVerde}`}
                  style={{ width: `${percentualDisponivel}%` }}
                />
              </div>

              <p className={styles.textoStatusSaldo}>
                Mais da metade do seu dinheiro continua disponível no Vero.
              </p>
            </div>

            <div className={styles.acoesPrincipais}>
              <button
                type="button"
                className={styles.btnAcaoPrimaria}
                onClick={() => navegar('/anotar-gasto')}
              >
                <IconPlus size={24} />
                <span>Registrar novo gasto</span>
              </button>

              <button
                type="button"
                className={styles.btnContasAtalho}
                onClick={() => navegar('/contas')}
              >
                <IconBills size={22} />
                <span>Ver minhas contas a pagar</span>
              </button>

              <a
                href="https://wa.me/5561999998888"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.btnWhatsApp}
              >
                <IconWhatsApp size={24} />
                <span>Anotar gasto pelo WhatsApp</span>
              </a>
            </div>
          </section>

          {/* Coluna Lateral de Últimos Gastos */}
          <aside className={styles.cardLateral} aria-labelledby="titulo-ultimos-gastos">
            <h2 id="titulo-ultimos-gastos" className={styles.tituloLateral}>
              Últimos gastos anotados
            </h2>

            <div className={styles.listaGastos}>
              {GASTOS_DEMO.map((gasto) => (
                <div key={gasto.id} className={styles.itemGasto}>
                  <div className={styles.gastoInfo}>
                    <div className={styles.iconeGasto} aria-hidden="true">
                      {gasto.icone}
                    </div>
                    <div>
                      <div className={styles.nomeGasto}>{gasto.descricao}</div>
                      <div className={styles.dataGasto}>{gasto.data}</div>
                    </div>
                  </div>
                  <strong className={styles.valorGasto}>
                    - {formatarMoeda(gasto.valor)}
                  </strong>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

import React, { useEffect, useState, useMemo } from 'react';
import styles from './Inicio.module.css';
import {
  BarraNavegacao,
  BotaoAudio,
  GraficoSaldo,
  IconPlus,
  IconWhatsApp,
  IconBills,
  IconMarket,
  IconPharmacy,
  IconTransport,
  IconHome,
  IconOther,
  IconClock,
  IconAlert,
} from '../../components';
import { useNavegacao } from '../../router';
import { listarContas, ContaSaida } from '../../servicos';
import {
  useDadosDoMes,
  saldoPorDia,
  totalGastos,
  fracaoDisponivel,
  nivelDisponivel,
  mensagemDisponivel,
} from '../../servicos/dadosDoMes';

export const Inicio: React.FC = () => {
  const { navegar } = useNavegacao();
  const { hoje, estado, definirMeta } = useDadosDoMes();

  const [contas, setContas] = useState<ContaSaida[]>([]);
  const [carregandoContas, setCarregandoContas] = useState(true);
  const [metaDigitada, setMetaDigitada] = useState<string | null>(null);
  const [avisoMeta, setAvisoMeta] = useState<string>('Quanto você deseja guardar no fim do mês.');

  useEffect(() => {
    let ativo = true;
    listarContas()
      .then((resultado) => {
        if (ativo) setContas(resultado);
      })
      .catch(() => {
        // Se a API falhar ou não estiver logado, segue com lista vazia
      })
      .finally(() => {
        if (ativo) setCarregandoContas(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  // Total de contas pendentes (a vencer ou em atraso) em centavos
  const totalContasPendentesCentavos = useMemo(() => {
    return Math.round(
      contas
        .filter((c) => c.status !== 'paga')
        .reduce((soma, c) => soma + Number(c.valor), 0) * 100
    );
  }, [contas]);

  // Contas ordenadas pelas mais próximas de vencer
  const contasMaisProximas = useMemo(() => {
    return contas
      .filter((c) => c.status !== 'paga')
      .sort((a, b) => a.vencimento_em.localeCompare(b.vencimento_em))
      .slice(0, 3);
  }, [contas]);

  // Cálculo da composição do saldo disponível
  const entradasFixas = estado.entradasFixas;
  const gastosAnotados = totalGastos(estado.itens);
  const saldoDisponivelCentavos = Math.max(
    0,
    entradasFixas - totalContasPendentesCentavos - gastosAnotados
  );
  const fracao = fracaoDisponivel(saldoDisponivelCentavos, entradasFixas);
  const nivel = nivelDisponivel(fracao);

  // Pontos do gráfico de saldo dia a dia
  const pontos = useMemo(() => {
    return saldoPorDia(estado.itens, hoje.dia);
  }, [estado.itens, hoje.dia]);

  // Últimos valores anotados pelo usuário (mais recentes primeiro)
  const ultimosGastos = useMemo(() => {
    return [...estado.itens]
      .sort((a, b) => b.id - a.id)
      .slice(0, 4);
  }, [estado.itens]);

  const formatarMoeda = (centavos: number) => {
    return (centavos / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  const obterIcone = (categoria: string) => {
    const c = categoria.toLowerCase();
    if (c.includes('mercado') || c.includes('supermercado') || c.includes('feira')) {
      return <IconMarket size={22} />;
    }
    if (c.includes('farm') || c.includes('remed') || c.includes('saude')) {
      return <IconPharmacy size={22} />;
    }
    if (c.includes('casa') || c.includes('aluguel') || c.includes('condom')) {
      return <IconHome size={22} />;
    }
    if (c.includes('transporte') || c.includes('onibus') || c.includes('uber') || c.includes('combust')) {
      return <IconTransport size={22} />;
    }
    if (c.includes('conta') || c.includes('luz') || c.includes('agua') || c.includes('internet')) {
      return <IconBills size={22} />;
    }
    return <IconOther size={22} />;
  };

  const salvarMeta = (e: React.FormEvent) => {
    e.preventDefault();
    const reais = Number((metaDigitada ?? '').replace(/\D/g, ''));
    if (!reais) {
      setAvisoMeta('Digite um valor numérico para a meta, por exemplo 2000.');
      return;
    }
    definirMeta(reais * 100);
    setMetaDigitada(null);
    setAvisoMeta(`Meta de saldo salva: ${formatarMoeda(reais * 100)}.`);
  };

  const textoAudio = `Você ainda tem disponível no mês: ${formatarMoeda(
    saldoDisponivelCentavos
  )}. ${mensagemDisponivel(fracao)}`;

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/inicio" />

      <main className={styles.conteudo}>
        <div className={styles.gradePrincipal}>
          {/* Coluna da Esquerda: Saldo Disponível, Origem e Ações */}
          <div className={styles.coluna}>
            {/* Card Principal: Saldo Disponível com Origem Clara */}
            <section className={styles.card} aria-labelledby="titulo-saldo">
              <div className={styles.topoSaldo}>
                <span id="titulo-saldo" className={styles.rotuloSaldo}>
                  Você ainda tem disponível no mês:
                </span>
                <BotaoAudio textoParaLer={textoAudio} />
              </div>

              <div
                className={styles.valorSaldo}
                data-testid="saldo-disponivel"
                aria-label={`Saldo disponível no mês: ${formatarMoeda(saldoDisponivelCentavos)}`}
              >
                {formatarMoeda(saldoDisponivelCentavos)}
              </div>

              <div
                className={styles.barraProgresso}
                role="progressbar"
                aria-valuenow={Math.round(fracao * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label="Fração do dinheiro disponível no mês"
              >
                <div
                  className={`${styles.barraPreenchimento} ${
                    nivel === 'bom'
                      ? styles.barraVerde
                      : nivel === 'atencao'
                      ? styles.barraAmarela
                      : styles.barraVermelha
                  }`}
                  style={{ width: `${Math.round(fracao * 100)}%` }}
                />
              </div>

              <p className={styles.textoStatusSaldo}>{mensagemDisponivel(fracao)}</p>

              {/* Detalhamento didático: De onde sai esse saldo */}
              <div className={styles.origemSaldoBox}>
                <div className={styles.origemTitulo}>De onde sai esse saldo:</div>
                <div className={styles.origemLinha}>
                  <span>Salário e entradas do mês</span>
                  <strong className={styles.valorPositivo}>+ {formatarMoeda(entradasFixas)}</strong>
                </div>
                <div className={styles.origemLinha}>
                  <span>Contas a pagar cadastradas</span>
                  <strong className={styles.valorNegativo}>− {formatarMoeda(totalContasPendentesCentavos)}</strong>
                </div>
                <div className={styles.origemLinha}>
                  <span>Gastos anotados no dia a dia</span>
                  <strong className={styles.valorNegativo}>− {formatarMoeda(gastosAnotados)}</strong>
                </div>
                <div className={`${styles.origemLinha} ${styles.origemSoma}`}>
                  <span>Dinheiro livre que ainda sobra</span>
                  <span>= {formatarMoeda(saldoDisponivelCentavos)}</span>
                </div>
              </div>
            </section>

            {/* Ações Rápidas */}
            <div className={styles.acoesPrincipais}>
              <button
                type="button"
                className={styles.btnAcaoPrimaria}
                onClick={() => navegar('/anotar-gasto')}
              >
                <IconPlus size={24} />
                <span>Anotar novo gasto ou entrada</span>
              </button>

              <a
                href="https://wa.me/5561999998888"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.btnWhatsApp}
              >
                <IconWhatsApp size={22} />
                <span>Anotar gasto pelo WhatsApp</span>
              </a>
            </div>

            {/* Contas Mais Próximas de Vencer (RF25, RF30) */}
            <section className={styles.card} aria-labelledby="titulo-contas-urgentes">
              <div className={styles.tituloCard}>
                <h2 id="titulo-contas-urgentes" style={{ fontSize: 20, margin: 0 }}>
                  Contas mais próximas de vencer
                </h2>
                <button
                  type="button"
                  className={styles.linkVerTodas}
                  onClick={() => navegar('/contas')}
                >
                  Ver todas ({contas.length})
                </button>
              </div>

              {carregandoContas ? (
                <p style={{ color: 'var(--ardosia)', fontSize: 15 }}>Carregando contas cadastradas...</p>
              ) : contasMaisProximas.length === 0 ? (
                <p style={{ color: 'var(--ardosia)', fontSize: 15 }}>
                  Parabéns! Nenhuma conta pendente para este mês.
                </p>
              ) : (
                <div className={styles.listaContasProximas}>
                  {contasMaisProximas.map((conta) => {
                    const dataObj = new Date(conta.vencimento_em + 'T12:00:00');
                    const dataFormatada = dataObj.toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: 'short',
                    });
                    const valorNum = Number(conta.valor);

                    return (
                      <div key={conta.id} className={styles.itemContaProxima}>
                        <div className={styles.infoContaProxima}>
                          <div className={styles.iconeConta} aria-hidden="true">
                            {obterIcone(conta.descricao || 'contas')}
                          </div>
                          <div>
                            <strong style={{ display: 'block', fontSize: 15 }}>
                              {conta.descricao || 'Conta a pagar'}
                            </strong>
                            <span
                              className={`${styles.badgeUrgencia} ${
                                conta.status === 'em_atraso'
                                  ? styles.badgeAtraso
                                  : styles.badgeAVencer
                              }`}
                            >
                              {conta.status === 'em_atraso' ? (
                                <>
                                  <IconAlert size={12} style={{ display: 'inline', marginRight: 4 }} />
                                  Em atraso ({dataFormatada})
                                </>
                              ) : (
                                <>
                                  <IconClock size={12} style={{ display: 'inline', marginRight: 4 }} />
                                  Vence em {dataFormatada}
                                </>
                              )}
                            </span>
                          </div>
                        </div>
                        <strong style={{ fontSize: 17, color: 'var(--grafite-noturno)' }}>
                          {formatarMoeda(Math.round(valorNum * 100))}
                        </strong>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          </div>

          {/* Coluna da Direita: Dashboard da Sabrina (Meta de Saldo, Gráfico e Últimos Gastos) */}
          <div className={styles.coluna}>
            {/* Meta de Saldo do Mês */}
            <section className={styles.card} aria-labelledby="titulo-meta">
              <h2 id="titulo-meta" className={styles.tituloCard} style={{ marginBottom: 8 }}>
                Meta de saldo do mês
              </h2>
              <form onSubmit={salvarMeta} className={styles.formMeta}>
                <label htmlFor="input-meta-valor" style={{ fontSize: 15, color: 'var(--ardosia)', fontWeight: 600 }}>
                  Quanto você quer ter guardado no fim do mês:
                </label>
                <div className={styles.linhaEntradaMeta}>
                  <input
                    id="input-meta-valor"
                    type="text"
                    inputMode="numeric"
                    placeholder="Ex: 2000"
                    value={
                      metaDigitada !== null
                        ? metaDigitada
                        : (estado.meta / 100).toLocaleString('pt-BR')
                    }
                    onChange={(e) => setMetaDigitada(e.target.value)}
                    className={styles.inputMeta}
                    aria-label="Valor da meta de saldo em reais"
                  />
                  <button type="submit" className={styles.btnSalvarMeta}>
                    Salvar meta
                  </button>
                </div>

                <span role="status" className={styles.statusMeta}>
                  {avisoMeta}
                </span>

                <div className={styles.destaqueMeta}>
                  {saldoDisponivelCentavos >= estado.meta
                    ? '🎉 Seu saldo disponível está acima da meta do mês!'
                    : `Faltam ${formatarMoeda(
                        estado.meta - saldoDisponivelCentavos
                      )} para você alcançar sua meta.`}
                </div>
              </form>
            </section>

            {/* Gráfico de Evolução do Saldo */}
            <section className={styles.card} aria-labelledby="titulo-grafico">
              <h2 id="titulo-grafico" className={styles.tituloCard}>
                Seu saldo no mês
              </h2>
              <GraficoSaldo
                pontos={pontos}
                meta={estado.meta}
                diasNoMes={hoje.diasNoMes}
              />
            </section>

            {/* Últimos Valores Anotados (conectados em tempo real) */}
            <section className={styles.card} aria-labelledby="titulo-ultimos-gastos">
              <div className={styles.tituloCard}>
                <h2 id="titulo-ultimos-gastos" style={{ fontSize: 20, margin: 0 }}>
                  Últimos valores anotados
                </h2>
                <button
                  type="button"
                  className={styles.linkVerTodas}
                  onClick={() => navegar('/anotar-gasto')}
                >
                  + Anotar novo
                </button>
              </div>

              <div className={styles.listaGastos}>
                {ultimosGastos.map((item) => {
                  const ehEntrada = item.tipo === 'entrada';
                  const quando =
                    item.dia === hoje.dia
                      ? 'Hoje'
                      : item.dia === hoje.dia - 1
                      ? 'Ontem'
                      : `Dia ${item.dia}`;

                  return (
                    <div key={item.id} className={styles.itemGasto}>
                      <div className={styles.infoGasto}>
                        <div className={styles.iconeGasto} aria-hidden="true">
                          {obterIcone(item.categoria)}
                        </div>
                        <div>
                          <div className={styles.nomeGasto}>{item.categoria}</div>
                          <div className={styles.dataGasto}>{quando}</div>
                        </div>
                      </div>
                      <strong
                        className={styles.valorGasto}
                        style={{
                          color: ehEntrada
                            ? 'var(--sucesso-texto)'
                            : 'var(--erro-texto)',
                        }}
                      >
                        {ehEntrada ? '+' : '−'} {formatarMoeda(item.centavos)}
                      </strong>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

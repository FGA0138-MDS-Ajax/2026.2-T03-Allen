import React, { useEffect, useState, useMemo } from 'react';
import styles from './Extrato.module.css';
import {
  BarraNavegacao,
  BotaoAudio,
  AlertaStatus,
  IconMarket,
  IconPharmacy,
  IconBills,
  IconTransport,
  IconHome,
  IconOther,
  IconTrash,
} from '../../components';
import { listarContas, ContaSaida } from '../../servicos';
import { useDadosDoMes, Lancamento } from '../../servicos/dadosDoMes';

type FiltroTipo = 'todos' | 'gastos' | 'contas' | 'entradas';

interface ItemExtrato {
  id: string; // id único
  lancamentoId?: number; // presente se for gasto apagável
  titulo: string;
  categoria: string;
  tipo: 'gasto' | 'entrada' | 'conta';
  statusConta?: string;
  dataTexto: string;
  dataOrdenacao: number;
  centavos: number;
  ehGastoApagavel: boolean;
}

export const Extrato: React.FC = () => {
  const { hoje, estado, removerLancamento } = useDadosDoMes();
  const [contas, setContas] = useState<ContaSaida[]>([]);
  const [filtro, setFiltro] = useState<FiltroTipo>('todos');
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    listarContas()
      .then((res) => {
        if (ativo) setContas(res);
      })
      .catch(() => {});
    return () => {
      ativo = false;
    };
  }, []);

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

  // Junta lançamentos diários e contas cadastradas em uma única timeline
  const itensUnificados = useMemo<ItemExtrato[]>(() => {
    const lista: ItemExtrato[] = [];

    // 1. Lançamentos (gastos e entradas)
    estado.itens.forEach((item: Lancamento) => {
      lista.push({
        id: `lancamento-${item.id}`,
        lancamentoId: item.id,
        titulo: item.categoria,
        categoria: item.categoria,
        tipo: item.tipo,
        dataTexto:
          item.dia === hoje.dia
            ? 'Hoje'
            : item.dia === hoje.dia - 1
            ? 'Ontem'
            : `Dia ${item.dia}`,
        dataOrdenacao: item.dia,
        centavos: item.centavos,
        ehGastoApagavel: item.tipo === 'gasto',
      });
    });

    // 2. Contas cadastradas
    contas.forEach((conta) => {
      const dataObj = new Date(conta.vencimento_em + 'T12:00:00');
      const diaNum = dataObj.getDate();
      const dataFormatada = dataObj.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
      const centavosConta = Math.round(Number(conta.valor) * 100);

      lista.push({
        id: `conta-${conta.id}`,
        titulo: conta.descricao || 'Conta a pagar',
        categoria: conta.descricao || 'Contas',
        tipo: 'conta',
        statusConta: conta.status,
        dataTexto: `Vencimento em ${dataFormatada}`,
        dataOrdenacao: diaNum,
        centavos: centavosConta,
        ehGastoApagavel: false,
      });
    });

    // Ordenação do mais recente para o mais antigo
    return lista.sort((a, b) => b.dataOrdenacao - a.dataOrdenacao);
  }, [estado.itens, contas, hoje.dia]);

  // Totais
  const totalEntradas = useMemo(() => {
    return itensUnificados
      .filter((i) => i.tipo === 'entrada')
      .reduce((s, i) => s + i.centavos, 0);
  }, [itensUnificados]);

  const totalGastos = useMemo(() => {
    return itensUnificados
      .filter((i) => i.tipo === 'gasto')
      .reduce((s, i) => s + i.centavos, 0);
  }, [itensUnificados]);

  const totalContas = useMemo(() => {
    return itensUnificados
      .filter((i) => i.tipo === 'conta' && i.statusConta !== 'paga')
      .reduce((s, i) => s + i.centavos, 0);
  }, [itensUnificados]);

  const saldoFinal = Math.max(0, totalEntradas - totalGastos - totalContas);

  // Filtragem por abas
  const itensFiltrados = useMemo(() => {
    if (filtro === 'gastos') return itensUnificados.filter((i) => i.tipo === 'gasto');
    if (filtro === 'contas') return itensUnificados.filter((i) => i.tipo === 'conta');
    if (filtro === 'entradas') return itensUnificados.filter((i) => i.tipo === 'entrada');
    return itensUnificados;
  }, [itensUnificados, filtro]);

  const aoApagarGasto = (lancamentoId: number, nome: string) => {
    removerLancamento(lancamentoId);
    setMensagemSucesso(`Gasto de ${nome} apagado com sucesso do Vero.`);
  };

  const textoResumoAudio = `Extrato do mês: você tem ${formatarMoeda(
    totalEntradas
  )} em entradas, ${formatarMoeda(totalGastos)} em gastos do dia a dia e ${formatarMoeda(
    totalContas
  )} em contas a pagar. Seu saldo final disponível é ${formatarMoeda(saldoFinal)}.`;

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/extrato" />

      <main className={styles.conteudo}>
        <div className={styles.cabecalhoSecao}>
          <div>
            <h1 className={styles.tituloPrincipal}>Extrato de Movimentações</h1>
            <p className={styles.subtituloPrincipal}>
              Histórico detalhado de todos os seus gastos, entradas e contas deste mês.
            </p>
          </div>
          <BotaoAudio textoParaLer={textoResumoAudio} rotuloAcessivel="Ouvir extrato do mês" />
        </div>

        {mensagemSucesso && (
          <div style={{ marginBottom: 20 }}>
            <AlertaStatus tipo="sucesso">{mensagemSucesso}</AlertaStatus>
          </div>
        )}

        {/* Resumo Consolidado */}
        <section className={styles.gridResumo} aria-label="Resumo consolidado do extrato">
          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Entradas</span>
            <span className={`${styles.valorResumo} ${styles.valorPositivo}`}>
              + {formatarMoeda(totalEntradas)}
            </span>
          </div>

          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Gastos Anotados</span>
            <span className={`${styles.valorResumo} ${styles.valorNegativo}`}>
              − {formatarMoeda(totalGastos)}
            </span>
          </div>

          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Contas a Pagar</span>
            <span className={`${styles.valorResumo} ${styles.valorAviso}`}>
              − {formatarMoeda(totalContas)}
            </span>
          </div>

          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Saldo que Sobra</span>
            <span className={`${styles.valorResumo} ${styles.valorDestaque}`}>
              = {formatarMoeda(saldoFinal)}
            </span>
          </div>
        </section>

        {/* Abas de Filtro */}
        <div className={styles.filtrosContainer} role="tablist" aria-label="Filtrar tipo de movimentação">
          <button
            type="button"
            role="tab"
            aria-selected={filtro === 'todos'}
            className={`${styles.btnFiltro} ${filtro === 'todos' ? styles.btnFiltroAtivo : ''}`}
            onClick={() => setFiltro('todos')}
          >
            Todas ({itensUnificados.length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={filtro === 'gastos'}
            className={`${styles.btnFiltro} ${filtro === 'gastos' ? styles.btnFiltroAtivo : ''}`}
            onClick={() => setFiltro('gastos')}
          >
            Gastos ({itensUnificados.filter((i) => i.tipo === 'gasto').length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={filtro === 'contas'}
            className={`${styles.btnFiltro} ${filtro === 'contas' ? styles.btnFiltroAtivo : ''}`}
            onClick={() => setFiltro('contas')}
          >
            Contas ({itensUnificados.filter((i) => i.tipo === 'conta').length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={filtro === 'entradas'}
            className={`${styles.btnFiltro} ${filtro === 'entradas' ? styles.btnFiltroAtivo : ''}`}
            onClick={() => setFiltro('entradas')}
          >
            Entradas ({itensUnificados.filter((i) => i.tipo === 'entrada').length})
          </button>
        </div>

        {/* Lista de Itens */}
        <section aria-label="Lista de movimentações do extrato">
          {itensFiltrados.length === 0 ? (
            <div className={styles.estadoVazio}>
              <p>Nenhuma movimentação encontrada para o filtro selecionado.</p>
            </div>
          ) : (
            <div className={styles.listaMovimentacoes}>
              {itensFiltrados.map((item) => {
                const ehEntrada = item.tipo === 'entrada';

                return (
                  <div key={item.id} className={styles.cardItem}>
                    <div className={styles.infoEsquerda}>
                      <div className={styles.iconeContainer} aria-hidden="true">
                        {obterIcone(item.categoria)}
                      </div>
                      <div>
                        <span className={styles.descricaoItem}>{item.titulo}</span>
                        <div className={styles.metaItem}>
                          <span>{item.dataTexto}</span>
                          <span>•</span>
                          <span
                            className={`${styles.badgeTipo} ${
                              item.tipo === 'entrada'
                                ? styles.badgeEntrada
                                : item.tipo === 'gasto'
                                ? styles.badgeGasto
                                : item.statusConta === 'paga'
                                ? styles.badgeContaPaga
                                : styles.badgeConta
                            }`}
                          >
                            {item.tipo === 'entrada'
                              ? 'Entrada'
                              : item.tipo === 'gasto'
                              ? 'Gasto'
                              : item.statusConta === 'paga'
                              ? 'Conta Paga'
                              : 'Conta Pendente'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className={styles.infoDireita}>
                      <span
                        className={styles.valorItem}
                        style={{
                          color: ehEntrada
                            ? 'var(--sucesso-texto)'
                            : 'var(--erro-texto)',
                        }}
                      >
                        {ehEntrada ? '+' : '−'} {formatarMoeda(item.centavos)}
                      </span>

                      {/* Botão de Apagar Gasto */}
                      {item.ehGastoApagavel && item.lancamentoId !== undefined && (
                        <button
                          type="button"
                          className={styles.btnApagar}
                          onClick={() => aoApagarGasto(item.lancamentoId!, item.titulo)}
                          aria-label={`Apagar gasto de ${item.titulo}`}
                          title="Apagar este gasto"
                        >
                          <IconTrash size={20} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

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
import { listarContas, excluirConta, ContaSaida } from '../../servicos';
import { useDadosDoMes } from '../../servicos/dadosDoMes';

type FiltroTipo = 'todos' | 'gastos' | 'contas' | 'entradas';

interface ItemExtrato {
  id: string; // id único
  lancamentoId?: number; // presente se for gasto ou entrada local
  contaId?: string; // presente se for conta a pagar
  titulo: string;
  categoria: string;
  tipo: 'gasto' | 'entrada' | 'conta';
  statusConta?: string;
  dataTexto: string;
  dataOrdenacao: number;
  centavos: number;
  ehApagavel: boolean;
}

export const Extrato: React.FC = () => {
  const { hoje, estado, removerLancamento } = useDadosDoMes();
  const [contas, setContas] = useState<ContaSaida[]>([]);
  const [filtro, setFiltro] = useState<FiltroTipo>('todos');
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [itemParaExcluir, setItemParaExcluir] = useState<ItemExtrato | null>(
    null
  );

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
    const valor = Number.isFinite(centavos) ? centavos : 0;
    return (valor / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  const obterIcone = (categoria: string) => {
    const c = categoria.toLowerCase();
    if (
      c.includes('mercado') ||
      c.includes('supermercado') ||
      c.includes('feira')
    ) {
      return <IconMarket size={22} />;
    }
    if (c.includes('farm') || c.includes('remed') || c.includes('saude')) {
      return <IconPharmacy size={22} />;
    }
    if (c.includes('casa') || c.includes('aluguel') || c.includes('condom')) {
      return <IconHome size={22} />;
    }
    if (
      c.includes('transporte') ||
      c.includes('onibus') ||
      c.includes('uber') ||
      c.includes('combust')
    ) {
      return <IconTransport size={22} />;
    }
    if (
      c.includes('conta') ||
      c.includes('luz') ||
      c.includes('agua') ||
      c.includes('internet')
    ) {
      return <IconBills size={22} />;
    }
    return <IconOther size={22} />;
  };

  // Unifica gastos/entradas do mês e contas a pagar em uma lista única
  const itensUnificados = useMemo(() => {
    const lista: ItemExtrato[] = [];

    // 1. Gastos e Entradas locais
    estado.itens.forEach((item) => {
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
        ehApagavel: true,
      });
    });

    // 2. Contas cadastradas
    contas.forEach((conta) => {
      const dataObj = new Date(conta.vencimento_em + 'T12:00:00');
      const dataFormatada = dataObj.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
      const diaNum = dataObj.getDate();
      const centavosConta = Math.round(Number(conta.valor) * 100);

      lista.push({
        id: `conta-${conta.id}`,
        contaId: conta.id,
        titulo: conta.descricao || 'Conta sem nome',
        categoria: 'Contas',
        tipo: 'conta',
        statusConta: conta.status,
        dataTexto: `Vencimento em ${dataFormatada}`,
        dataOrdenacao: diaNum,
        centavos: centavosConta,
        ehApagavel: true,
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
    if (filtro === 'gastos')
      return itensUnificados.filter((i) => i.tipo === 'gasto');
    if (filtro === 'contas')
      return itensUnificados.filter((i) => i.tipo === 'conta');
    if (filtro === 'entradas')
      return itensUnificados.filter((i) => i.tipo === 'entrada');
    return itensUnificados;
  }, [itensUnificados, filtro]);

  const confirmarExclusao = async () => {
    if (!itemParaExcluir) return;

    if (itemParaExcluir.tipo === 'conta' && itemParaExcluir.contaId) {
      setContas((ant) => ant.filter((c) => c.id !== itemParaExcluir.contaId));
      await excluirConta(itemParaExcluir.contaId);
      setMensagemSucesso(
        `Conta "${itemParaExcluir.titulo}" apagada com sucesso do Vero.`
      );
    } else if (itemParaExcluir.lancamentoId !== undefined) {
      removerLancamento(itemParaExcluir.lancamentoId);
      setMensagemSucesso(
        `${itemParaExcluir.tipo === 'entrada' ? 'Recebimento' : 'Gasto'} de ${itemParaExcluir.titulo} apagado com sucesso do Vero.`
      );
    }

    setItemParaExcluir(null);
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
        {/* Cabeçalho */}
        <section className={styles.cabecalhoExtrato}>
          <div className={styles.topoTitulo}>
            <div>
              <h1 className={styles.titulo}>Extrato de movimentações</h1>
              <p className={styles.subtitulo}>
                Veja todas as entradas, gastos e contas do mês em um só lugar.
              </p>
            </div>
            <BotaoAudio textoParaLer={textoResumoAudio} />
          </div>

          {mensagemSucesso && (
            <div style={{ marginTop: 16 }}>
              <AlertaStatus tipo="sucesso">{mensagemSucesso}</AlertaStatus>
            </div>
          )}

          {/* Cards de Resumo */}
          <div className={styles.gradeResumo}>
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
              <span className={`${styles.valorResumo} ${styles.valorNegativo}`}>
                − {formatarMoeda(totalContas)}
              </span>
            </div>

            <div className={`${styles.cardResumo} ${styles.cardDestaque}`}>
              <span className={styles.rotuloResumo}>Saldo que Sobra</span>
              <span className={`${styles.valorResumo} ${styles.valorDestaque}`}>
                = {formatarMoeda(saldoFinal)}
              </span>
            </div>
          </div>
        </section>

        {/* Lista e Filtros */}
        <section className={styles.cardLista}>
          {/* Abas de Filtro */}
          <div
            className={styles.filtros}
            role="tablist"
            aria-label="Filtrar lançamentos do extrato"
          >
            <button
              type="button"
              role="tab"
              aria-selected={filtro === 'todos'}
              className={`${styles.btnFiltro} ${filtro === 'todos' ? styles.btnFiltroAtivo : ''}`}
              onClick={() => setFiltro('todos')}
            >
              Todos ({itensUnificados.length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={filtro === 'entradas'}
              className={`${styles.btnFiltro} ${filtro === 'entradas' ? styles.btnFiltroAtivo : ''}`}
              onClick={() => setFiltro('entradas')}
            >
              Entradas (
              {itensUnificados.filter((i) => i.tipo === 'entrada').length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={filtro === 'gastos'}
              className={`${styles.btnFiltro} ${filtro === 'gastos' ? styles.btnFiltroAtivo : ''}`}
              onClick={() => setFiltro('gastos')}
            >
              Gastos ({itensUnificados.filter((i) => i.tipo === 'gasto').length}
              )
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={filtro === 'contas'}
              className={`${styles.btnFiltro} ${filtro === 'contas' ? styles.btnFiltroAtivo : ''}`}
              onClick={() => setFiltro('contas')}
            >
              Contas ({itensUnificados.filter((i) => i.tipo === 'conta').length}
              )
            </button>
          </div>

          {/* Itens */}
          {itensFiltrados.length === 0 ? (
            <div className={styles.listaVazia}>
              <p>Nenhuma movimentação encontrada neste filtro.</p>
            </div>
          ) : (
            <div className={styles.listaItens}>
              {itensFiltrados.map((item) => {
                const ehEntrada = item.tipo === 'entrada';

                return (
                  <div key={item.id} className={styles.itemLinha}>
                    <div className={styles.infoEsquerda}>
                      <div className={styles.iconeContainer} aria-hidden="true">
                        {obterIcone(item.categoria)}
                      </div>
                      <div>
                        <div className={styles.tituloItem}>{item.titulo}</div>
                        <div className={styles.subItem}>
                          <span>{item.dataTexto}</span>
                          <span className={styles.pontoSeparador}>•</span>
                          <span className={styles.tagTipo}>
                            {ehEntrada
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

                      {/* Botão de Apagar (Disponível para gastos, entradas e contas) */}
                      {item.ehApagavel && (
                        <button
                          type="button"
                          className={styles.btnApagar}
                          onClick={() => setItemParaExcluir(item)}
                          aria-label={`Apagar ${ehEntrada ? 'entrada' : item.tipo === 'conta' ? 'conta' : 'gasto'} de ${item.titulo}`}
                          title={`Apagar este(a) ${ehEntrada ? 'recebimento' : item.tipo === 'conta' ? 'conta' : 'gasto'}`}
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

      {/* Modal Acessível de Confirmação de Exclusão (RF10 / #68) */}
      {itemParaExcluir && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-modal-excluir-extrato"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(26, 26, 46, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 16,
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: 20,
              padding: 24,
              maxWidth: 420,
              width: '100%',
              boxShadow: '0 12px 36px rgba(0,0,0,0.2)',
            }}
          >
            <h2
              id="titulo-modal-excluir-extrato"
              style={{
                fontFamily: 'var(--font-titulo)',
                fontSize: 22,
                color: 'var(--grafite-noturno)',
                marginBottom: 8,
              }}
            >
              Tem certeza que deseja apagar?
            </h2>
            <p
              style={{
                fontSize: 16,
                color: 'var(--ardosia)',
                lineHeight: 1.5,
                marginBottom: 20,
              }}
            >
              Você está prestes a apagar o lançamento de{' '}
              <strong>{itemParaExcluir.titulo}</strong> no valor de{' '}
              <strong>{formatarMoeda(itemParaExcluir.centavos)}</strong>. Essa
              ação não pode ser desfeita.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                type="button"
                onClick={confirmarExclusao}
                style={{
                  minHeight: 50,
                  borderRadius: 14,
                  backgroundColor: '#EF4444',
                  color: '#FFFFFF',
                  fontWeight: 700,
                  fontSize: 16,
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                Sim, apagar lançamento
              </button>

              <button
                type="button"
                onClick={() => setItemParaExcluir(null)}
                style={{
                  minHeight: 50,
                  borderRadius: 14,
                  backgroundColor: '#F3F4F6',
                  color: 'var(--grafite-noturno)',
                  fontWeight: 700,
                  fontSize: 16,
                  border: '1px solid #D1D5DB',
                  cursor: 'pointer',
                }}
              >
                Não, manter lançamento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

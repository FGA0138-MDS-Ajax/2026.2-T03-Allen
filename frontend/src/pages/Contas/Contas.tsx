import React, { useEffect, useState, useMemo } from 'react';
import {
  Botao,
  CampoTexto,
  TecladoNumerico,
  AlertaStatus,
  BotaoAudio,
  BarraNavegacao,
  IconBills,
  IconClock,
  IconAlert,
  IconCheck,
  IconPlus,
  IconArrowLeft,
  IconTrash,
  IconMarket,
  IconPharmacy,
  IconTransport,
  IconHome,
} from '../../components';
import { useNavegacao } from '../../router';
import {
  ContaSaida,
  listarContas,
  cadastrarConta,
  definirPagamentoConta,
  excluirConta,
  estaAutenticado,
  ErroApi,
} from '../../servicos';
import styles from './Contas.module.css';

type FiltroStatus = 'todas' | 'a_vencer' | 'em_atraso' | 'paga';

const SUGESTOES = ['Luz', 'Água', 'Aluguel', 'Internet', 'Telefone', 'Cartão'];

const obterIconeConta = (descricao?: string | null) => {
  const d = (descricao || '').toLowerCase();
  if (
    d.includes('mercado') ||
    d.includes('supermercado') ||
    d.includes('feira') ||
    d.includes('alimento') ||
    d.includes('comida')
  ) {
    return <IconMarket size={26} />;
  }
  if (
    d.includes('farm') ||
    d.includes('remed') ||
    d.includes('reméd') ||
    d.includes('saude') ||
    d.includes('saúde') ||
    d.includes('medic')
  ) {
    return <IconPharmacy size={26} />;
  }
  if (
    d.includes('aluguel') ||
    d.includes('condom') ||
    d.includes('casa') ||
    d.includes('iptu') ||
    d.includes('moradia')
  ) {
    return <IconHome size={26} />;
  }
  if (
    d.includes('transporte') ||
    d.includes('onibus') ||
    d.includes('ônibus') ||
    d.includes('uber') ||
    d.includes('combust') ||
    d.includes('gasolina') ||
    d.includes('carro')
  ) {
    return <IconTransport size={26} />;
  }
  return <IconBills size={26} />;
};

export const Contas: React.FC = () => {
  const { navegar } = useNavegacao();
  const [contas, setContas] = useState<ContaSaida[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState<FiltroStatus>('todas');
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [pendenteId, setPendenteId] = useState<string | null>(null);

  const [modoCadastro, setModoCadastro] = useState(false);
  const [valorDigitado, setValorDigitado] = useState('');
  const [descricao, setDescricao] = useState('');
  const [dataVencimento, setDataVencimento] = useState(() => {
    const data = new Date();
    data.setDate(data.getDate() + 7);
    return data.toISOString().split('T')[0];
  });
  const [salvando, setSalvando] = useState(false);
  const [recorrente, setRecorrente] = useState(false);
  const [contaParaExcluir, setContaParaExcluir] = useState<ContaSaida | null>(null);

  const carregarContas = async () => {
    if (!estaAutenticado()) {
      navegar('/entrar');
      return;
    }

    try {
      setCarregando(true);
      const lista = await listarContas();
      setContas(lista);
      setErro(null);
    } catch (e) {
      if (e instanceof ErroApi) {
        if (e.status === 401) {
          navegar('/entrar');
          return;
        }
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível carregar as contas a pagar.');
      }
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarContas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const centavosAtuais = valorDigitado ? parseInt(valorDigitado, 10) : 0;

  const formatarMoeda = (valor: number) => {
    const v = Number.isFinite(valor) ? valor : 0;
    return v.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };


  const digitar = (digito: string) => {
    if (valorDigitado.length < 8) {
      setValorDigitado((anterior) => anterior + digito);
    }
  };

  const apagar = () => {
    setValorDigitado((anterior) => anterior.slice(0, -1));
  };

  const salvarConta = async () => {
    if (centavosAtuais <= 0) {
      setErro('Informe um valor válido maior que zero.');
      return;
    }
    if (!dataVencimento) {
      setErro('Selecione o dia do vencimento da conta.');
      return;
    }

    setSalvando(true);
    setErro(null);

    try {
      await cadastrarConta({
        vencimento_em: dataVencimento,
        valor: centavosAtuais / 100,
        descricao: descricao.trim() || undefined,
        recorrente,
      });

      setMensagemSucesso('Conta cadastrada com sucesso!');
      setModoCadastro(false);
      setValorDigitado('');
      setDescricao('');
      setRecorrente(false);
      await carregarContas();
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível salvar a conta. Tente novamente.');
      }
    } finally {
      setSalvando(false);
    }
  };

  const confirmarExclusao = async () => {
    if (!contaParaExcluir) return;

    try {
      setErro(null);
      await excluirConta(contaParaExcluir.id);
      setContas((lista) => lista.filter((c) => c.id !== contaParaExcluir.id));
      setMensagemSucesso(
        `Conta "${contaParaExcluir.descricao || 'sem descrição'}" apagada com sucesso do Vero.`
      );
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível apagar a conta.');
      }
    } finally {
      setContaParaExcluir(null);
    }
  };

  const alternarPagamento = async (id: string, paga: boolean) => {
    try {
      setPendenteId(id);
      setErro(null);
      const atualizada = await definirPagamentoConta(id, paga);
      setContas((lista) => lista.map((c) => (c.id === id ? atualizada : c)));
      setMensagemSucesso(
        paga
          ? `Conta "${atualizada.descricao || 'sem descrição'}" marcada como paga!`
          : `Pagamento da conta "${atualizada.descricao || 'sem descrição'}" desfeito.`
      );
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível atualizar o pagamento da conta.');
      }
    } finally {
      setPendenteId(null);
    }
  };

  const resumo = useMemo(() => {
    let totalAVencer = 0;
    let totalAtraso = 0;
    let totalPago = 0;

    contas.forEach((c) => {
      const v = Number(c.valor);
      if (c.status === 'a_vencer') totalAVencer += v;
      else if (c.status === 'em_atraso') totalAtraso += v;
      else if (c.status === 'paga') totalPago += v;
    });

    return { totalAVencer, totalAtraso, totalPago };
  }, [contas]);

  const contasFiltradas = useMemo(() => {
    if (filtro === 'todas') return contas;
    return contas.filter((c) => c.status === filtro);
  }, [contas, filtro]);

  // Agrupamento diário de contas ordenado por vencimento (RF32, critério 1 / #78)
  const contasAgrupadasPorDia = useMemo(() => {
    const mapa = new Map<string, ContaSaida[]>();
    for (const conta of contasFiltradas) {
      const data = conta.vencimento_em;
      const existentes = mapa.get(data) || [];
      existentes.push(conta);
      mapa.set(data, existentes);
    }
    const datasOrdenadas = Array.from(mapa.keys()).sort();
    return datasOrdenadas.map((data) => ({
      data,
      contas: mapa.get(data)!,
    }));
  }, [contasFiltradas]);

  const textoResumoAudio = useMemo(() => {
    return `Você tem ${formatarMoeda(resumo.totalAVencer)} a vencer este mês, ${
      resumo.totalAtraso > 0 ? `${formatarMoeda(resumo.totalAtraso)} em atraso` : 'nenhuma conta em atraso'
    }, e ${formatarMoeda(resumo.totalPago)} já pagos no Vero.`;
  }, [resumo]);

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/contas" />

      <main>
        <div className={styles.cabecalhoSecao}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
            <h1 className={styles.tituloPrincipal} style={{ margin: 0 }}>Minhas Contas a Pagar</h1>
            <BotaoAudio textoParaLer={textoResumoAudio} rotuloAcessivel="Ouvir resumo de contas" />
          </div>
          <p className={styles.subtituloPrincipal}>
            Acompanhe o que já pagou e o que ainda precisa separar dinheiro este mês.
          </p>
        </div>

        {erro && (
          <div style={{ marginBottom: 20 }}>
            <AlertaStatus tipo="erro">{erro}</AlertaStatus>
          </div>
        )}

        {mensagemSucesso && (
          <div style={{ marginBottom: 20 }}>
            <AlertaStatus tipo="sucesso">{mensagemSucesso}</AlertaStatus>
          </div>
        )}

        <section className={styles.gridResumo} aria-label="Resumo geral das contas">
          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>A Vencer</span>
            <span className={`${styles.valorResumo} ${styles.destaqueAVencer}`}>
              {formatarMoeda(resumo.totalAVencer)}
            </span>
          </div>

          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Em Atraso</span>
            <span className={`${styles.valorResumo} ${styles.destaqueAtraso}`}>
              {formatarMoeda(resumo.totalAtraso)}
            </span>
          </div>

          <div className={styles.cardResumo}>
            <span className={styles.rotuloResumo}>Já Pagas</span>
            <span className={`${styles.valorResumo} ${styles.destaquePaga}`}>
              {formatarMoeda(resumo.totalPago)}
            </span>
          </div>
        </section>

        {modoCadastro && (
          <section className={styles.painelCadastro} aria-label="Cadastrar nova conta a pagar">
            <h2 className={styles.tituloPrincipal} style={{ fontSize: 24 }}>
              Cadastrar Nova Conta a Pagar
            </h2>
            <p className={styles.subtituloPrincipal} style={{ marginBottom: 16 }}>
              Informe o valor e a data de vencimento da conta.
            </p>

            <div className={styles.formGrid}>
              <div
                className={styles.displayValorCadastro}
                aria-live="polite"
                aria-label={`Valor da conta: ${formatarMoeda(centavosAtuais / 100)}`}
              >
                {formatarMoeda(centavosAtuais / 100)}
              </div>

              <TecladoNumerico onDigito={digitar} onApagar={apagar} capturarTeclado={modoCadastro} />

              <div>
                <CampoTexto
                  rotulo="Nome da conta (opcional)"
                  placeholder="Ex: Conta de Luz, Condomínio, Água"
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                />
                <div className={styles.sugestoesRapidas}>
                  {SUGESTOES.map((item) => (
                    <button
                      key={item}
                      type="button"
                      className={styles.btnSugestao}
                      onClick={() => setDescricao(item)}
                    >
                      + {item}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label
                  htmlFor="data-vencimento"
                  className={styles.rotuloResumo}
                  style={{ display: 'block', marginBottom: 6 }}
                >
                  Data de Vencimento
                </label>
                <input
                  id="data-vencimento"
                  type="date"
                  className={styles.campoData}
                  value={dataVencimento}
                  onChange={(e) => setDataVencimento(e.target.value)}
                />
              </div>

              <div>
                <label className={styles.checkboxContainer}>
                  <input
                    type="checkbox"
                    className={styles.checkboxInput}
                    checked={recorrente}
                    onChange={(e) => setRecorrente(e.target.checked)}
                  />
                  <span className={styles.checkboxTexto}>
                    🔁 Repetir todo mês (Conta fixa / recorrente)
                  </span>
                </label>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                <Botao
                  variant="primary"
                  onClick={salvarConta}
                  disabled={salvando || centavosAtuais <= 0}
                  fullWidth
                >
                  {salvando ? 'Salvando...' : 'Salvar Conta'}
                </Botao>
                <Botao
                  variant="secondary"
                  onClick={() => {
                    setModoCadastro(false);
                    setValorDigitado('');
                    setDescricao('');
                    setRecorrente(false);
                  }}
                  disabled={salvando}
                  fullWidth
                >
                  Cancelar
                </Botao>
              </div>
            </div>
          </section>
        )}

        {!modoCadastro && (
          <div className={styles.barraControles}>
            <div className={styles.filtrosContainer} role="tablist" aria-label="Filtros de situação das contas">
              <button
                type="button"
                role="tab"
                aria-selected={filtro === 'todas'}
                className={`${styles.btnFiltro} ${filtro === 'todas' ? styles.btnFiltroAtivo : ''}`}
                onClick={() => setFiltro('todas')}
              >
                Todas ({contas.length})
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={filtro === 'a_vencer'}
                className={`${styles.btnFiltro} ${filtro === 'a_vencer' ? styles.btnFiltroAtivo : ''}`}
                onClick={() => setFiltro('a_vencer')}
              >
                <IconClock size={16} /> A vencer ({contas.filter((c) => c.status === 'a_vencer').length})
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={filtro === 'em_atraso'}
                className={`${styles.btnFiltro} ${filtro === 'em_atraso' ? styles.btnFiltroAtivo : ''}`}
                onClick={() => setFiltro('em_atraso')}
              >
                <IconAlert size={16} /> Em atraso ({contas.filter((c) => c.status === 'em_atraso').length})
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={filtro === 'paga'}
                className={`${styles.btnFiltro} ${filtro === 'paga' ? styles.btnFiltroAtivo : ''}`}
                onClick={() => setFiltro('paga')}
              >
                <IconCheck size={16} /> Pagas ({contas.filter((c) => c.status === 'paga').length})
              </button>
            </div>

            <Botao
              variant="primary"
              onClick={() => {
                setModoCadastro(true);
                setMensagemSucesso(null);
              }}
              icone={<IconPlus size={20} />}
            >
              Cadastrar Nova Conta
            </Botao>
          </div>
        )}

        <section aria-label="Lista de contas a pagar">
          {carregando ? (
            <div className={styles.estadoVazio}>
              <p>Carregando contas cadastradas...</p>
            </div>
          ) : contasFiltradas.length === 0 ? (
            <div className={styles.estadoVazio}>
              <p className={styles.estadoVazioTitulo}>Nenhuma conta encontrada</p>
              <p>
                {filtro === 'todas'
                  ? 'Você ainda não cadastrou nenhuma conta a pagar no Vero.'
                  : 'Não há contas nesta situação no momento.'}
              </p>
            </div>
          ) : (
            <div className={styles.listaContas}>
              {contasAgrupadasPorDia.map((grupo) => {
                const dataObj = new Date(grupo.data + 'T12:00:00');
                const dataCabecalho = dataObj.toLocaleDateString('pt-BR', {
                  weekday: 'long',
                  day: '2-digit',
                  month: 'long',
                });
                const dataCabecalhoFormatada =
                  dataCabecalho.charAt(0).toUpperCase() + dataCabecalho.slice(1);

                return (
                  <section
                    key={grupo.data}
                    aria-label={`Contas para ${dataCabecalhoFormatada}`}
                    style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 8 }}
                  >
                    <div
                      style={{
                        fontSize: 16,
                        fontWeight: 700,
                        color: 'var(--violeta-profundo)',
                        backgroundColor: '#F3F0FB',
                        padding: '8px 14px',
                        borderRadius: 10,
                        borderLeft: '4px solid var(--violeta-vero)',
                      }}
                    >
                      {dataCabecalhoFormatada}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {grupo.contas.map((conta) => {
                        const valorNumerico = Number(conta.valor);
                        const dataFormatada = dataObj.toLocaleDateString('pt-BR', {
                          day: '2-digit',
                          month: 'long',
                          year: 'numeric',
                        });

                        return (
                          <div key={conta.id} className={styles.cardConta}>
                            <div className={styles.infoPrincipal}>
                              <div className={styles.iconeContainer} aria-hidden="true">
                                {obterIconeConta(conta.descricao)}
                              </div>
                              <div className={styles.detalhesTexto}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                  <span className={styles.nomeConta}>
                                    {conta.descricao || 'Conta sem descrição'}
                                  </span>
                                  {conta.recorrente && (
                                    <span className={styles.badgeRecorrente}>
                                      🔁 Todo mês
                                    </span>
                                  )}
                                </div>
                                <span className={styles.dataVencimento}>
                                  Vencimento: <strong>{dataFormatada}</strong>
                                </span>
                              </div>
                            </div>

                            <div className={styles.valoresEStatus}>
                              <div className={styles.blocoValorEBadge}>
                                <strong className={styles.valorConta}>
                                  {formatarMoeda(valorNumerico)}
                                </strong>

                                {conta.status === 'a_vencer' && (
                                  <span className={`${styles.badgeStatus} ${styles.badgeAVencer}`}>
                                    <IconClock size={16} aria-hidden="true" />
                                    <span>A vencer</span>
                                  </span>
                                )}

                                {conta.status === 'em_atraso' && (
                                  <span className={`${styles.badgeStatus} ${styles.badgeEmAtraso}`}>
                                    <IconAlert size={16} aria-hidden="true" />
                                    <span>Em atraso</span>
                                  </span>
                                )}

                                {conta.status === 'paga' && (
                                  <span className={`${styles.badgeStatus} ${styles.badgePaga}`}>
                                    <IconCheck size={16} aria-hidden="true" />
                                    <span>Paga</span>
                                  </span>
                                )}
                              </div>

                              <div className={styles.acoesPagamento}>
                                {conta.status !== 'paga' ? (
                                  <button
                                    type="button"
                                    className={styles.btnMarcarPaga}
                                    onClick={() => alternarPagamento(conta.id, true)}
                                    disabled={pendenteId === conta.id}
                                    aria-label={`Marcar a conta ${conta.descricao || 'sem descrição'} como paga`}
                                  >
                                    <IconCheck size={18} aria-hidden="true" />
                                    <span>{pendenteId === conta.id ? 'Salvando...' : 'Marcar como paga'}</span>
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    className={styles.btnDesfazerPaga}
                                    onClick={() => alternarPagamento(conta.id, false)}
                                    disabled={pendenteId === conta.id}
                                    aria-label={`Desfazer pagamento da conta ${conta.descricao || 'sem descrição'}`}
                                  >
                                    <IconArrowLeft size={16} aria-hidden="true" />
                                    <span>{pendenteId === conta.id ? 'Salvando...' : 'Desfazer pagamento'}</span>
                                  </button>
                                )}

                                <button
                                  type="button"
                                  className={styles.btnExcluir}
                                  onClick={() => setContaParaExcluir(conta)}
                                  aria-label={`Apagar conta ${conta.descricao || 'sem descrição'}`}
                                >
                                  <IconTrash size={18} aria-hidden="true" />
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {contaParaExcluir && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-modal-excluir-conta"
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
              id="titulo-modal-excluir-conta"
              style={{
                fontFamily: 'var(--font-titulo)',
                fontSize: 22,
                color: 'var(--grafite-noturno)',
                marginBottom: 8,
              }}
            >
              Tem certeza que deseja apagar?
            </h2>
            <p style={{ fontSize: 16, color: 'var(--ardosia)', lineHeight: 1.5, marginBottom: 20 }}>
              Você está prestes a apagar a conta{' '}
              <strong>{contaParaExcluir.descricao || 'sem descrição'}</strong> no valor de{' '}
              <strong>{formatarMoeda(Number(contaParaExcluir.valor))}</strong>. Essa ação não pode ser desfeita.
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
                Sim, apagar conta
              </button>

              <button
                type="button"
                onClick={() => setContaParaExcluir(null)}
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
                Não, manter conta
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

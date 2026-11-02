import React, { useEffect, useState, useMemo } from 'react';
import {
  Botao,
  CampoTexto,
  TecladoNumerico,
  AlertaStatus,
  BotaoAudio,
  IconVero,
  IconBills,
  IconClock,
  IconAlert,
  IconCheck,
  IconPlus,
  IconArrowLeft,
  IconLogout,
} from '../../components';
import { useNavegacao } from '../../router';
import {
  ContaSaida,
  listarContas,
  cadastrarConta,
  limparSessao,
  estaAutenticado,
  ErroApi,
} from '../../servicos';
import styles from './Contas.module.css';

type FiltroStatus = 'todas' | 'a_vencer' | 'em_atraso' | 'paga';

const SUGESTOES_CONTAS = ['Luz', 'Água', 'Aluguel', 'Internet', 'Telefone', 'Cartão'];

export const Contas: React.FC = () => {
  const { navegar } = useNavegacao();
  const [contas, setContas] = useState<ContaSaida[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState<FiltroStatus>('todas');
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  // Estado do formulário de cadastro de nova conta (RF25)
  const [modoCadastro, setModoCadastro] = useState(false);
  const [valorDigitado, setValorDigitado] = useState(''); // Centavos
  const [descricao, setDescricao] = useState('');
  const [dataVencimento, setDataVencimento] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split('T')[0];
  });
  const [salvando, setSalvando] = useState(false);

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
  }, []);

  const centavosAtuais = valorDigitado ? parseInt(valorDigitado, 10) : 0;

  const formatarMoeda = (valor: number) => {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  const handleDigito = (d: string) => {
    if (valorDigitado.length < 8) {
      setValorDigitado((prev) => prev + d);
    }
  };

  const handleApagar = () => {
    setValorDigitado((prev) => prev.slice(0, -1));
  };

  const handleSalvarConta = async () => {
    if (centavosAtuais <= 0) {
      setErro('Informe um valor válido maior que zero para a conta.');
      return;
    }
    if (!dataVencimento) {
      setErro('Selecione a data de vencimento da conta.');
      return;
    }

    setSalvando(true);
    setErro(null);

    try {
      const valorEmReais = centavosAtuais / 100;
      await cadastrarConta({
        vencimento_em: dataVencimento,
        valor: valorEmReais,
        descricao: descricao.trim() || undefined,
      });

      setMensagemSucesso('Conta cadastrada com sucesso!');
      setModoCadastro(false);
      setValorDigitado('');
      setDescricao('');
      await carregarContas();
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Erro ao salvar a conta. Verifique os dados e tente novamente.');
      }
    } finally {
      setSalvando(false);
    }
  };

  // Cálculos de resumo
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

  // Contas filtradas
  const contasFiltradas = useMemo(() => {
    if (filtro === 'todas') return contas;
    return contas.filter((c) => c.status === filtro);
  }, [contas, filtro]);

  const textoResumoAudio = useMemo(() => {
    return `Você tem ${formatarMoeda(resumo.totalAVencer)} a vencer este mês, ${
      resumo.totalAtraso > 0 ? `${formatarMoeda(resumo.totalAtraso)} em atraso` : 'nenhuma conta em atraso'
    }, e ${formatarMoeda(resumo.totalPago)} já pagos.`;
  }, [resumo]);

  return (
    <div className={styles.pageContainer}>
      <header className={styles.navbar}>
        <a
          href="/"
          className={styles.brandLogo}
          onClick={(e) => {
            e.preventDefault();
            navegar('/');
          }}
          aria-label="Vero - Início"
        >
          <IconVero size={34} />
          <span>Vero</span>
        </a>

        <div className={styles.navAcoes}>
          <Botao
            variant="secondary"
            onClick={() => navegar('/')}
            icone={<IconArrowLeft size={18} />}
          >
            Voltar ao Início
          </Botao>
          <Botao
            variant="secondary"
            onClick={() => {
              limparSessao();
              navegar('/entrar');
            }}
            aria-label="Sair da conta"
            icone={<IconLogout size={18} />}
          >
            Sair
          </Botao>
        </div>
      </header>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className={styles.tituloPrincipal}>Minhas Contas a Pagar</h1>
          <p className={styles.subtituloPrincipal}>
            Acompanhe o que já foi pago, o que está para vencer e o que está atrasado.
          </p>
        </div>

        <BotaoAudio
          textoParaLer={textoResumoAudio}
          rotuloAcessivel="Ouvir resumo das contas"
        />
      </div>

      {mensagemSucesso && (
        <AlertaStatus tipo="sucesso" role="status">
          {mensagemSucesso}
        </AlertaStatus>
      )}

      {erro && (
        <AlertaStatus tipo="erro" role="alert">
          {erro}
        </AlertaStatus>
      )}

      {/* Grid de Resumo */}
      <section className={styles.gridResumo} aria-label="Resumo dos valores">
        <div className={styles.cardResumo}>
          <span className={styles.rotuloResumo}>A Vencer no Mês</span>
          <strong className={`${styles.valorResumo} ${styles.destaqueAVencer}`}>
            {formatarMoeda(resumo.totalAVencer)}
          </strong>
        </div>

        <div className={styles.cardResumo}>
          <span className={styles.rotuloResumo}>Em Atraso</span>
          <strong className={`${styles.valorResumo} ${styles.destaqueAtraso}`}>
            {formatarMoeda(resumo.totalAtraso)}
          </strong>
        </div>

        <div className={styles.cardResumo}>
          <span className={styles.rotuloResumo}>Total Já Pago</span>
          <strong className={`${styles.valorResumo} ${styles.destaquePaga}`}>
            {formatarMoeda(resumo.totalPago)}
          </strong>
        </div>
      </section>

      {/* Formulário de Cadastro de Nova Conta (RF25) */}
      {modoCadastro ? (
        <section className={styles.painelCadastro} aria-labelledby="titulo-cadastro-conta">
          <h2
            id="titulo-cadastro-conta"
            style={{
              fontFamily: 'var(--font-titulo)',
              fontSize: '24px',
              fontWeight: 800,
              color: 'var(--violeta-profundo)',
              marginBottom: '16px',
            }}
          >
            Cadastrar Nova Conta a Pagar
          </h2>

          <div className={styles.formGrid}>
            <div>
              <label
                htmlFor="display-valor-conta"
                style={{
                  display: 'block',
                  fontSize: '16px',
                  fontWeight: 700,
                  marginBottom: '8px',
                  color: 'var(--ardosia)',
                }}
              >
                1. Digite o valor da conta:
              </label>
              <div
                id="display-valor-conta"
                className={styles.displayValorCadastro}
                aria-label={`Valor da conta: ${formatarMoeda(centavosAtuais / 100)}`}
              >
                {formatarMoeda(centavosAtuais / 100)}
              </div>
              <TecladoNumerico
                onDigito={handleDigito}
                onApagar={handleApagar}
                onLimpar={() => setValorDigitado('')}
              />
            </div>

            <div>
              <label
                htmlFor="data-vencimento"
                style={{
                  display: 'block',
                  fontSize: '16px',
                  fontWeight: 700,
                  marginBottom: '8px',
                  color: 'var(--ardosia)',
                }}
              >
                2. Data de vencimento:
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
              <CampoTexto
                rotulo="3. Nome da conta (opcional):"
                placeholder="Exemplo: Conta de Luz, Aluguel..."
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
              />
              <div className={styles.sugestoesRapidas} aria-label="Sugestões de nomes">
                {SUGESTOES_CONTAS.map((sugestao) => (
                  <button
                    key={sugestao}
                    type="button"
                    className={styles.btnSugestao}
                    onClick={() => setDescricao(sugestao)}
                  >
                    + {sugestao}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
              <Botao
                variant="primary"
                fullWidth
                disabled={centavosAtuais <= 0 || salvando}
                onClick={handleSalvarConta}
              >
                {salvando ? 'Salvando conta...' : 'Salvar Conta'}
              </Botao>
              <Botao
                variant="secondary"
                fullWidth
                disabled={salvando}
                onClick={() => {
                  setModoCadastro(false);
                  setValorDigitado('');
                  setDescricao('');
                }}
              >
                Cancelar
              </Botao>
            </div>
          </div>
        </section>
      ) : (
        /* Barra de Ações & Filtros */
        <div className={styles.barraControles}>
          <div className={styles.filtrosContainer} role="tablist" aria-label="Filtrar contas por situação">
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

      {/* Lista de Contas (RF32) */}
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
                ? 'Você ainda não cadastrou nenhuma conta a pagar.'
                : 'Não há contas nesta situação no momento.'}
            </p>
          </div>
        ) : (
          <div className={styles.listaContas}>
            {contasFiltradas.map((conta) => {
              const valorNum = Number(conta.valor);
              const dataObj = new Date(conta.vencimento_em + 'T12:00:00');
              const dataFormatada = dataObj.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
              });

              return (
                <div key={conta.id} className={styles.cardConta}>
                  <div className={styles.infoPrincipal}>
                    <div className={styles.iconeContainer} aria-hidden="true">
                      <IconBills size={26} />
                    </div>
                    <div className={styles.detalhesTexto}>
                      <span className={styles.nomeConta}>
                        {conta.descricao || 'Conta sem descrição'}
                      </span>
                      <span className={styles.dataVencimento}>
                        Vencimento: <strong>{dataFormatada}</strong>
                      </span>
                    </div>
                  </div>

                  <div className={styles.valoresEStatus}>
                    <strong className={styles.valorConta}>
                      {formatarMoeda(valorNum)}
                    </strong>

                    {/* Badge Triplo de Status WCAG (Cor + Ícone + Texto) */}
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
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};

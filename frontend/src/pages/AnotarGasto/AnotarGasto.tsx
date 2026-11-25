import React, { useState } from 'react';
import styles from './AnotarGasto.module.css';
import {
  BarraNavegacao,
  Botao,
  TecladoNumerico,
  SeletorCategoria,
  AlertaStatus,
  ConfirmacaoSucesso,
  LeitorQrCode,
  IconQrCode,
} from '../../components';
import { useNavegacao } from '../../router';
import { NovoLancamento, useDadosDoMes } from '../../servicos/dadosDoMes';
import { ErroApi } from '../../servicos/api';
import {
  parsearQrCodeNfce,
  parsearValorMonetario,
  sugerirCategoriaPorEstabelecimento,
} from '../../utils/nfce';
import { calcularHoje } from '../../servicos/dadosDoMes';

const NOMES_CATEGORIAS_ENTRADA: Record<string, string> = {
  salario: 'Salário / Renda',
  beneficio: 'Aposentadoria',
  extra: 'Trabalho extra',
  outros: 'Outro motivo',
};

export const AnotarGasto: React.FC = () => {
  const { navegar } = useNavegacao();
  const { adicionarLancamento, removerLancamento } = useDadosDoMes();
  const [tipo, setTipo] = useState<'gasto' | 'entrada'>('gasto');
  const [valorStr, setValorStr] = useState<string>(''); // dígitos em centavos
  const [categoriaGasto, setCategoriaGasto] = useState<string>('mercado');
  const [categoriaEntrada, setCategoriaEntrada] = useState<string>('salario');
  const [sucesso, setSucesso] = useState<boolean>(false);
  const [ultimoLancamentoId, setUltimoLancamentoId] = useState<string | null>(
    null
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [leitorAberto, setLeitorAberto] = useState<boolean>(false);
  const [nfcePendente, setNfcePendente] = useState<{
    estabelecimento: string;
    infoCnpj?: string;
    data: string;
    valorTexto: string;
    aviso?: string;
  } | null>(null);

  const hojeAtual = calcularHoje();
  const primeiroDiaMesAtual = `${hojeAtual.mes}-01`;
  const hojeIso = `${hojeAtual.mes}-${String(hojeAtual.dia).padStart(2, '0')}`;

  const centavos = valorStr ? parseInt(valorStr, 10) : 0;
  const valorFormatado = (centavos / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

  const digitar = (digito: string) => {
    if (valorStr.length < 8) {
      setValorStr((ant) => ant + digito);
      setErro(null);
    }
  };

  const apagar = () => {
    setValorStr((ant) => ant.slice(0, -1));
    setErro(null);
  };

  const limpar = () => {
    setValorStr('');
    setErro(null);
  };

  /** Grava na API. Só mostra "Tudo certo!" depois que o servidor confirmou. */
  const gravar = async (novo: NovoLancamento): Promise<boolean> => {
    if (salvando) return false;
    setSalvando(true);
    try {
      const salvo = await adicionarLancamento(novo);
      setUltimoLancamentoId(salvo.id);
      setErro(null);
      setSucesso(true);
      return true;
    } catch (e) {
      setErro(
        e instanceof ErroApi && e.status !== 0 && e.status < 500
          ? e.detalhe
          : 'Não foi possível salvar agora. Verifique a internet e tente de novo.'
      );
      return false;
    } finally {
      setSalvando(false);
    }
  };

  const salvar = async () => {
    if (centavos <= 0) {
      setErro(
        `Digite um valor maior que zero para ${tipo === 'gasto' ? 'o gasto' : 'a entrada'}.`
      );
      return;
    }

    await gravar(
      tipo === 'gasto'
        ? { tipo, centavos, categoriaCodigo: categoriaGasto }
        : {
            tipo,
            centavos,
            descricao: NOMES_CATEGORIAS_ENTRADA[categoriaEntrada],
          }
    );
  };

  const desfazer = async () => {
    if (ultimoLancamentoId) {
      try {
        await removerLancamento(ultimoLancamentoId);
        setUltimoLancamentoId(null);
      } catch {
        setErro(
          'Não foi possível desfazer agora. Apague o lançamento pelo Extrato.'
        );
      }
    }
    setSucesso(false);
  };

  const aoLerQrCode = (textoLido: string) => {
    setLeitorAberto(false);
    const dados = parsearQrCodeNfce(textoLido);
    if (!dados.valido) {
      setErro(
        dados.aviso ??
          'Esse QR Code não parece ser de uma nota fiscal. Você pode tentar outra foto ou digitar o valor abaixo.'
      );
      return;
    }

    const catSugerida = sugerirCategoriaPorEstabelecimento(
      dados.estabelecimento
    );
    setCategoriaGasto(catSugerida);
    setErro(null);

    const dataForaDoMes =
      dados.data < primeiroDiaMesAtual || dados.data > hojeIso;
    const avisoData = dataForaDoMes
      ? 'Atenção: a data desta nota não pertence ao mês atual até hoje. O Vero registra lançamentos apenas dentro do mês atual — ajuste a data abaixo se desejar lançar neste mês.'
      : undefined;

    const avisoCombinado = [dados.aviso, avisoData].filter(Boolean).join(' ');

    setNfcePendente({
      estabelecimento: dados.estabelecimento,
      infoCnpj:
        dados.uf && (dados.cnpj || dados.modelo === 'nfse')
          ? `${dados.modelo === 'nfse' ? 'Nota de serviço' : 'Nota'} identificada (${[
              dados.uf,
              dados.cnpj && `CNPJ ${dados.cnpj}`,
            ]
              .filter(Boolean)
              .join(' · ')})`
          : undefined,
      data: dados.data,
      valorTexto:
        dados.centavos !== null
          ? (dados.centavos / 100).toFixed(2).replace('.', ',')
          : '',
      aviso: avisoCombinado || undefined,
    });
  };

  const confirmarNfce = async () => {
    if (!nfcePendente) return;

    const centavosNfce = parsearValorMonetario(nfcePendente.valorTexto);
    if (!centavosNfce || centavosNfce <= 0) {
      setErro('Não entendi o valor. Digite o total da nota assim: 1.250,00.');
      return;
    }

    if (
      !nfcePendente.data ||
      nfcePendente.data < primeiroDiaMesAtual ||
      nfcePendente.data > hojeIso
    ) {
      setErro(
        'A data da nota precisa estar dentro do mês atual até hoje para entrar no saldo do mês.'
      );
      return;
    }

    setValorStr(String(centavosNfce));

    const salvou = await gravar({
      tipo: 'gasto',
      centavos: centavosNfce,
      categoriaCodigo: categoriaGasto,
      descricao: nfcePendente.estabelecimento.trim() || undefined,
      data: nfcePendente.data,
      origem: 'qrcode_nf',
    });
    if (salvou) setNfcePendente(null);
  };

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/anotar-gasto" />

      <main className={styles.conteudo}>
        <div className={styles.cardFormulario}>
          {/* Seletor de Tipo: Gasto ou Entrada */}
          <div
            className={styles.seletorTipo}
            role="group"
            aria-label="Tipo de movimentação"
          >
            <button
              type="button"
              className={`${styles.btnTipo} ${
                tipo === 'gasto' ? styles.btnTipoAtivoGasto : ''
              }`}
              onClick={() => {
                setTipo('gasto');
                setErro(null);
              }}
              aria-pressed={tipo === 'gasto'}
            >
              <span>− Saiu (Gasto)</span>
            </button>

            <button
              type="button"
              className={`${styles.btnTipo} ${
                tipo === 'entrada' ? styles.btnTipoAtivoEntrada : ''
              }`}
              onClick={() => {
                setTipo('entrada');
                setErro(null);
              }}
              aria-pressed={tipo === 'entrada'}
            >
              <span>+ Entrou dinheiro</span>
            </button>
          </div>

          <h1 className={styles.tituloTela}>
            {nfcePendente
              ? 'Confira os dados da nota fiscal'
              : tipo === 'gasto'
                ? 'Anotar novo gasto'
                : 'Anotar recebimento'}
          </h1>
          <p className={styles.subtituloTela}>
            {nfcePendente
              ? 'Veja se as informações lidas estão certas antes de salvar:'
              : tipo === 'gasto'
                ? 'Leia o QR Code da nota ou digite o valor usando o teclado:'
                : 'Digite o valor recebido que entrou na sua conta:'}
          </p>

          {erro && (
            <div style={{ marginBottom: 16 }}>
              <AlertaStatus tipo="erro">{erro}</AlertaStatus>
            </div>
          )}

          {nfcePendente ? (
            <div className={styles.painelConfirmacaoNfce}>
              {nfcePendente.aviso && (
                <AlertaStatus tipo="aviso">{nfcePendente.aviso}</AlertaStatus>
              )}

              <div className={styles.campoNfceGrupo}>
                <label
                  htmlFor="nfce-estabelecimento"
                  className={styles.rotuloNfce}
                >
                  Nome do estabelecimento (opcional)
                </label>
                <input
                  id="nfce-estabelecimento"
                  type="text"
                  className={styles.inputNfce}
                  value={nfcePendente.estabelecimento}
                  onChange={(e) =>
                    setNfcePendente({
                      ...nfcePendente,
                      estabelecimento: e.target.value,
                    })
                  }
                  placeholder="Ex: Supermercado, Farmácia"
                />
                {nfcePendente.infoCnpj && (
                  <span style={{ fontSize: 14, color: 'var(--ardosia)' }}>
                    {nfcePendente.infoCnpj}
                  </span>
                )}
              </div>

              <div className={styles.campoNfceGrupo}>
                <label htmlFor="nfce-data" className={styles.rotuloNfce}>
                  Data da compra
                </label>
                <input
                  id="nfce-data"
                  type="date"
                  min={primeiroDiaMesAtual}
                  max={hojeIso}
                  className={styles.inputNfce}
                  value={nfcePendente.data}
                  onChange={(e) => {
                    setErro(null);
                    setNfcePendente({
                      ...nfcePendente,
                      data: e.target.value,
                    });
                  }}
                />
              </div>

              <div className={styles.campoNfceGrupo}>
                <label htmlFor="nfce-valor" className={styles.rotuloNfce}>
                  Valor total da nota (R$)
                </label>
                <input
                  id="nfce-valor"
                  type="text"
                  inputMode="decimal"
                  className={`${styles.inputNfce} ${styles.inputValorNfce}`}
                  value={nfcePendente.valorTexto}
                  onChange={(e) =>
                    setNfcePendente({
                      ...nfcePendente,
                      valorTexto: e.target.value,
                    })
                  }
                  placeholder="Ex: 85,50"
                />
              </div>

              <div>
                <h2 className={styles.subtituloCategoria}>
                  Escolha a categoria:
                </h2>
                <SeletorCategoria
                  categoriaSelecionada={categoriaGasto}
                  onSelecionar={(id) => setCategoriaGasto(id)}
                />
              </div>

              <div className={styles.acoes}>
                <Botao
                  variant="primary"
                  fullWidth
                  disabled={salvando}
                  onClick={confirmarNfce}
                >
                  {salvando ? 'Salvando…' : 'Confirmar e salvar gasto'}
                </Botao>
                <button
                  type="button"
                  className={styles.btnCancelar}
                  onClick={() => {
                    setNfcePendente(null);
                    setErro(null);
                  }}
                >
                  Voltar para digitação manual
                </button>
              </div>
            </div>
          ) : (
            <>
              {tipo === 'gasto' && (
                <button
                  type="button"
                  className={styles.btnQrCode}
                  onClick={() => {
                    setErro(null);
                    setLeitorAberto(true);
                  }}
                >
                  <IconQrCode size={24} />
                  <span>Ler QR Code da nota fiscal</span>
                </button>
              )}

              {/* Display monetário */}
              <div
                className={styles.displayMonetario}
                aria-label={`Valor ${tipo === 'gasto' ? 'do gasto' : 'da entrada'}: ${valorFormatado}`}
                role="region"
                style={{
                  borderColor:
                    tipo === 'gasto' ? 'var(--violeta-vero)' : '#10B981',
                }}
              >
                {tipo === 'entrada' && '+ '}
                {valorFormatado}
              </div>

              {/* Teclado numérico com suporte ativo a teclado físico */}
              <TecladoNumerico
                onDigito={digitar}
                onApagar={apagar}
                onLimpar={limpar}
                capturarTeclado={!leitorAberto && !nfcePendente}
              />

              {tipo === 'gasto' ? (
                <>
                  <h2 className={styles.subtituloCategoria}>
                    Escolha a categoria:
                  </h2>
                  <SeletorCategoria
                    categoriaSelecionada={categoriaGasto}
                    onSelecionar={(id) => setCategoriaGasto(id)}
                  />
                </>
              ) : (
                <>
                  <h2 className={styles.subtituloCategoria}>
                    De onde veio esse dinheiro?
                  </h2>
                  <div
                    className={styles.gradeCategoriasEntrada}
                    role="group"
                    aria-label="Categorias de entrada"
                  >
                    {[
                      { id: 'salario', rotulo: 'Salário / Renda' },
                      { id: 'beneficio', rotulo: 'Aposentadoria' },
                      { id: 'extra', rotulo: 'Trabalho extra' },
                      { id: 'outros', rotulo: 'Outro motivo' },
                    ].map((cat) => (
                      <button
                        key={cat.id}
                        type="button"
                        className={`${styles.btnCategoriaEntrada} ${
                          categoriaEntrada === cat.id
                            ? styles.btnCategoriaEntradaAtiva
                            : ''
                        }`}
                        onClick={() => setCategoriaEntrada(cat.id)}
                        aria-pressed={categoriaEntrada === cat.id}
                      >
                        {cat.rotulo}
                      </button>
                    ))}
                  </div>
                </>
              )}

              <div className={styles.acoes}>
                <Botao
                  variant="primary"
                  fullWidth
                  disabled={centavos <= 0 || salvando}
                  onClick={salvar}
                >
                  {salvando
                    ? 'Salvando…'
                    : tipo === 'gasto'
                      ? 'Salvar gasto'
                      : 'Salvar recebimento'}
                </Botao>

                <button
                  type="button"
                  className={styles.btnCancelar}
                  onClick={() => navegar('/inicio')}
                >
                  Cancelar
                </button>
              </div>
            </>
          )}
        </div>
      </main>

      {leitorAberto && (
        <LeitorQrCode
          aoLerCodigo={aoLerQrCode}
          aoFechar={() => setLeitorAberto(false)}
        />
      )}

      {/* Modal Acessível de Confirmação com Opção de Desfazer */}
      <ConfirmacaoSucesso
        aberta={sucesso}
        mensagem={`${tipo === 'gasto' ? 'Gasto' : 'Recebimento'} de ${valorFormatado} registrado com sucesso no Vero.`}
        onIrParaInicio={() => navegar('/inicio')}
        onDesfazer={desfazer}
        onContinuar={() => {
          setSucesso(false);
          setValorStr('');
          setUltimoLancamentoId(null);
        }}
        textoContinuar={`Anotar outr${tipo === 'gasto' ? 'o gasto' : 'o recebimento'}`}
      />
    </div>
  );
};

import React, { useState } from 'react';
import styles from './AnotarGasto.module.css';
import {
  BarraNavegacao,
  Botao,
  TecladoNumerico,
  SeletorCategoria,
  AlertaStatus,
  ConfirmacaoSucesso,
} from '../../components';
import { useNavegacao } from '../../router';
import { useDadosDoMes } from '../../servicos/dadosDoMes';

const NOMES_CATEGORIAS_GASTO: Record<string, string> = {
  mercado: 'Mercado',
  farmacia: 'Farmácia',
  contas: 'Contas',
  transporte: 'Transporte',
  casa: 'Casa',
  outros: 'Outros',
};

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
  const [ultimoLancamentoId, setUltimoLancamentoId] = useState<number | null>(
    null
  );
  const [erro, setErro] = useState<string | null>(null);

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

  const salvar = () => {
    if (centavos <= 0) {
      setErro(
        `Digite um valor maior que zero para ${tipo === 'gasto' ? 'o gasto' : 'a entrada'}.`
      );
      return;
    }

    const nomeCat =
      tipo === 'gasto'
        ? NOMES_CATEGORIAS_GASTO[categoriaGasto] || 'Gasto Geral'
        : NOMES_CATEGORIAS_ENTRADA[categoriaEntrada] || 'Entrada Geral';

    const id = adicionarLancamento(tipo, centavos, nomeCat);
    setUltimoLancamentoId(id);

    setSucesso(true);
    setErro(null);
  };

  const desfazer = () => {
    if (ultimoLancamentoId) {
      removerLancamento(ultimoLancamentoId);
      setUltimoLancamentoId(null);
    }
    setSucesso(false);
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
            {tipo === 'gasto' ? 'Anotar novo gasto' : 'Anotar recebimento'}
          </h1>
          <p className={styles.subtituloTela}>
            {tipo === 'gasto'
              ? 'Digite o valor do gasto usando o teclado:'
              : 'Digite o valor recebido que entrou na sua conta:'}
          </p>

          {erro && (
            <div style={{ marginBottom: 16 }}>
              <AlertaStatus tipo="erro">{erro}</AlertaStatus>
            </div>
          )}

          {/* Display monetário */}
          <div
            className={styles.displayMonetario}
            aria-label={`Valor ${tipo === 'gasto' ? 'do gasto' : 'da entrada'}: ${valorFormatado}`}
            role="region"
            style={{
              borderColor: tipo === 'gasto' ? 'var(--violeta-vero)' : '#10B981',
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
            capturarTeclado={true}
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
              disabled={centavos <= 0}
              onClick={salvar}
            >
              {tipo === 'gasto' ? 'Salvar gasto' : 'Salvar recebimento'}
            </Botao>

            <button
              type="button"
              className={styles.btnCancelar}
              onClick={() => navegar('/inicio')}
            >
              Cancelar
            </button>
          </div>
        </div>
      </main>

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

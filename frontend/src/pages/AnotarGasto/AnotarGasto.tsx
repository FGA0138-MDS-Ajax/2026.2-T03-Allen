import React, { useState } from 'react';
import styles from './AnotarGasto.module.css';
import {
  BarraNavegacao,
  Botao,
  TecladoNumerico,
  SeletorCategoria,
  AlertaStatus,
  IconCheck,
} from '../../components';
import { useNavegacao } from '../../router';
import { useDadosDoMes } from '../../servicos/dadosDoMes';

const NOMES_CATEGORIAS: Record<string, string> = {
  mercado: 'Mercado',
  farmacia: 'Farmácia',
  contas: 'Contas',
  transporte: 'Transporte',
  casa: 'Casa',
  outros: 'Outros',
};

export const AnotarGasto: React.FC = () => {
  const { navegar } = useNavegacao();
  const { adicionarLancamento } = useDadosDoMes();
  const [valorStr, setValorStr] = useState<string>(''); // dígitos em centavos
  const [categoria, setCategoria] = useState<string>('mercado');
  const [sucesso, setSucesso] = useState<boolean>(false);
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

  const salvarGasto = () => {
    if (centavos <= 0) {
      setErro('Digite um valor maior que zero para o gasto.');
      return;
    }

    const nomeCat = NOMES_CATEGORIAS[categoria] || 'Gasto Geral';
    adicionarLancamento('gasto', centavos, nomeCat);

    setSucesso(true);
    setErro(null);
  };

  return (
    <div className={styles.pageContainer}>
      <BarraNavegacao rotaAtiva="/anotar-gasto" />

      <main className={styles.conteudo}>
        <div className={styles.cardFormulario}>
          <h1 className={styles.tituloTela}>Anotar novo gasto</h1>
          <p className={styles.subtituloTela}>
            Digite o valor usando o teclado físico do computador ou o teclado na tela:
          </p>

          {erro && (
            <div style={{ marginBottom: 16 }}>
              <AlertaStatus tipo="erro">{erro}</AlertaStatus>
            </div>
          )}

          {sucesso ? (
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{ marginBottom: 16 }}>
                <AlertaStatus tipo="sucesso">
                  Gasto de {valorFormatado} registrado com sucesso no Vero!
                </AlertaStatus>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 24 }}>
                <Botao
                  variant="primary"
                  fullWidth
                  onClick={() => {
                    setSucesso(false);
                    setValorStr('');
                  }}
                >
                  <IconCheck size={20} />
                  <span>Anotar outro gasto</span>
                </Botao>

                <button
                  type="button"
                  className={styles.btnCancelar}
                  onClick={() => navegar('/inicio')}
                >
                  Voltar para o início
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Display monetário */}
              <div
                className={styles.displayMonetario}
                aria-label={`Valor do gasto: ${valorFormatado}`}
                role="region"
              >
                {valorFormatado}
              </div>

              {/* Teclado numérico com suporte ativo a teclado físico */}
              <TecladoNumerico
                onDigito={digitar}
                onApagar={apagar}
                onLimpar={limpar}
                capturarTeclado={true}
              />

              <h2 className={styles.subtituloCategoria}>Escolha a categoria:</h2>
              <SeletorCategoria
                categoriaSelecionada={categoria}
                onSelecionar={(id) => setCategoria(id)}
              />

              <div className={styles.acoes}>
                <Botao
                  variant="primary"
                  fullWidth
                  disabled={centavos <= 0}
                  onClick={salvarGasto}
                >
                  Salvar gasto
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
    </div>
  );
};

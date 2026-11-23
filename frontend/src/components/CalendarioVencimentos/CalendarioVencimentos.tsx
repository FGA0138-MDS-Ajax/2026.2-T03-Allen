import React, { useMemo, useState } from 'react';
import { ContaSaida, StatusConta } from '../../servicos';
import {
  IconAlert,
  IconArrowLeft,
  IconCheck,
  IconClock,
} from '../Icones/Icones';
import styles from './CalendarioVencimentos.module.css';

export interface CalendarioVencimentosProps {
  contas: ContaSaida[];
  diaSelecionado: string | null;
  aoSelecionarDia: (dataIso: string | null) => void;
  mesInicial?: string; // AAAA-MM
}

const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

const obterMesAtual = (): { ano: number; mes: number } => {
  const agora = new Date();
  return { ano: agora.getFullYear(), mes: agora.getMonth() };
};

const parsearMesInicial = (
  mesInicial?: string
): { ano: number; mes: number } => {
  if (!mesInicial || !/^\d{4}-\d{2}$/.test(mesInicial)) {
    return obterMesAtual();
  }
  const [anoStr, mesStr] = mesInicial.split('-');
  return { ano: Number(anoStr), mes: Number(mesStr) - 1 };
};

const formatarChaveMes = (ano: number, mes: number): string =>
  `${ano}-${String(mes + 1).padStart(2, '0')}`;

const formatarDataPorExtenso = (dataIso: string): string => {
  const data = new Date(`${dataIso}T12:00:00`);
  return data.toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
};

const descreverContasDoDia = (contasDia: ContaSaida[]): string => {
  if (contasDia.length === 0) return 'sem contas';
  const partes: string[] = [];
  const atraso = contasDia.filter((c) => c.status === 'em_atraso').length;
  const vencer = contasDia.filter((c) => c.status === 'a_vencer').length;
  const pagas = contasDia.filter((c) => c.status === 'paga').length;
  if (atraso) partes.push(`${atraso} em atraso`);
  if (vencer) partes.push(`${vencer} a vencer`);
  if (pagas) partes.push(`${pagas} ${pagas === 1 ? 'paga' : 'pagas'}`);
  return partes.join(', ');
};

export const CalendarioVencimentos: React.FC<CalendarioVencimentosProps> = ({
  contas,
  diaSelecionado,
  aoSelecionarDia,
  mesInicial,
}) => {
  const [mesAtual, setMesAtual] = useState(() => parsearMesInicial(mesInicial));

  const chaveMes = formatarChaveMes(mesAtual.ano, mesAtual.mes);

  const nomeMesAno = useMemo(() => {
    const dataRef = new Date(mesAtual.ano, mesAtual.mes, 1, 12);
    const texto = dataRef.toLocaleDateString('pt-BR', {
      month: 'long',
      year: 'numeric',
    });
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }, [mesAtual]);

  const contasPorDia = useMemo(() => {
    const mapa: Record<string, ContaSaida[]> = {};
    for (const conta of contas) {
      if (!conta.vencimento_em.startsWith(chaveMes)) continue;
      if (!mapa[conta.vencimento_em]) mapa[conta.vencimento_em] = [];
      mapa[conta.vencimento_em].push(conta);
    }
    return mapa;
  }, [contas, chaveMes]);

  const celulas = useMemo(() => {
    const primeiroDiaSemana = new Date(mesAtual.ano, mesAtual.mes, 1).getDay();
    const totalDias = new Date(mesAtual.ano, mesAtual.mes + 1, 0).getDate();
    const itens: Array<{ dia: number | null; dataIso: string | null }> = [];

    for (let i = 0; i < primeiroDiaSemana; i++) {
      itens.push({ dia: null, dataIso: null });
    }
    for (let d = 1; d <= totalDias; d++) {
      const dataIso = `${chaveMes}-${String(d).padStart(2, '0')}`;
      itens.push({ dia: d, dataIso });
    }
    return itens;
  }, [mesAtual, chaveMes]);

  const mudarMes = (delta: number) => {
    setMesAtual((ant) => {
      const nova = new Date(ant.ano, ant.mes + delta, 1);
      return { ano: nova.getFullYear(), mes: nova.getMonth() };
    });
  };

  const estadosDoDia = (contasDia: ContaSaida[]): StatusConta[] => {
    const ordem: StatusConta[] = ['em_atraso', 'a_vencer', 'paga'];
    return ordem.filter((st) => contasDia.some((c) => c.status === st));
  };

  return (
    <section
      className={styles.container}
      aria-label={`Calendário de vencimentos de ${nomeMesAno}`}
    >
      <div className={styles.cabecalho}>
        <button
          type="button"
          className={styles.btnMes}
          onClick={() => mudarMes(-1)}
          aria-label="Mês anterior"
        >
          <IconArrowLeft size={18} aria-hidden="true" />
          <span>Anterior</span>
        </button>

        <h2 className={styles.tituloMes}>{nomeMesAno}</h2>

        <button
          type="button"
          className={styles.btnMes}
          onClick={() => mudarMes(1)}
          aria-label="Próximo mês"
        >
          <span>Próximo</span>
          <span aria-hidden="true" style={{ fontSize: 18, lineHeight: 1 }}>
            ›
          </span>
        </button>
      </div>

      <div className={styles.legenda} aria-label="Legenda dos ícones">
        <span className={`${styles.itemLegenda} ${styles.legendaAVencer}`}>
          <IconClock size={16} aria-hidden="true" />
          <span>A vencer</span>
        </span>
        <span className={`${styles.itemLegenda} ${styles.legendaEmAtraso}`}>
          <IconAlert size={16} aria-hidden="true" />
          <span>Em atraso</span>
        </span>
        <span className={`${styles.itemLegenda} ${styles.legendaPaga}`}>
          <IconCheck size={16} aria-hidden="true" />
          <span>Paga</span>
        </span>
      </div>

      <div className={styles.diasSemana} aria-hidden="true">
        {DIAS_SEMANA.map((dia) => (
          <div key={dia} className={styles.nomeDiaSemana}>
            {dia}
          </div>
        ))}
      </div>

      <div
        className={styles.gradeDias}
        role="group"
        aria-label={`Dias de ${nomeMesAno}`}
      >
        {celulas.map((celula, idx) => {
          if (celula.dia === null || celula.dataIso === null) {
            return (
              <div
                key={`vazio-${idx}`}
                className={styles.celulaVazia}
                aria-hidden="true"
              />
            );
          }

          const dataIso = celula.dataIso;
          const contasDia = contasPorDia[dataIso] || [];
          const estados = estadosDoDia(contasDia);
          const selecionado = diaSelecionado === dataIso;
          const labelDia = `${formatarDataPorExtenso(dataIso)}: ${descreverContasDoDia(contasDia)}`;

          return (
            <button
              key={dataIso}
              type="button"
              className={`${styles.btnDia} ${contasDia.length > 0 ? styles.btnDiaComConta : ''} ${selecionado ? styles.btnDiaSelecionado : ''}`}
              aria-label={labelDia}
              aria-pressed={selecionado}
              onClick={() => aoSelecionarDia(selecionado ? null : dataIso)}
            >
              <span className={styles.numeroDia}>{celula.dia}</span>

              {estados.length > 0 && (
                <span className={styles.marcadores} aria-hidden="true">
                  {estados.map((st) => {
                    if (st === 'em_atraso') {
                      return (
                        <span
                          key={st}
                          className={`${styles.marcador} ${styles.marcadorAtraso}`}
                        >
                          <IconAlert size={14} />
                        </span>
                      );
                    }
                    if (st === 'a_vencer') {
                      return (
                        <span
                          key={st}
                          className={`${styles.marcador} ${styles.marcadorAVencer}`}
                        >
                          <IconClock size={14} />
                        </span>
                      );
                    }
                    return (
                      <span
                        key={st}
                        className={`${styles.marcador} ${styles.marcadorPaga}`}
                      >
                        <IconCheck size={14} />
                      </span>
                    );
                  })}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
};

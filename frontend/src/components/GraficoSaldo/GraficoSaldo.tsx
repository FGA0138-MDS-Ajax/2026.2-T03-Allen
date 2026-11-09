import React, { useEffect, useRef, useState } from 'react';
import styles from './GraficoSaldo.module.css';
import {
  PASSO_ESCALA,
  escalaDoGrafico,
  puloDosRotulos,
  PontoSaldo,
} from '../../servicos/dadosDoMes';

export interface GraficoSaldoProps {
  pontos: PontoSaldo[];
  meta: number; // em centavos
  diasNoMes: number;
}

const ALTURA = 320;
const MARGEM = { topo: 20, dir: 24, base: 36, esq: 84 };

function formatarMoeda(centavos: number): string {
  return (centavos / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

function rotuloReaisAbreviado(centavos: number): string {
  return `R$ ${(centavos / 100).toLocaleString('pt-BR')}`;
}

export const GraficoSaldo: React.FC<GraficoSaldoProps> = ({
  pontos,
  meta,
  diasNoMes,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [largura, setLargura] = useState(0);
  const [diaEmFoco, setDiaEmFoco] = useState<number | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observador = new ResizeObserver(([entrada]) => {
      setLargura(entrada.contentRect.width);
    });
    observador.observe(el);
    return () => observador.disconnect();
  }, []);

  const w = Math.max(0, largura - MARGEM.esq - MARGEM.dir);
  const h = ALTURA - MARGEM.topo - MARGEM.base;
  const valores = [...pontos.map((p) => p.saldo), meta];
  const { minimo, maximo, passos } = escalaDoGrafico(valores);
  const pulo = puloDosRotulos(h, passos);

  const calcularX = (dia: number) =>
    MARGEM.esq + (diasNoMes <= 1 ? 0 : ((dia - 1) / (diasNoMes - 1)) * w);

  const calcularY = (valor: number) =>
    MARGEM.topo + ((maximo - valor) / Math.max(1, maximo - minimo)) * h;

  // Marcas nos dias 1, 5, 10, 15, 20, 25 e fim do mês
  const marcasDias: number[] = [];
  let ultimoX = -Infinity;
  for (const dia of [1, 5, 10, 15, 20, 25, diasNoMes]) {
    if (marcasDias.includes(dia) || (dia !== diasNoMes && diasNoMes - dia < 3))
      continue;
    if (dia !== 1 && calcularX(dia) - ultimoX < 40) continue;
    marcasDias.push(dia);
    ultimoX = calcularX(dia) + (dia === 1 ? 20 : 0);
  }

  const ultimoPonto = pontos[pontos.length - 1] || { dia: 1, saldo: 0 };
  const pontoEmFoco =
    diaEmFoco === null ? undefined : pontos.find((p) => p.dia === diaEmFoco);

  const aoMoverPonteiro = (evento: React.PointerEvent<SVGRectElement>) => {
    const elSvg = evento.currentTarget.ownerSVGElement;
    if (!elSvg || w === 0) return;
    const rect = elSvg.getBoundingClientRect();
    const px = evento.clientX - rect.left;
    const dia = Math.round(((px - MARGEM.esq) / w) * (diasNoMes - 1)) + 1;
    setDiaEmFoco(Math.max(1, Math.min(diasNoMes, dia)));
  };

  const larguraDica = 190;
  const dicaADireita =
    diaEmFoco !== null && calcularX(diaEmFoco) + 12 + larguraDica <= largura;

  return (
    <div className={styles.container}>
      <div className={styles.legendas}>
        <span className={styles.itemLegenda}>
          <span className={styles.tracoSaldo} aria-hidden="true" />
          <span>Saldo disponível</span>
        </span>
        <span className={styles.itemLegenda}>
          <span className={styles.tracoMeta} aria-hidden="true" />
          <span>Meta de saldo</span>
        </span>
      </div>

      <div
        ref={containerRef}
        role="img"
        aria-label="Gráfico de linha comparando o saldo disponível dia a dia com a meta do mês"
        className={styles.areaGrafico}
      >
        {largura > 0 && (
          <svg
            width={largura}
            height={ALTURA}
            aria-hidden="true"
            style={{ display: 'block' }}
          >
            {/* Linhas de grade e rótulos de valores */}
            {Array.from({ length: passos + 1 }, (_, i) => {
              const valor = minimo + i * PASSO_ESCALA;
              const comRotulo = i % pulo === 0;
              const yLinha = calcularY(valor);
              return (
                <g key={valor}>
                  <line
                    x1={MARGEM.esq}
                    x2={MARGEM.esq + w}
                    y1={yLinha}
                    y2={yLinha}
                    stroke={comRotulo ? '#E9E4F8' : '#F3F0FB'}
                    strokeWidth={1}
                  />
                  {comRotulo && (
                    <text
                      x={MARGEM.esq - 10}
                      y={yLinha}
                      textAnchor="end"
                      dominantBaseline="middle"
                      fill="#4B4B63"
                      fontSize={14}
                      fontWeight={600}
                    >
                      {rotuloReaisAbreviado(valor)}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Marcas de dias no eixo X */}
            {marcasDias.map((dia) => (
              <text
                key={dia}
                x={calcularX(dia)}
                y={ALTURA - 10}
                textAnchor={dia === 1 ? 'start' : 'middle'}
                fill="#4B4B63"
                fontSize={13}
                fontWeight={600}
              >
                {dia === 1 ? 'Dia 1' : `Dia ${dia}`}
              </text>
            ))}

            {/* Linha tracejada da meta */}
            <line
              x1={calcularX(1)}
              x2={calcularX(diasNoMes)}
              y1={calcularY(meta)}
              y2={calcularY(meta)}
              stroke="#3B82F6"
              strokeWidth={2.5}
              strokeDasharray="8 6"
              strokeLinecap="round"
            />
            <text
              x={calcularX(diasNoMes)}
              y={calcularY(meta) - 8}
              textAnchor="end"
              fill="#1D4ED8"
              fontSize={14}
              fontWeight={700}
            >
              Meta: {rotuloReaisAbreviado(meta)}
            </text>

            {/* Linha violeta do saldo diário */}
            {pontos.length > 0 && (
              <path
                d={pontos
                  .map(
                    (p, i) =>
                      `${i === 0 ? 'M' : 'L'}${calcularX(p.dia)},${calcularY(
                        p.saldo
                      )}`
                  )
                  .join(' ')}
                fill="none"
                stroke="#7C3AED"
                strokeWidth={3}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}

            {/* Círculo do último saldo registrado */}
            {pontos.length > 0 && (
              <>
                <circle
                  cx={calcularX(ultimoPonto.dia)}
                  cy={calcularY(ultimoPonto.saldo)}
                  r={6}
                  fill="#7C3AED"
                  stroke="#FFFFFF"
                  strokeWidth={2}
                />
                <text
                  x={calcularX(ultimoPonto.dia)}
                  y={calcularY(ultimoPonto.saldo) - 12}
                  textAnchor="middle"
                  fill="#1A1A2E"
                  fontSize={14}
                  fontWeight={800}
                >
                  {formatarMoeda(ultimoPonto.saldo)}
                </text>
              </>
            )}

            {/* Linha vertical de foco ao passar ponteiro */}
            {diaEmFoco !== null && (
              <>
                <line
                  x1={calcularX(diaEmFoco)}
                  x2={calcularX(diaEmFoco)}
                  y1={MARGEM.topo}
                  y2={MARGEM.topo + h}
                  stroke="#7C3AED"
                  strokeDasharray="3 3"
                  strokeWidth={1.5}
                />
                {pontoEmFoco && (
                  <circle
                    cx={calcularX(diaEmFoco)}
                    cy={calcularY(pontoEmFoco.saldo)}
                    r={5}
                    fill="#7C3AED"
                    stroke="#FFFFFF"
                    strokeWidth={2}
                  />
                )}
              </>
            )}

            {/* Retângulo transparente para captura de eventos de mouse/ponteiro */}
            <rect
              x={MARGEM.esq}
              y={MARGEM.topo}
              width={w}
              height={h}
              fill="transparent"
              onPointerMove={aoMoverPonteiro}
              onPointerDown={aoMoverPonteiro}
              onPointerLeave={() => setDiaEmFoco(null)}
            />
          </svg>
        )}

        {diaEmFoco !== null && (
          <div
            className={styles.dicaFlutuante}
            style={{
              top: MARGEM.topo,
              left: dicaADireita
                ? calcularX(diaEmFoco) + 12
                : Math.max(0, calcularX(diaEmFoco) - larguraDica - 12),
            }}
          >
            <strong>Dia {diaEmFoco}</strong>
            {pontoEmFoco && (
              <span>Saldo: {formatarMoeda(pontoEmFoco.saldo)}</span>
            )}
            <span>Meta: {formatarMoeda(meta)}</span>
          </div>
        )}
      </div>

      <details className={styles.detalhesTabela}>
        <summary className={styles.sumarioTabela}>
          Ver valores do gráfico em tabela acessível
        </summary>
        <table className={styles.tabela}>
          <thead>
            <tr>
              <th scope="col" className={styles.th}>
                Dia
              </th>
              <th scope="col" className={styles.th}>
                Saldo
              </th>
              <th scope="col" className={styles.th}>
                Meta
              </th>
            </tr>
          </thead>
          <tbody>
            {pontos.map((p) => (
              <tr key={p.dia}>
                <td className={styles.td}>Dia {p.dia}</td>
                <td className={styles.td}>{formatarMoeda(p.saldo)}</td>
                <td className={styles.td}>{formatarMoeda(meta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
};

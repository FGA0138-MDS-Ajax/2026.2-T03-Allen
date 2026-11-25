/**
 * Regras de data do vencimento de contas (#120 e #121), iguais às da API.
 */

export const MESES = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
] as const;

const doisDigitos = (n: number) => String(n).padStart(2, '0');

/** Data local (não UTC) no formato YYYY-MM-DD. */
export function paraIso(data: Date): string {
  return `${data.getFullYear()}-${doisDigitos(data.getMonth() + 1)}-${doisDigitos(data.getDate())}`;
}

/** "2026-10-01" -> "01/10/2026" */
export function isoParaBr(iso: string): string {
  const [ano, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${ano}`;
}

const diasNoMes = (ano: number, mes: number) => new Date(ano, mes, 0).getDate();

/**
 * Vencimento mais antigo aceito: dia 1º do mês anterior. A conta atrasada do mês
 * passado ainda entra; uma data de anos atrás é erro de toque no seletor (#121).
 */
export function vencimentoMinimo(hoje: Date = new Date()): string {
  return paraIso(new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1));
}

export function mensagemVencimentoAntigo(hoje: Date = new Date()): string {
  return `Essa data de vencimento já passou faz tempo. Use uma data a partir de ${isoParaBr(
    vencimentoMinimo(hoje)
  )}.`;
}

/**
 * Conta fixa (#120): a pessoa escolhe só dia e mês; o ano é o da primeira data
 * possível a partir do vencimento mínimo. Assim, em 23/11/2026, "10 de novembro"
 * é a conta deste mês (em atraso) e "5 de setembro" é setembro de 2027.
 * Dia que não existe no mês vira o último dia (31 de fevereiro -> 28 ou 29).
 */
export function vencimentoPorDiaEMes(
  dia: number,
  mes: number,
  hoje: Date = new Date()
): string {
  const minimo = vencimentoMinimo(hoje);
  for (const ano of [
    hoje.getFullYear() - 1,
    hoje.getFullYear(),
    hoje.getFullYear() + 1,
  ]) {
    const data = paraIso(
      new Date(ano, mes - 1, Math.min(dia, diasNoMes(ano, mes)))
    );
    if (data >= minimo) return data;
  }
  // Não chega aqui: dentro de 3 anos sempre há uma data válida
  return minimo;
}

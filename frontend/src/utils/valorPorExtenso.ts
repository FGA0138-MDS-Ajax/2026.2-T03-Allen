/**
 * Valores em reais escritos por extenso, para leitura em voz alta (RF21 / #101).
 * "R$ 1.250,00" vira "mil duzentos e cinquenta reais": assim a fala não depende
 * de a voz do aparelho saber ler o símbolo e os separadores.
 */

const UNIDADES = [
  'zero',
  'um',
  'dois',
  'três',
  'quatro',
  'cinco',
  'seis',
  'sete',
  'oito',
  'nove',
  'dez',
  'onze',
  'doze',
  'treze',
  'quatorze',
  'quinze',
  'dezesseis',
  'dezessete',
  'dezoito',
  'dezenove',
];

const DEZENAS = [
  '',
  '',
  'vinte',
  'trinta',
  'quarenta',
  'cinquenta',
  'sessenta',
  'setenta',
  'oitenta',
  'noventa',
];

const CENTENAS = [
  '',
  'cento',
  'duzentos',
  'trezentos',
  'quatrocentos',
  'quinhentos',
  'seiscentos',
  'setecentos',
  'oitocentos',
  'novecentos',
];

/** 1 a 999 por extenso. */
const ateMil = (n: number): string => {
  if (n === 100) return 'cem';
  const partes: string[] = [];
  const c = Math.floor(n / 100);
  const resto = n % 100;
  if (c) partes.push(CENTENAS[c]);
  if (resto) {
    if (resto < 20) partes.push(UNIDADES[resto]);
    else {
      const d = Math.floor(resto / 10);
      const u = resto % 10;
      partes.push(u ? `${DEZENAS[d]} e ${UNIDADES[u]}` : DEZENAS[d]);
    }
  }
  return partes.join(' e ');
};

const ESCALAS: [singular: string, plural: string][] = [
  ['', ''],
  ['mil', 'mil'],
  ['milhão', 'milhões'],
  ['bilhão', 'bilhões'],
];

/** Número inteiro não negativo por extenso ("mil duzentos e cinquenta"). */
export const inteiroPorExtenso = (valor: number): string => {
  const n = Math.floor(Math.abs(valor));
  if (n === 0) return 'zero';

  const grupos: number[] = [];
  for (let resto = n; resto > 0; resto = Math.floor(resto / 1000)) {
    grupos.push(resto % 1000);
  }

  const pedacos: { texto: string; grupo: number }[] = [];
  for (let i = grupos.length - 1; i >= 0; i--) {
    const g = grupos[i];
    if (!g) continue;
    const [singular, plural] = ESCALAS[i] ?? ESCALAS[ESCALAS.length - 1];
    let texto: string;
    if (i === 0) texto = ateMil(g);
    else if (i === 1) texto = g === 1 ? 'mil' : `${ateMil(g)} mil`;
    else texto = `${ateMil(g)} ${g === 1 ? singular : plural}`;
    pedacos.push({ texto, grupo: g });
  }

  // "mil e duzentos", "mil e cinquenta", mas "mil duzentos e cinquenta"
  return pedacos
    .map(({ texto, grupo }, i) => {
      if (i === 0) return texto;
      const ultimo = i === pedacos.length - 1;
      const usaE = ultimo && (grupo < 100 || grupo % 100 === 0);
      return `${usaE ? 'e ' : ''}${texto}`;
    })
    .join(' ');
};

/** Centavos em reais por extenso: 125000 → "mil duzentos e cinquenta reais". */
export const reaisPorExtenso = (centavos: number): string => {
  const total = Number.isFinite(centavos) ? Math.round(centavos) : 0;
  const negativo = total < 0;
  const absoluto = Math.abs(total);
  const reais = Math.floor(absoluto / 100);
  const cents = absoluto % 100;

  const partes: string[] = [];
  if (reais > 0 || cents === 0) {
    const extenso = inteiroPorExtenso(reais);
    // "um milhão de reais", "dois milhões de reais"
    const de = reais >= 1_000_000 && reais % 1_000_000 === 0 ? ' de' : '';
    partes.push(`${extenso}${de} ${reais === 1 ? 'real' : 'reais'}`);
  }
  if (cents > 0) {
    partes.push(
      `${inteiroPorExtenso(cents)} ${cents === 1 ? 'centavo' : 'centavos'}`
    );
  }

  return `${negativo ? 'menos ' : ''}${partes.join(' e ')}`;
};

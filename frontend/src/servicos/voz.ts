/**
 * Escolha da voz de leitura em voz alta (US13).
 * A voz padrão do navegador costuma soar robótica; as vozes "Natural"/neurais
 * (Edge) e as do Google (Chrome) soam bem mais humanas.
 */

const pontuarVoz = (voz: SpeechSynthesisVoice): number => {
  let pontos = 0;
  if (/natural|neural/i.test(voz.name)) pontos += 4;
  if (/online/i.test(voz.name)) pontos += 2;
  if (/google/i.test(voz.name)) pontos += 2;
  if (!voz.localService) pontos += 1;
  return pontos;
};

const ehPortuguesBr = (voz: SpeechSynthesisVoice) =>
  voz.lang.toLowerCase().replace('_', '-') === 'pt-br';

/** A voz em português do Brasil que soa mais natural, ou null se não houver. */
export const escolherVozPtBr = (
  vozes: SpeechSynthesisVoice[]
): SpeechSynthesisVoice | null => {
  const brasileiras = vozes.filter(ehPortuguesBr);
  const candidatas = brasileiras.length
    ? brasileiras
    : vozes.filter((v) => v.lang.toLowerCase().startsWith('pt'));
  return (
    [...candidatas].sort((a, b) => pontuarVoz(b) - pontuarVoz(a))[0] ?? null
  );
};

/** Fala em pt-BR com a melhor voz disponível e ritmo um pouco mais calmo. */
export const criarFala = (
  texto: string,
  voz: SpeechSynthesisVoice | null
): SpeechSynthesisUtterance => {
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = 'pt-BR';
  fala.rate = 0.92;
  fala.pitch = 1;
  if (voz) fala.voice = voz;
  return fala;
};

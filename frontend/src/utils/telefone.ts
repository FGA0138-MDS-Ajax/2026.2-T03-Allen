/**
 * Utilitários de máscara e validação de número de telefone celular no padrão brasileiro.
 */

const DDDS_VALIDOS = new Set([
  '11', '12', '13', '14', '15', '16', '17', '18', '19',
  '21', '22', '24', '27', '28',
  '31', '32', '33', '34', '35', '37', '38',
  '41', '42', '43', '44', '45', '46',
  '47', '48', '49',
  '51', '53', '54', '55',
  '61', '62', '63', '64', '65', '66', '67', '68', '69',
  '71', '73', '74', '75', '77', '79',
  '81', '82', '83', '84', '85', '86', '87', '88', '89',
  '91', '92', '93', '94', '95', '96', '97', '98', '99',
]);

/**
 * Remove qualquer caractere que não seja dígito numérico.
 */
export const extrairDigitos = (valor: string): string => {
  return valor.replace(/\D/g, '');
};

/**
 * Aplica a máscara brasileira de celular progressivamente:
 * Exemplo: (61) 99999-8888
 */
export const formatarCelular = (valor: string): string => {
  const digitos = extrairDigitos(valor).slice(0, 11);

  if (digitos.length === 0) return '';
  if (digitos.length <= 2) return `(${digitos}`;
  if (digitos.length <= 7) return `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`;
  return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7, 11)}`;
};

/**
 * Valida se a sequência numérica é um número de celular brasileiro válido:
 * - Exatamente 11 dígitos numéricos
 * - DDD existente no Brasil
 * - Terceiro dígito igual a 9 (padrão de celular nacional)
 */
export const validarCelular = (valor: string): boolean => {
  const digitos = extrairDigitos(valor);

  if (digitos.length !== 11) {
    return false;
  }

  const ddd = digitos.slice(0, 2);
  if (!DDDS_VALIDOS.has(ddd)) {
    return false;
  }

  // Celulares no Brasil iniciam com 9 logo após o DDD
  if (digitos[2] !== '9') {
    return false;
  }

  // Rejeita sequências repetidas como 11999999999
  const corpo = digitos.slice(2);
  const todosIguais = corpo.split('').every((d) => d === corpo[0]);
  if (todosIguais) {
    return false;
  }

  return true;
};

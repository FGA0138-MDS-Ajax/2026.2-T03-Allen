import { describe, it, expect } from 'vitest';
import { extrairDigitos, formatarCelular, validarCelular } from './telefone';

describe('Utilitários de telefone celular', () => {
  it('extrai apenas os dígitos numéricos de uma string', () => {
    expect(extrairDigitos('(61) 98765-4321')).toBe('61987654321');
    expect(extrairDigitos('abc-123.45')).toBe('12345');
    expect(extrairDigitos('')).toBe('');
  });

  it('formata o celular com máscara progressiva', () => {
    expect(formatarCelular('61')).toBe('(61');
    expect(formatarCelular('619')).toBe('(61) 9');
    expect(formatarCelular('6198765')).toBe('(61) 98765');
    expect(formatarCelular('61987654321')).toBe('(61) 98765-4321');
    expect(formatarCelular('61987654321000')).toBe('(61) 98765-4321'); // trunca em 11
  });

  it('valida corretamente celulares brasileiros legítimos', () => {
    expect(validarCelular('61987654321')).toBe(true);
    expect(validarCelular('(61) 98765-4321')).toBe(true);
    expect(validarCelular('11912345678')).toBe(true);
  });

  it('rejeita números com quantidade insuficiente de dígitos ou sem DDD', () => {
    expect(validarCelular('987654321')).toBe(false);
    expect(validarCelular('123456')).toBe(false);
    expect(validarCelular('')).toBe(false);
  });

  it('rejeita celulares com DDD inválido', () => {
    expect(validarCelular('00987654321')).toBe(false);
    expect(validarCelular('01987654321')).toBe(false);
  });

  it('rejeita números onde o primeiro dígito após DDD não é 9', () => {
    expect(validarCelular('61887654321')).toBe(false); // telefone fixo
  });

  it('rejeita números com todos os dígitos repetidos', () => {
    expect(validarCelular('11999999999')).toBe(false);
  });
});

import { describe, it, expect } from 'vitest';
import {
  parsearQrCodeNfce,
  parsearValorMonetario,
  sugerirCategoriaPorEstabelecimento,
  formatarCnpj,
} from './nfce';

describe('Utilitário NFC-e (QR Code de Nota Fiscal)', () => {
  it('formata CNPJ de 14 dígitos corretamente', () => {
    expect(formatarCnpj('12345678000199')).toBe('12.345.678/0001-99');
  });

  it('converte valores monetários com separador de milhar corretamente', () => {
    expect(parsearValorMonetario('1.234,56')).toBe(123456);
    expect(parsearValorMonetario('85,50')).toBe(8550);
    expect(parsearValorMonetario('1234.56')).toBe(123456);
    expect(parsearValorMonetario('0')).toBeNull();
  });

  it('interpreta URL NFC-e v2.0 online extraindo chave, UF, CNPJ e deixando estabelecimento vazio', () => {
    const url =
      'https://www.fazenda.df.gov.br/nfce/qrcode?p=53261112345678000199650010000123451123456789|2|1|1|ABCDEF';
    const res = parsearQrCodeNfce(url);

    expect(res.valido).toBe(true);
    expect(res.uf).toBe('DF');
    expect(res.cnpj).toBe('12.345.678/0001-99');
    expect(res.estabelecimento).toBe('');
    expect(res.chaveAcesso).toBe(
      '53261112345678000199650010000123451123456789'
    );
    expect(res.data.startsWith('2026-11-')).toBe(true);
    expect(res.centavos).toBeNull();
    expect(res.aviso).toBeTruthy();
  });

  it('interpreta URL NFC-e v2.0 de contingência extraindo dia e valor total do parâmetro p', () => {
    const url =
      'https://www.fazenda.df.gov.br/nfce/qrcode?p=53261112345678000199650010000123459123456789|2|1|14|125.90|7a626a|1|HASH';
    const res = parsearQrCodeNfce(url);

    expect(res.valido).toBe(true);
    expect(res.data).toBe('2026-11-14');
    expect(res.centavos).toBe(12590);
    expect(res.aviso).toBeUndefined();
  });

  it('interpreta URL NFC-e v1.0 extraindo valor total e data em hex', () => {
    // '2026-11-10' em hex = 323032362d31312d3130
    const url =
      'https://nfce.fazenda.sp.gov.br/consulta?chNFe=35261198765432000111650010000123451123456789&nVersao=100&tpAmb=1&dhEmi=323032362d31312d3130&vNF=142.90';
    const res = parsearQrCodeNfce(url);

    expect(res.valido).toBe(true);
    expect(res.uf).toBe('SP');
    expect(res.cnpj).toBe('98.765.432/0001-11');
    expect(res.data).toBe('2026-11-10');
    expect(res.centavos).toBe(14290);
    expect(res.aviso).toBeUndefined();
  });

  it('aceita payload JSON apenas quando permitido em modo de teste e rejeita em produção', () => {
    const json = JSON.stringify({
      estabelecimento: 'Supermercado Atacadão',
      valor: 89.5,
      data: '2026-11-12',
    });

    const emDev = parsearQrCodeNfce(json, true);
    expect(emDev.valido).toBe(true);
    expect(emDev.estabelecimento).toBe('Supermercado Atacadão');
    expect(emDev.centavos).toBe(8950);

    const emProd = parsearQrCodeNfce(json, false);
    expect(emProd.valido).toBe(false);
  });

  it('rejeita QR Code que não pertence a uma nota fiscal', () => {
    const res = parsearQrCodeNfce('https://google.com');
    expect(res.valido).toBe(false);
  });

  it('sugere categoria correta pelo nome do estabelecimento ou outros por padrão', () => {
    expect(sugerirCategoriaPorEstabelecimento('Drogaria São Paulo')).toBe(
      'farmacia'
    );
    expect(sugerirCategoriaPorEstabelecimento('Supermercado Dia')).toBe(
      'mercado'
    );
    expect(sugerirCategoriaPorEstabelecimento('Posto Ipiranga')).toBe(
      'transporte'
    );
    expect(sugerirCategoriaPorEstabelecimento('')).toBe('outros');
    expect(sugerirCategoriaPorEstabelecimento('Loja Exemplo')).toBe('outros');
  });
});

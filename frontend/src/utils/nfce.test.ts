import { describe, it, expect, vi, afterEach } from 'vitest';
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

  it('aceita o formato americano e não salva valor errado em texto ambíguo (#104)', () => {
    expect(parsearValorMonetario('1,250.00')).toBe(125000);
    expect(parsearValorMonetario('1.250')).toBe(125000);
    expect(parsearValorMonetario('1.234.567,89')).toBe(123456789);
    expect(parsearValorMonetario('R$ 45,90')).toBe(4590);
    expect(parsearValorMonetario('12,5')).toBe(1250);
    expect(parsearValorMonetario('10')).toBe(1000);
    expect(parsearValorMonetario('1,250')).toBeNull();
    expect(parsearValorMonetario('1,2,3')).toBeNull();
    expect(parsearValorMonetario('12.34,5.6')).toBeNull();
    expect(parsearValorMonetario(',')).toBeNull();
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

describe('NFS-e do padrão nacional (#122)', () => {
  // município (7) · ambiente (1) · tipo de inscrição (1) · CPF/CNPJ (14) ·
  // número (13) · AAMM (4) · código numérico (9) · DV (1)
  const chave = ({
    municipio = '5300108', // Brasília
    tipoInscricao = '2',
    inscricao = '12345678000195',
    aamm = '2610',
  } = {}) =>
    `${municipio}2${tipoInscricao}${inscricao}0000000000123${aamm}1234567890`;

  afterEach(() => {
    vi.useRealTimers();
  });

  const hojeEm23deNovembro = () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 10, 23, 10, 0));
  };

  it('monta chaves de 50 dígitos no teste', () => {
    expect(chave()).toHaveLength(50);
  });

  it('lê o QR da Consulta Pública: UF, CNPJ e mês da emissão, sem valor', () => {
    hojeEm23deNovembro();
    const res = parsearQrCodeNfce(
      `https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave=${chave()}`
    );

    expect(res).toMatchObject({
      valido: true,
      modelo: 'nfse',
      chaveAcesso: chave(),
      uf: 'DF',
      cnpj: '12.345.678/0001-95',
      estabelecimento: '',
      data: '2026-10-01',
      centavos: null,
    });
    expect(res.aviso).toMatch(/nota fiscal de serviço lida/i);
  });

  it('nota emitida no mês atual fica com a data de hoje', () => {
    hojeEm23deNovembro();
    const res = parsearQrCodeNfce(
      `https://www.nfse.gov.br/consultapublica?chave=${chave({ aamm: '2611' })}`
    );
    expect(res.data).toBe('2026-11-23');
  });

  it('aceita a chave pura e o identificador "NFS" + chave', () => {
    expect(parsearQrCodeNfce(chave()).modelo).toBe('nfse');
    expect(parsearQrCodeNfce(`NFS${chave()}`).chaveAcesso).toBe(chave());
  });

  it('não mostra o CPF de prestador pessoa física', () => {
    const res = parsearQrCodeNfce(
      chave({ tipoInscricao: '1', inscricao: '00012345678909' })
    );
    expect(res.valido).toBe(true);
    expect(res.cnpj).toBeUndefined();
  });

  it('50 dígitos sem a estrutura da chave não viram nota', () => {
    expect(parsearQrCodeNfce(chave({ municipio: '9900000' })).valido).toBe(
      false
    );
    expect(parsearQrCodeNfce(chave({ aamm: '2613' })).valido).toBe(false);
  });

  it('NFS-e de prefeitura fora do padrão nacional: aviso para digitar', () => {
    const res = parsearQrCodeNfce(
      'https://nfe.prefeitura.sp.gov.br/nfse/consulta?nf=123&verificacao=ABCD1234'
    );
    expect(res.valido).toBe(false);
    expect(res.aviso).toMatch(/prefeitura/i);
  });

  it('NFC-e continua sendo lida como nota de compra', () => {
    const res = parsearQrCodeNfce(
      'https://www.fazenda.df.gov.br/nfce/qrcode?p=53261112345678000199650010000123451123456789|2|1|1|HASH'
    );
    expect(res.valido).toBe(true);
    expect(res.modelo).not.toBe('nfse');
  });
});

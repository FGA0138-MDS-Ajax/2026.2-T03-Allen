/**
 * Utilitário para leitura e interpretação de QR Codes de nota fiscal: NFC-e (Nota Fiscal
 * de Consumidor Eletrônica, compras) e NFS-e do padrão nacional (serviços, #122).
 */

export interface DadosNfce {
  valido: boolean;
  /** nfce: nota de compra (chave de 44 dígitos); nfse: nota de serviço (50 dígitos) */
  modelo?: 'nfce' | 'nfse';
  chaveAcesso?: string;
  uf?: string;
  estabelecimento: string;
  cnpj?: string;
  data: string; // YYYY-MM-DD
  centavos: number | null;
  urlOriginal: string;
  aviso?: string;
}

const CODIGOS_UF: Record<string, string> = {
  '11': 'RO',
  '12': 'AC',
  '13': 'AM',
  '14': 'RR',
  '15': 'PA',
  '16': 'AP',
  '17': 'TO',
  '21': 'MA',
  '22': 'PI',
  '23': 'CE',
  '24': 'RN',
  '25': 'PB',
  '26': 'PE',
  '27': 'AL',
  '28': 'SE',
  '29': 'BA',
  '31': 'MG',
  '32': 'ES',
  '33': 'RJ',
  '35': 'SP',
  '41': 'PR',
  '42': 'SC',
  '43': 'RS',
  '50': 'MS',
  '51': 'MT',
  '52': 'GO',
  '53': 'DF',
};

export function formatarCnpj(cnpj: string): string {
  const limpo = cnpj.replace(/\D/g, '');
  if (limpo.length !== 14) return limpo;
  return limpo.replace(
    /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
    '$1.$2.$3/$4-$5'
  );
}

/** Separador de milhar seguido de grupos de 3 dígitos, ex.: "1.234.567" ou "1,250". */
const soMilhares = (texto: string, sep: string) =>
  new RegExp(`^\\d{1,3}(\\${sep}\\d{3})+$`).test(texto);

/**
 * Converte texto monetário em centavos. Aceita o formato brasileiro ("1.234,56",
 * "85,50", "1.250") e o americano ("1,250.00", "1234.56"). Quando há os dois
 * separadores, o último é o decimal. Texto ambíguo ou malformado devolve null,
 * para a tela pedir o valor de novo em vez de salvar um valor errado.
 */
export function parsearValorMonetario(texto: string): number | null {
  const limpo = texto.replace(/[^\d.,]/g, '').trim();
  if (!limpo || !/\d/.test(limpo)) return null;

  const ultimaVirgula = limpo.lastIndexOf(',');
  const ultimoPonto = limpo.lastIndexOf('.');
  let normalizado: string | null;

  if (ultimaVirgula >= 0 && ultimoPonto >= 0) {
    const decimal = ultimaVirgula > ultimoPonto ? ',' : '.';
    const milhar = decimal === ',' ? '.' : ',';
    const [inteiro, centavos, ...resto] = limpo.split(decimal);
    normalizado =
      resto.length === 0 &&
      /^\d{1,2}$/.test(centavos) &&
      soMilhares(inteiro, milhar)
        ? `${inteiro.split(milhar).join('')}.${centavos}`
        : null;
  } else if (ultimaVirgula >= 0 || ultimoPonto >= 0) {
    const sep = ultimaVirgula >= 0 ? ',' : '.';
    const partes = limpo.split(sep);
    if (
      partes.length === 2 &&
      /^\d+$/.test(partes[0]) &&
      /^\d{1,2}$/.test(partes[1])
    ) {
      normalizado = `${partes[0]}.${partes[1]}`;
    } else if (sep === '.' && soMilhares(limpo, '.')) {
      // "1.250" no Brasil é mil duzentos e cinquenta
      normalizado = partes.join('');
    } else {
      // "1,250" pode ser 1,25 ou 1.250: ambíguo, melhor pedir de novo
      normalizado = null;
    }
  } else {
    normalizado = limpo;
  }

  if (normalizado === null) return null;
  const numero = Number(normalizado);
  if (!Number.isFinite(numero) || numero <= 0) return null;
  return Math.round(numero * 100);
}

function decodificarHexParaTexto(hex: string): string {
  try {
    if (!/^[0-9a-fA-F]+$/.test(hex) || hex.length % 2 !== 0) {
      return hex;
    }
    const bytes = new Uint8Array(
      hex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16))
    );
    return new TextDecoder('utf-8').decode(bytes);
  } catch {
    return hex;
  }
}

function extrairDataDeTexto(bruto: string | null | undefined): string | null {
  if (!bruto) return null;
  const decodificado = decodificarHexParaTexto(bruto.trim());
  const matchIso = decodificado.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (matchIso) {
    return `${matchIso[1]}-${matchIso[2]}-${matchIso[3]}`;
  }
  const matchBr = decodificado.match(/(\d{2})\/(\d{2})\/(\d{4})/);
  if (matchBr) {
    return `${matchBr[3]}-${matchBr[2]}-${matchBr[1]}`;
  }
  return null;
}

function extrairCentavos(
  bruto: string | number | null | undefined
): number | null {
  if (bruto === null || bruto === undefined || bruto === '') return null;
  if (typeof bruto === 'number') {
    return Number.isFinite(bruto) && bruto > 0 ? Math.round(bruto * 100) : null;
  }
  return parsearValorMonetario(bruto);
}

function dataPadraoHoje(): string {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, '0');
  const dia = String(hoje.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

/**
 * Data aproximada a partir do ano/mês da chave: hoje, se a nota é do mês atual; senão,
 * o dia 1º daquele mês (ou o dia informado na contingência).
 */
function dataPorAnoMes(
  anoDoisDigitos: string,
  mes: string,
  diaExplicito?: string
): string {
  const ano = `20${anoDoisDigitos}`;
  const hoje = new Date();
  const anoAtual = String(hoje.getFullYear());
  const mesAtual = String(hoje.getMonth() + 1).padStart(2, '0');

  let dia =
    ano === anoAtual && mes === mesAtual
      ? String(hoje.getDate()).padStart(2, '0')
      : '01';

  if (diaExplicito) {
    const diaNum = parseInt(diaExplicito, 10);
    if (Number.isFinite(diaNum) && diaNum >= 1 && diaNum <= 31) {
      dia = String(diaNum).padStart(2, '0');
    }
  }

  const mesValido = Number(mes) >= 1 && Number(mes) <= 12 ? mes : mesAtual;
  return `${ano}-${mesValido}-${dia}`;
}

function extrairDadosDaChave44(
  chave: string,
  diaExplicito?: string
): {
  uf: string;
  cnpj: string;
  dataEstimada: string;
} {
  const codUf = chave.slice(0, 2);
  return {
    uf: CODIGOS_UF[codUf] || 'BR',
    cnpj: formatarCnpj(chave.slice(6, 20)),
    dataEstimada: dataPorAnoMes(
      chave.slice(2, 4),
      chave.slice(4, 6),
      diaExplicito
    ),
  };
}

/**
 * Chave de acesso da NFS-e do padrão nacional (50 dígitos):
 * município IBGE (7) · ambiente gerador (1) · tipo de inscrição 1=CPF/2=CNPJ (1) ·
 * CPF/CNPJ do prestador (14) · número da NFS-e (13) · ano e mês da emissão AAMM (4) ·
 * código numérico (9) · dígito verificador (1).
 * Devolve null se a estrutura não bate (não é uma chave de NFS-e).
 */
function extrairDadosDaChaveNfse(chave: string): {
  uf: string;
  cnpj?: string;
  dataEstimada: string;
} | null {
  if (!/^\d{50}$/.test(chave)) return null;
  const uf = CODIGOS_UF[chave.slice(0, 2)];
  const ambiente = chave[7];
  const tipoInscricao = chave[8];
  const mes = Number(chave.slice(38, 40));
  if (
    !uf ||
    (ambiente !== '1' && ambiente !== '2') ||
    (tipoInscricao !== '1' && tipoInscricao !== '2') ||
    mes < 1 ||
    mes > 12
  ) {
    return null;
  }
  return {
    uf,
    // CPF de prestador pessoa física não é mostrado (é dado pessoal)
    cnpj: tipoInscricao === '2' ? formatarCnpj(chave.slice(9, 23)) : undefined,
    // AAMM nas posições 37 a 40
    dataEstimada: dataPorAnoMes(chave.slice(36, 38), chave.slice(38, 40)),
  };
}

const AVISO_NFSE =
  'Nota fiscal de serviço lida! O valor não vem dentro do código: digite o valor total abaixo.';

/** NFS-e de prefeitura fora do padrão nacional: cada cidade tem o seu formato. */
const AVISO_NFSE_MUNICIPAL =
  'Essa nota fiscal de serviço é de um sistema da prefeitura que o Vero ainda não consegue ler. Digite o valor abaixo.';

function lerNfseNacional(texto: string): DadosNfce | null {
  const semPrefixo = texto.replace(/NFS(?=\d{50})/g, '');
  for (const candidata of semPrefixo.match(/\d{50}/g) ?? []) {
    const dados = extrairDadosDaChaveNfse(candidata);
    if (dados) {
      return {
        valido: true,
        modelo: 'nfse',
        chaveAcesso: candidata,
        uf: dados.uf,
        cnpj: dados.cnpj,
        estabelecimento: '',
        data: dados.dataEstimada,
        centavos: null,
        urlOriginal: texto,
        aviso: AVISO_NFSE,
      };
    }
  }
  return null;
}

/**
 * Interpreta o conteúdo lido de um QR Code de nota fiscal (NFC-e v1, v2, contingência,
 * NFS-e nacional ou JSON em dev).
 */
export function parsearQrCodeNfce(
  textoBruto: string,
  permitirJsonTeste = import.meta.env.DEV
): DadosNfce {
  const texto = textoBruto.trim();
  const hojeStr = dataPadraoHoje();

  if (!texto) {
    return {
      valido: false,
      estabelecimento: '',
      data: hojeStr,
      centavos: null,
      urlOriginal: texto,
    };
  }

  // 1. Payload JSON simplificado (restrito ao modo de desenvolvimento/testes)
  if (permitirJsonTeste && texto.startsWith('{') && texto.endsWith('}')) {
    try {
      const obj = JSON.parse(texto) as Record<string, unknown>;
      const centavos = extrairCentavos(
        (obj.valor as string | number | undefined) ??
          (obj.vNF as string | number | undefined)
      );
      const nome =
        typeof obj.estabelecimento === 'string'
          ? obj.estabelecimento.trim()
          : typeof obj.xNome === 'string'
            ? obj.xNome.trim()
            : '';
      const data =
        extrairDataDeTexto(
          typeof obj.data === 'string' ? obj.data : undefined
        ) || hojeStr;

      if (nome && centavos) {
        return {
          valido: true,
          estabelecimento: nome,
          data,
          centavos,
          urlOriginal: texto,
        };
      }
    } catch {
      // Segue para tentativa de URL
    }
  }

  // 2. Leitura como URL de SEFAZ (NFC-e v1.0, v2.0 online ou v2.0 contingência offline)
  let url: URL | null = null;
  try {
    url = new URL(texto);
  } catch {
    url = null;
  }

  if (url) {
    // NFS-e nacional: QR da Consulta Pública com a chave de 50 dígitos (#122)
    const ehNfse = /nfs-?e/i.test(url.hostname + url.pathname);
    if (ehNfse) {
      const nfse = lerNfseNacional(texto);
      if (nfse) return nfse;
      return {
        valido: false,
        modelo: 'nfse',
        estabelecimento: '',
        data: hojeStr,
        centavos: null,
        urlOriginal: texto,
        aviso: AVISO_NFSE_MUNICIPAL,
      };
    }

    const params = url.searchParams;
    const parametroP = params.get('p');

    // Layout 2.0:
    // Online: ?p=CHAVE44|2|tpAmb|idCSC|cHashQRCode
    // Contingência: ?p=CHAVE44|2|tpAmb|diaEmissao|vNF|digVal|idCSC|cHashQRCode
    if (parametroP) {
      const partes = parametroP.split('|');
      const possivelChave = (partes[0] || '').replace(/\D/g, '');

      if (possivelChave.length === 44) {
        const ehContingencia =
          partes.length >= 7 && /^\d{1,2}$/.test(partes[3] || '');
        const diaContingencia = ehContingencia ? partes[3] : undefined;
        const valorContingencia = ehContingencia
          ? extrairCentavos(partes[4])
          : null;

        const { uf, cnpj, dataEstimada } = extrairDadosDaChave44(
          possivelChave,
          diaContingencia
        );
        const valorExtra =
          valorContingencia ??
          extrairCentavos(params.get('vNF') || params.get('valor'));
        const nomeExtra = (
          params.get('estabelecimento') ||
          params.get('xNome') ||
          ''
        ).trim();
        const dataExtra = extrairDataDeTexto(params.get('dhEmi'));

        return {
          valido: true,
          chaveAcesso: possivelChave,
          uf,
          cnpj,
          estabelecimento: nomeExtra,
          data: dataExtra || dataEstimada,
          centavos: valorExtra,
          urlOriginal: texto,
          aviso:
            valorExtra === null
              ? 'QR Code da nota lido! A SEFAZ do estado não envia o valor dentro do código — digite ou confira o valor total abaixo.'
              : undefined,
        };
      }
    }

    // Layout 1.0: ?chNFe=CHAVE44&...&dhEmi=...&vNF=123.45
    const chNFe = (params.get('chNFe') || '').replace(/\D/g, '');
    const vNF = extrairCentavos(params.get('vNF') || params.get('valor'));
    const dhEmi = extrairDataDeTexto(params.get('dhEmi') || params.get('data'));
    const xNome = (
      params.get('xNome') ||
      params.get('estabelecimento') ||
      ''
    ).trim();

    if (chNFe.length === 44) {
      const { uf, cnpj, dataEstimada } = extrairDadosDaChave44(chNFe);
      return {
        valido: true,
        chaveAcesso: chNFe,
        uf,
        cnpj,
        estabelecimento: xNome,
        data: dhEmi || dataEstimada,
        centavos: vNF,
        urlOriginal: texto,
        aviso:
          vNF === null
            ? 'Nota fiscal identificada, mas o valor total não veio no código. Informe o valor abaixo.'
            : undefined,
      };
    }

    // Fallback para URL da SEFAZ/Fazenda que contenha 44 dígitos na string
    const ehSefaz = /fazenda|sefaz|nfce|nfe|sat/i.test(
      url.hostname + url.pathname
    );
    const matchChave = texto.match(/\d{44}/);
    if (ehSefaz && matchChave) {
      const { uf, cnpj, dataEstimada } = extrairDadosDaChave44(matchChave[0]);
      return {
        valido: true,
        chaveAcesso: matchChave[0],
        uf,
        cnpj,
        estabelecimento: xNome,
        data: dhEmi || dataEstimada,
        centavos: vNF,
        urlOriginal: texto,
        aviso:
          vNF === null
            ? 'Nota fiscal identificada, mas não foi possível consultar o valor automático na SEFAZ. Digite o valor total abaixo.'
            : undefined,
      };
    }
  }

  // 3. Chave de acesso pura: 50 dígitos (NFS-e) ou 44 dígitos (NFC-e)
  if (texto.length <= 60) {
    const nfse = lerNfseNacional(texto.replace(/[\s.-]/g, ''));
    if (nfse) return { ...nfse, urlOriginal: texto };
  }

  const apenasDigitos = texto.replace(/\D/g, '');
  if (apenasDigitos.length === 44 && texto.length <= 54) {
    const { uf, cnpj, dataEstimada } = extrairDadosDaChave44(apenasDigitos);
    return {
      valido: true,
      chaveAcesso: apenasDigitos,
      uf,
      cnpj,
      estabelecimento: '',
      data: dataEstimada,
      centavos: null,
      urlOriginal: texto,
      aviso:
        'Chave da nota fiscal identificada! Informe o valor total abaixo para concluir.',
    };
  }

  return {
    valido: false,
    estabelecimento: '',
    data: hojeStr,
    centavos: null,
    urlOriginal: texto,
  };
}

/**
 * Sugere uma categoria de gasto do Vero com base no nome do estabelecimento.
 */
export function sugerirCategoriaPorEstabelecimento(nome: string): string {
  const n = nome.trim().toLowerCase();
  if (!n) return 'outros';

  if (
    n.includes('mercado') ||
    n.includes('super') ||
    n.includes('atacad') ||
    n.includes('padaria') ||
    n.includes('horti') ||
    n.includes('açougue') ||
    n.includes('acougue') ||
    n.includes('mercearia')
  ) {
    return 'mercado';
  }
  if (
    n.includes('farm') ||
    n.includes('drog') ||
    n.includes('saude') ||
    n.includes('saúde') ||
    n.includes('medic')
  ) {
    return 'farmacia';
  }
  if (
    n.includes('posto') ||
    n.includes('combust') ||
    n.includes('uber') ||
    n.includes('transport') ||
    n.includes('estaciona')
  ) {
    return 'transporte';
  }
  if (
    n.includes('casa') ||
    n.includes('constru') ||
    n.includes('material') ||
    n.includes('moveis') ||
    n.includes('móveis')
  ) {
    return 'casa';
  }
  return 'outros';
}

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from rapidfuzz import fuzz, process


class TipoTransacao(StrEnum):
    GASTO = "GASTO"
    RECEITA = "RECEITA"
    DESCONHECIDO = "DESCONHECIDO"


@dataclass
class IntencaoMensagem:
    tipo: TipoTransacao
    # Valor em centavos
    valor: int | None
    categoria: str
    descricao: str
    sucesso: bool
    motivo_recusa: str | None = None


CATEGORIAS: dict[str, list[str]] = {
    # Gastos
    "Farmácia": [
        "farmacia",
        "farmasia",
        "remedio",
        "drogaria",
        "medicamento",
        "dipirona",
        "pomada",
    ],
    "Alimentação": [
        "mercado",
        "supermercado",
        "padaria",
        "comida",
        "feira",
        "acougue",
        "almoco",
        "jantar",
        "pao",
        "paes",
        "leite",
        "lanche",
        "restaurante",
        "cafe",
    ],
    "Transporte": [
        "uber",
        "taxi",
        "onibus",
        "gasolina",
        "combustivel",
        "passagem",
        "metro",
    ],
    "Saúde": [
        "medico",
        "consulta",
        "exame",
        "dentista",
        "hospital",
        "clinica",
        "fisioterapia",
    ],
    "Moradia": ["aluguel", "condominio", "luz", "agua", "gas", "energia", "internet"],
    "Lazer": [
        "passeio",
        "viagem",
        "cinema",
        "bar",
        "presente",
        "cerveja",
        "cigarro",
        "churrasco",
    ],
    # Receitas
    "Aposentadoria": ["aposentadoria", "inss", "beneficio"],
    "Salário": ["salario", "pagamento", "vale", "adiantamento"],
    "Renda Extra": ["bico", "venda", "freela", "renda", "reembolso", "pix"],
}

VERBOS_RECEITA = [
    "recebi",
    "recebeu",
    "receber",
    "recebimento",
    "caiu",
    "ganhei",
    "ganhou",
    "entrou",
    "deposito",
]
VERBOS_GASTO = [
    "gastei",
    "gastou",
    "gasto",
    "comprei",
    "comprou",
    "comprar",
    "paguei",
    "pagou",
    "foi",
    "deu",
    "custou",
    "despesa",
    "perdi",
]
MARCADORES_FUTURO = [
    "vou gastar",
    "vou pagar",
    "vou comprar",
    "pretendo",
    "amanha",
    "amanhã",
    "semana que vem",
    "mes que vem",
    "mês que vem",
]

PADROES_BOAS_VINDAS = [
    "acabei de criar",
    "criar minha conta",
    "criei minha conta",
    "primeiro acesso",
    "gostaria de anotar",
    "anotar um gasto",
    "como funciona",
    "ajuda",
]

SAUDACOES = {
    "oi",
    "ola",
    "ola vero",
    "oi vero",
    "bom dia",
    "boa tarde",
    "boa noite",
    "opa",
    "e ai",
    "eai",
    "ola assistente",
}


def eh_saudacao(texto: str) -> bool:
    texto_norm = normalizar_texto(texto.strip())
    texto_limpo = re.sub(r"[^\w\s]", "", texto_norm).strip()

    if texto_limpo in SAUDACOES:
        return True

    for padrao in PADROES_BOAS_VINDAS:
        if padrao in texto_norm:
            return True

    tokens = texto_limpo.split()
    if len(tokens) <= 3 and any(t in {"oi", "ola", "opa"} for t in tokens):
        return True

    return False


def normalizar_texto(texto: str) -> str:
    texto = texto.lower()
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def contem_palavra(texto_norm: str, palavras: list[str]) -> bool:
    padrao = r"\b(?:" + "|".join(re.escape(p) for p in palavras) + r")\b"
    return bool(re.search(padrao, texto_norm))


def eh_tempo_futuro(texto_norm: str) -> bool:
    for marcador in MARCADORES_FUTURO:
        if marcador in texto_norm:
            return True

    return False


def string_para_centavos(num_str: str) -> int | None:
    s = num_str.strip()
    try:
        if "." in s and "," in s:
            p_pos = s.rfind(".")
            c_pos = s.rfind(",")
            if c_pos > p_pos:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        elif "." in s:
            partes = s.split(".")

            if len(partes) == 2 and len(partes[1]) == 3:
                s = s.replace(".", "")
            elif len(partes) > 2:
                s = s.replace(".", "")

        valor_float = float(s)
        if valor_float <= 0:
            return None
        return int(round(valor_float * 100))
    except (ValueError, IndexError):
        return None


# Retorna em centavos
def extrair_valor(texto: str) -> tuple[int | None, bool]:
    texto_lower = texto.lower()

    # Rejeita valores negativos
    if re.search(r"-\s*\d+", texto_lower):
        return None, False

    # Separa reais e centavos
    match_reais_centavos = re.search(
        r"\b(\d+)\s*(?:reais|real|conto)\s*(?:e\s*)?(\d{1,2})\s*centavos?\b",
        texto_lower,
    )
    if match_reais_centavos:
        reais = int(match_reais_centavos.group(1))
        centavos = int(match_reais_centavos.group(2).ljust(2, "0")[:2])
        return (reais * 100 + centavos), False

    # Limpeza de valores não monetários
    texto_limpo = re.sub(r"\bdia\s+\d{1,2}\b", "", texto_lower)
    texto_limpo = re.sub(
        r"\b\d+\s+(?:pães|paes|pao|itens|unidades|garrafas|latas|pecas|peças|litros|quilos|kg|caixas)\b",
        " ",
        texto_limpo,
    )

    # Procura valores numéricos no texto limpo
    matches = list(
        re.finditer(
            r"(?:r\$\s*)?((?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{1,2})?)", texto_limpo
        )
    )
    candidatos: list[tuple[int, int]] = []  # (valor, peso_prioridade)
    for m in matches:
        num_str = m.group(1)
        if len(num_str) == 4 and num_str.startswith("20") and "r$" not in m.group(0):
            continue
        v = string_para_centavos(num_str)
        if v is not None and v > 0:
            inicio, fim = m.span()
            contexto = texto_limpo[
                max(0, inicio - 10) : min(len(texto_limpo), fim + 10)
            ]
            peso = 1
            if any(
                termo in contexto
                for termo in ["r$", "reais", "real", "conto", "por", "de"]
            ):
                peso = 2
            candidatos.append((v, peso))

    if not candidatos:
        return None, False

    if len(candidatos) > 1:
        if re.search(r"\b\d+.*?\be\s+\d+", texto_limpo):
            return None, True

    # Ordena pela prioridade
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0][0], False


def identificar_categoria(texto_normalizado: str, tipo: TipoTransacao) -> str:
    todas_palavras = texto_normalizado.split()
    melhor_score = 0.0
    melhor_categoria = "Outros" if tipo == TipoTransacao.GASTO else "Outras Receitas"

    for categoria, sinonimos in CATEGORIAS.items():
        for palavra in todas_palavras:
            if len(palavra) < 3:
                continue

            resultado = process.extractOne(
                palavra,
                sinonimos,
                scorer=fuzz.ratio,
                score_cutoff=75.0,  # Limiar de confiança de 75%
            )

            if resultado:
                _, score, _ = resultado
                if score > melhor_score:
                    melhor_score = score
                    melhor_categoria = categoria

    return melhor_categoria


def processar_texto_mensagem(texto: str) -> IntencaoMensagem:
    texto_norm = normalizar_texto(texto)

    if eh_tempo_futuro(texto_norm):
        return IntencaoMensagem(
            tipo=TipoTransacao.DESCONHECIDO,
            valor=None,
            categoria="Outros",
            descricao=texto.strip(),
            sucesso=False,
            motivo_recusa="futuro",
        )

    valor, eh_unica = extrair_valor(texto)

    bool_receita = contem_palavra(texto_norm, VERBOS_RECEITA)
    bool_gasto = contem_palavra(texto_norm, VERBOS_GASTO)

    if "pagamento" in texto_norm and bool_receita:
        bool_gasto = False

    if (bool_receita and bool_gasto) or eh_unica:
        return IntencaoMensagem(
            tipo=TipoTransacao.DESCONHECIDO,
            valor=None,
            categoria="Outros",
            descricao=texto.strip(),
            sucesso=False,
            motivo_recusa="multiplas_transacoes",
        )

    tipo = TipoTransacao.DESCONHECIDO
    if bool_receita:
        tipo = TipoTransacao.RECEITA
    elif bool_gasto:
        tipo = TipoTransacao.GASTO
    elif "aposentadoria" in texto_norm or "salario" in texto_norm:
        tipo = TipoTransacao.RECEITA
    elif valor is not None:
        tipo = TipoTransacao.GASTO

    categoria = identificar_categoria(texto_norm, tipo)
    sucesso = (valor is not None) and (tipo != TipoTransacao.DESCONHECIDO)
    # Sabemos o que foi, mas não quanto: o assistente pede só o valor (RF16)
    motivo = (
        "sem_valor" if valor is None and tipo != TipoTransacao.DESCONHECIDO else None
    )

    return IntencaoMensagem(
        tipo=tipo,
        valor=valor,
        categoria=categoria,
        descricao=texto.strip(),
        sucesso=sucesso,
        motivo_recusa=motivo,
    )


RESPOSTAS_GASTO = ["gasto", "gastei", "saida", "despesa", "paguei", "compra", "comprei"]
RESPOSTAS_RECEITA = ["entrada", "recebi", "receita", "ganhei", "rendimento", "caiu"]


def identificar_tipo_resposta(texto: str) -> TipoTransacao:
    """Lê a resposta a "foi um gasto ou uma entrada?" (RF16)."""
    texto_norm = normalizar_texto(texto)
    gasto = contem_palavra(texto_norm, RESPOSTAS_GASTO)
    receita = contem_palavra(texto_norm, RESPOSTAS_RECEITA)
    if gasto and not receita:
        return TipoTransacao.GASTO
    if receita and not gasto:
        return TipoTransacao.RECEITA
    return TipoTransacao.DESCONHECIDO

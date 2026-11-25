"""RF24: resumo periódico das finanças no WhatsApp (semanal e mensal).

Conteúdo curto: quanto gastou no período, onde mais gastou e quanto resta no mês.
A pessoa desliga respondendo "parar resumo" e volta a receber com "voltar resumo".
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes import servico as servico_transacoes
from app.nucleo.banco import SessaoLocal

MESES = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]

# Quantas categorias aparecem em "onde mais gastou"
MAIORES_CATEGORIAS = 3


class Periodo(StrEnum):
    SEMANAL = "semanal"
    MENSAL = "mensal"


@dataclass
class Resumo:
    periodo: Periodo
    inicio: date
    fim: date
    gastos: Decimal
    categorias: list[tuple[str, Decimal]]
    # Saldo do mês do fim do período (entradas - gastos - contas), como no app
    saldo_mes: Decimal


def datas_do_periodo(periodo: Periodo, hoje: date) -> tuple[date, date]:
    """Semanal: os 7 dias antes de hoje. Mensal: o mês anterior inteiro."""
    ontem = hoje - timedelta(days=1)
    if periodo == Periodo.SEMANAL:
        return hoje - timedelta(days=7), ontem
    return ontem.replace(day=1), ontem


def montar_resumo(
    sessao: Session, usuario_id: uuid.UUID, periodo: Periodo, hoje: date
) -> Resumo | None:
    """None quando não houve nenhum gasto no período: não manda resumo vazio."""
    inicio, fim = datas_do_periodo(periodo, hoje)
    gastos, categorias = servico_transacoes.gastos_do_periodo(
        sessao, usuario_id, inicio, fim
    )
    if gastos <= 0:
        return None
    saldo = servico_transacoes.resumir_mes(sessao, usuario_id, fim.strftime("%Y-%m"))
    return Resumo(
        periodo=periodo,
        inicio=inicio,
        fim=fim,
        gastos=gastos,
        categorias=categorias[:MAIORES_CATEGORIAS],
        saldo_mes=saldo.saldo,
    )


def _moeda(valor: Decimal) -> str:
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _juntar(itens: list[str]) -> str:
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def texto_resumo(resumo: Resumo) -> str:
    """Texto curto e fixo, com só os números variando: cabe num template de
    mensagem caso o envio passe para a API oficial do WhatsApp."""
    mes = MESES[resumo.fim.month - 1]
    if resumo.periodo == Periodo.SEMANAL:
        titulo = (
            f"📊 *Seu resumo da semana* ({resumo.inicio:%d/%m} a {resumo.fim:%d/%m})"
        )
        quando = "Nos últimos 7 dias, você gastou"
    else:
        titulo = f"📊 *Seu resumo de {mes}*"
        quando = f"Em {mes}, você gastou"

    linhas = [titulo, "", f"{quando} *{_moeda(resumo.gastos)}*."]
    if resumo.categorias:
        maiores = [f"{nome} ({_moeda(valor)})" for nome, valor in resumo.categorias]
        linhas.append(f"Onde mais gastou: {_juntar(maiores)}.")

    if resumo.saldo_mes >= 0:
        verbo = "ainda restam" if resumo.periodo == Periodo.SEMANAL else "sobraram"
        linhas.append(f"Em {mes}, {verbo} *{_moeda(resumo.saldo_mes)}*.")
    else:
        linhas.append(
            f"Em {mes}, os gastos passaram as entradas em "
            f"*{_moeda(-resumo.saldo_mes)}*."
        )

    linhas += ["", "Para não receber mais este resumo, responda *parar resumo*."]
    return "\n".join(linhas)


# Comandos no WhatsApp


def _normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


# Palavras que, numa mensagem curta que fala de "resumo", mostram o que a pessoa
# quer (#137). Não precisa ser a frase exata: "parar resumo por favor" também vale
PARA_DESLIGAR = {
    "parar",
    "pare",
    "cancelar",
    "cancela",
    "desligar",
    "desliga",
    "tirar",
    "tira",
    "chega",
    "sem",
    "nao",
    "nunca",
}
PARA_LIGAR = {
    "voltar",
    "volta",
    "quero",
    "ligar",
    "liga",
    "ativar",
    "ativa",
    "receber",
    "mandar",
    "manda",
}
# Mensagens mais longas que isso são conversa, não comando
MAX_PALAVRAS_COMANDO = 10


def comando_resumo(texto: str) -> bool | None:
    """False para desligar, True para ligar, None se a mensagem não é um comando.

    Negação ganha: "não quero mais receber resumo" desliga, mesmo tendo "quero" e
    "receber"."""
    palavras = _normalizar(texto).split()
    if not {"resumo", "resumos"} & set(palavras):
        return None
    if len(palavras) > MAX_PALAVRAS_COMANDO:
        return None
    if PARA_DESLIGAR & set(palavras):
        return False
    if PARA_LIGAR & set(palavras):
        return True
    return None


def tratar_comando(usuario_id: uuid.UUID, texto: str) -> str | None:
    """Se a mensagem liga ou desliga o resumo, grava a preferência e devolve a
    resposta para a pessoa. Senão, None (a mensagem segue para o assistente)."""
    ativo = comando_resumo(texto)
    if ativo is None:
        return None
    with SessaoLocal() as sessao:
        usuario = sessao.get(Usuario, usuario_id)
        if usuario is not None:
            usuario.resumo_ativo = ativo
            sessao.commit()
    if ativo:
        return (
            "Pronto! Vou voltar a mandar o resumo das suas finanças toda segunda-feira "
            "e no começo de cada mês."
        )
    return (
        "Tudo bem, não vou mais mandar o resumo.\n\n"
        "Se quiser receber de novo, é só responder *voltar resumo*."
    )

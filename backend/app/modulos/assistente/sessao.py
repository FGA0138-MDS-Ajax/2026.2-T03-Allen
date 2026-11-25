import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import valkey

from app.modulos.assistente.extrator import TipoTransacao
from app.nucleo.config import settings

logger = logging.getLogger(__name__)

TEMPO_EXPIRACAO_SEGUNDOS = 15 * 60


class CampoFaltando(StrEnum):
    """Dado que o assistente não conseguiu extrair e pediu à pessoa (RF16)."""

    VALOR = "valor"
    TIPO = "tipo"
    CATEGORIA = "categoria"


EMOJIS_SIM = {"👍", "✅"}
EMOJIS_NAO = {"👎", "❌"}


def normalizar_resposta(texto: str) -> str:
    t = texto.lower().strip()
    t = re.sub(r"[!.,?;:\-_]", " ", t)
    t_sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"
    )

    return " ".join(t_sem_acento.split())


@dataclass
class RegistroPendente:
    tipo: TipoTransacao
    # Em centavos. Vazio enquanto o assistente espera a pessoa dizer o valor (RF16)
    valor: int | None
    categoria: str
    descricao: str
    criado: datetime
    # Preenchido quando o lançamento está incompleto: o assistente pediu este dado
    # e a próxima mensagem completa o lançamento, em vez de começar outro (RF16)
    faltando: CampoFaltando | None = None
    # Valor do enum noOrigem da tblTransacao: de onde veio o lançamento (texto, foto)
    origem: str = "whatsapp_texto"


class GerenciadorSessao:
    def __init__(self):
        self._sessoes_memoria: dict[str, RegistroPendente] = {}
        try:
            self._valkey = valkey.Valkey.from_url(
                settings.VALKEY_URL, decode_responses=True
            )
            self._valkey.ping()
        except Exception:
            self._valkey = None

    def _chave(self, telefone: str) -> str:
        return f"vero:sessao_assistente:{telefone}"

    def salvar_pendencia(
        self,
        telefone: str,
        tipo: TipoTransacao,
        valor: int | None,
        categoria: str,
        descricao: str,
        faltando: CampoFaltando | None = None,
        origem: str = "whatsapp_texto",
    ) -> None:
        agora = datetime.now(UTC)
        pendencia = RegistroPendente(
            tipo=tipo,
            valor=valor,
            categoria=categoria,
            descricao=descricao,
            criado=agora,
            faltando=faltando,
            origem=origem,
        )

        if self._valkey:
            try:
                dados = asdict(pendencia)
                dados["tipo"] = dados["tipo"].value
                dados["criado"] = dados["criado"].isoformat()
                self._valkey.setex(
                    self._chave(telefone),
                    24 * 3600,
                    json.dumps(dados),
                )
                return
            except Exception as e:
                logger.warning(
                    "Falha ao salvar sessão no Valkey (%s). Usando memória.", e
                )

        self._sessoes_memoria[telefone] = pendencia

    def obter_pendencia(self, telefone: str) -> tuple[RegistroPendente | None, bool]:
        agora = datetime.now(UTC)

        if self._valkey:
            try:
                conteudo = self._valkey.get(self._chave(telefone))
                if conteudo:
                    dados = json.loads(conteudo)
                    criado = datetime.fromisoformat(dados["criado"])

                    if agora - criado > timedelta(seconds=TEMPO_EXPIRACAO_SEGUNDOS):
                        self.limpar_pendencia(telefone)
                        return None, True

                    valor = dados.get("valor")
                    faltando = dados.get("faltando")
                    return (
                        RegistroPendente(
                            tipo=TipoTransacao(dados["tipo"]),
                            valor=int(valor) if valor is not None else None,
                            categoria=dados["categoria"],
                            descricao=dados["descricao"],
                            criado=criado,
                            faltando=CampoFaltando(faltando) if faltando else None,
                            origem=dados.get("origem", "whatsapp_texto"),
                        ),
                        False,
                    )
            except Exception as e:
                logger.warning("Falha ao obter sessão do Valkey (%s).", e)

        pendencia = self._sessoes_memoria.get(telefone)
        if not pendencia:
            return None, False

        if agora - pendencia.criado > timedelta(seconds=TEMPO_EXPIRACAO_SEGUNDOS):
            del self._sessoes_memoria[telefone]
            return None, True

        return pendencia, False

    def limpar_pendencia(self, telefone: str) -> None:
        if self._valkey:
            try:
                self._valkey.delete(self._chave(telefone))
            except Exception:
                pass

        self._sessoes_memoria.pop(telefone, None)

    @staticmethod
    def resposta_sim(texto: str) -> bool:
        texto_strip = texto.strip()
        if any(e in texto_strip for e in EMOJIS_SIM):
            return True

        norm = normalizar_resposta(texto)
        if not norm:
            return False

        afirmativos = {
            "sim",
            "s",
            "pode",
            "isso",
            "claro",
            "confirmo",
            "correto",
            "pode ser",
            "anota",
            "ok",
            "okay",
            "blz",
            "beleza",
            "esta certo",
            "ta certo",
            "com certeza",
            "anota ai",
            "pode sim",
            "sim pode",
            "sim pode anotar",
            "sim anota",
        }

        if norm in afirmativos:
            return True

        if re.match(r"^(?:sim|s|ok|pode|claro|confirmo|anota)\b", norm):
            return True

        return False

    @staticmethod
    def resposta_nao(texto: str) -> bool:
        texto_strip = texto.strip()
        if any(e in texto_strip for e in EMOJIS_NAO):
            return True

        norm = normalizar_resposta(texto)
        if not norm:
            return False

        negativos = {
            "nao",
            "n",
            "cancela",
            "cancelar",
            "errei",
            "errado",
            "espera",
            "parar",
            "deixa",
            "esquece",
            "nem pensar",
        }

        if norm in negativos:
            return True

        if re.match(r"^(?:nao|n|cancela|cancelar|errei|errado)\b", norm):
            return True

        return False


sessao_assistente = GerenciadorSessao()

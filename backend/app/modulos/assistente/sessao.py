import json
import logging
import re
import unicodedata
import valkey
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from app.modulos.assistente.extrator import TipoTransacao
from app.nucleo.config import settings

logger = logging.getLogger(__name__)

TEMPO_EXPIRACAO_SEGUNDOS = 15 * 60

EMOJIS_SIM = {"👍", "✅"}
EMOJIS_NAO = {"👎", "❌"}

def normalizar_resposta(texto: str) -> str:
    t = texto.lower().strip()
    t = re.sub(r"[!.,?;:\-_]", " ", t)
    t_sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )

    return " ".join(t_sem_acento.split())

@dataclass
class RegistroPendente:
    tipo: TipoTransacao
    valor: int
    categoria: str
    descricao: str
    criado: datetime

class GerenciadorSessao:
    def __init__(self):
        self._sessoes_memoria: dict[str, RegistroPendente] = {}
        try:
            self._valkey = valkey.Valkey.from_url(settings.VALKEY_URL, decode_responses=True)
            self._valkey.ping()
        except Exception:
            self._valkey = None

    def _chave(self, telefone: str) -> str:
        return f"vero:sessao_assistente:{telefone}"

    def salvar_pendencia(self, telefone: str, tipo: TipoTransacao, valor: int, categoria: str, descricao: str) -> None:
        agora = datetime.now(timezone.utc)
        pendencia = RegistroPendente(
            tipo=tipo,
            valor=valor,
            categoria=categoria,
            descricao=descricao,
            criado=agora,
        )

        if self._valkey:
            try:
                dados = asdict(pendencia)
                dados["tipo"] = dados["tipo"].value
                dados["criado"] = dados["criado"].isoformat()
                self._valkey.setex(
                    self._chave(telefone),
                    TEMPO_EXPIRACAO_SEGUNDOS,
                    json.dumps(dados),
                )
                return
            except Exception as e:
                logger.warning("Falha ao salvar sessão no Valkey (%s). Usando memória.", e)

        self._sessoes_memoria[telefone] = pendencia

    def obter_pendencia(self, telefone: str) -> tuple[RegistroPendente | None, bool]:
        if self._valkey:
            try:
                conteudo = self._valkey.get(self._chave(telefone))
                if conteudo:
                    dados = json.loads(conteudo)
                    return (
                        RegistroPendente(
                            tipo=TipoTransacao(dados["tipo"]),
                            valor=int(dados["valor"]),
                            categoria=dados["categoria"],
                            descricao=dados["descricao"],
                            criado=datetime.fromisoformat(dados["criado"]),
                        ),
                        False,
                    )
            except Exception as e:
                logger.warning("Falha ao obter sessão do Valkey (%s).", e)

        pendencia = self._sessoes_memoria.get(telefone)
        if not pendencia:
            return None, False

        agora = datetime.now(timezone.utc)
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
            "sim", "s", "pode", "isso", "claro", "confirmo", "correto",
            "pode ser", "anota", "ok", "okay", "blz", "beleza", "esta certo",
            "ta certo", "com certeza", "anota ai", "pode sim", "sim pode",
            "sim pode anotar", "sim anota",
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
            "nao", "n", "cancela", "cancelar", "errei", "errado",
            "espera", "parar", "deixa", "esquece", "nem pensar",
        }
        
        if norm in negativos:
            return True

        if re.match(r"^(?:nao|n|cancela|cancelar|errei|errado)\b", norm):
            return True
        
        return False

sessao_assistente = GerenciadorSessao()
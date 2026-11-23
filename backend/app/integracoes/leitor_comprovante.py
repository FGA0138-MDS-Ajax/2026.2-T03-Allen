"""Adaptadores da leitura de fotos de comprovantes (RF14).

A imagem só passa pela memória: não é gravada em disco, no banco nem no log (LGPD).
"""

import base64
import logging

import anthropic
from pydantic import BaseModel, Field

from app.modulos.assistente.extrator import CATEGORIAS
from app.nucleo.config import AdaptadorLeitorComprovante, settings
from app.nucleo.portas import (
    FalhaLeituraComprovante,
    LeituraComprovante,
    PortaLeitorComprovante,
)

logger = logging.getLogger(__name__)

TIPOS_MIME_ACEITOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}

INSTRUCOES = (
    "Você lê fotos enviadas por pessoas idosas no WhatsApp para um app de finanças "
    "pessoais. A foto pode ser um comprovante de pagamento, um Pix, uma nota fiscal, "
    "um cupom ou uma conta de consumo (luz, água, gás, internet).\n\n"
    "Extraia:\n"
    "- valor_centavos: o valor total pago ou recebido, em centavos (R$ 35,90 = 3590). "
    "Em nota ou cupom, use o total a pagar, não o de um item. Use null se não "
    "estiver legível ou se houver dúvida entre valores.\n"
    "- tipo: GASTO se o dinheiro saiu da pessoa (compra, pagamento, conta, Pix "
    "enviado), RECEITA se entrou (Pix recebido, depósito, benefício), ou "
    "DESCONHECIDO se não der para saber.\n"
    "- categoria: uma das opções da lista, ou DESCONHECIDA se nenhuma servir.\n"
    "- descricao: até 60 caracteres, como o estabelecimento ou a conta "
    '(ex.: "Drogaria São Paulo", "Conta de luz"). Vazio se não houver.\n\n'
    "Se a foto não for de um comprovante, nota ou conta, devolva valor_centavos null, "
    "tipo DESCONHECIDO e categoria DESCONHECIDA. Nunca invente um valor."
)


class _Leitura(BaseModel):
    valor_centavos: int | None
    tipo: str = Field(description="GASTO, RECEITA ou DESCONHECIDO")
    categoria: str = Field(
        description="Uma de: " + ", ".join(CATEGORIAS) + " ou DESCONHECIDA"
    )
    descricao: str


def _limpar(leitura: _Leitura) -> LeituraComprovante:
    """Descarta o que não faz sentido em vez de confiar cegamente na resposta."""
    valor = leitura.valor_centavos
    tipo = leitura.tipo.upper() if leitura.tipo.upper() in {"GASTO", "RECEITA"} else ""
    return LeituraComprovante(
        valor=valor if valor is not None and valor > 0 else None,
        tipo=tipo,
        categoria=leitura.categoria if leitura.categoria in CATEGORIAS else "",
        descricao=leitura.descricao.strip()[:60],
    )


class LeitorComprovanteFalso:
    """Para desenvolvimento e testes: não lê nada, então o assistente pede todos os
    dados à pessoa (RF16)."""

    async def ler(
        self, imagem: bytes, tipo_mime: str, legenda: str | None
    ) -> LeituraComprovante:
        logger.warning("Foto não lida (leitor falso, apenas para desenvolvimento)")
        return LeituraComprovante()


class LeitorComprovanteClaude:
    def __init__(self) -> None:
        self._cliente = anthropic.AsyncAnthropic(
            api_key=settings.AI_API_KEY,
            timeout=settings.AI_TIMEOUT_SEGUNDOS,
            # Uma nova tentativa estouraria o tempo do RNF04: na falha, o assistente
            # já pede os dados à pessoa
            max_retries=0,
        )

    async def ler(
        self, imagem: bytes, tipo_mime: str, legenda: str | None
    ) -> LeituraComprovante:
        if tipo_mime not in TIPOS_MIME_ACEITOS:
            raise FalhaLeituraComprovante(f"Formato de imagem não aceito: {tipo_mime}")

        conteudo: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": tipo_mime,
                    "data": base64.standard_b64encode(imagem).decode("ascii"),
                },
            }
        ]
        if legenda:
            conteudo.append(
                {"type": "text", "text": f"Legenda enviada com a foto: {legenda}"}
            )
        else:
            conteudo.append({"type": "text", "text": "Leia esta foto."})

        try:
            resposta = await self._cliente.messages.parse(
                model=settings.AI_MODELO,
                max_tokens=1024,
                system=INSTRUCOES,
                # Tarefa simples e com prazo curto (RNF04)
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": conteudo}],
                output_format=_Leitura,
            )
        except anthropic.APIConnectionError as erro:
            # Inclui o tempo esgotado (APITimeoutError)
            raise FalhaLeituraComprovante(
                "Sem resposta do serviço de leitura"
            ) from erro
        except anthropic.APIStatusError as erro:
            raise FalhaLeituraComprovante(
                f"Serviço de leitura respondeu {erro.status_code}"
            ) from erro

        if resposta.stop_reason == "refusal" or resposta.parsed_output is None:
            raise FalhaLeituraComprovante("Leitura recusada ou incompleta")
        return _limpar(resposta.parsed_output)


def obter_leitor_comprovante() -> PortaLeitorComprovante:
    """Entrega o adaptador escolhido no LEITOR_COMPROVANTE."""
    if settings.LEITOR_COMPROVANTE == AdaptadorLeitorComprovante.CLAUDE:
        return LeitorComprovanteClaude()
    return LeitorComprovanteFalso()

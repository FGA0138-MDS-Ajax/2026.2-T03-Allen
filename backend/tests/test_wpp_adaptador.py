"""#152: o adaptador "api" envia de verdade pela Evolution API."""

import httpx
import pytest

from app.integracoes import wpp
from app.nucleo.config import AdaptadorWhatsApp, settings
from app.nucleo.portas import FalhaEnvioWhatsApp


def test_envia_pela_evolution_api(monkeypatch):
    chamadas = []

    def post(url, json, headers, timeout):
        chamadas.append((url, json, headers))
        return httpx.Response(201, request=httpx.Request("POST", url))

    monkeypatch.setattr(wpp.httpx, "post", post)

    wpp.WppApi().enviar(
        "5561990000174@s.whatsapp.net", "Lembrete", "Sua conta vence hoje"
    )

    url, corpo, cabecalhos = chamadas[0]
    assert url == (
        f"{settings.EVOLUTION_URL}/message/sendText/{settings.INSTANCE_NAME}"
    )
    assert corpo == {"number": "5561990000174", "text": "Sua conta vence hoje"}
    assert cabecalhos == {"apikey": settings.AUTHENTICATION_API_KEY}


@pytest.mark.parametrize(
    "falha",
    [
        lambda url: httpx.Response(500, request=httpx.Request("POST", url)),
        lambda url: (_ for _ in ()).throw(httpx.ConnectError("fora do ar")),
    ],
)
def test_falha_vira_falha_de_envio(monkeypatch, falha):
    """A tarefa conta como não enviado em vez de dizer que mandou."""
    monkeypatch.setattr(wpp.httpx, "post", lambda url, **_: falha(url))

    with pytest.raises(FalhaEnvioWhatsApp):
        wpp.WppApi().enviar("5561990000174@s.whatsapp.net", "Lembrete", "texto")


def test_obter_whatsapp_escolhe_pelo_env(monkeypatch):
    monkeypatch.setattr(settings, "ENVIO_WHATSAPP", AdaptadorWhatsApp.API)
    assert isinstance(wpp.obter_whatsapp(), wpp.WppApi)
    monkeypatch.setattr(settings, "ENVIO_WHATSAPP", AdaptadorWhatsApp.FALSO)
    assert isinstance(wpp.obter_whatsapp(), wpp.WhatsAppFalso)

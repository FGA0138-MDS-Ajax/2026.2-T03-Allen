"""Testes do processamento de áudio no assistente do WhatsApp (RF13, RNF04, LGPD)."""

import asyncio
import base64
import io
import sys
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import app.modulos.assistente.audio as audio_module
import app.modulos.assistente.router as router_module
from app.integracoes.transcricao import AdaptadorWhisper, TranscricaoFalsa
from app.main import app
from app.modulos.assistente import mensagens
from app.modulos.assistente.extrator import TipoTransacao, processar_texto_mensagem
from app.modulos.assistente.sessao import GerenciadorSessao
from app.modulos.transacoes.esquemas import OrigemTransacao
from app.nucleo.config import settings
from app.nucleo.portas import AudioMuitoLongo, FalhaTranscricao

FIXTURES_AUDIO = Path(__file__).parent / "fixtures" / "audios"


@pytest.fixture
def ambiente_audio(monkeypatch):
    sessao = GerenciadorSessao()
    sessao._valkey = None

    mensagens_enviadas: list[str] = []
    registrar = Mock()

    monkeypatch.setattr(router_module, "sessao_assistente", sessao)
    monkeypatch.setattr(
        router_module,
        "buscar_usuario_telefone",
        lambda telefone: type(
            "UsuarioTeste", (), {"id": "usuario-teste", "nome": "Maria"}
        )(),
    )

    async def enviar(destinatario: str, texto: str) -> None:
        mensagens_enviadas.append(texto)

    monkeypatch.setattr(router_module, "enviar_mensagem", enviar)
    monkeypatch.setattr(router_module, "SessaoLocal", lambda: nullcontext(object()))
    monkeypatch.setattr(router_module.servico_transacoes, "registrar", registrar)

    return sessao, mensagens_enviadas, registrar


def _payload_audio(
    audio_bytes: bytes, seconds: int = 4, inline_b64: bool = True
) -> dict:
    msg: dict = {
        "audioMessage": {
            "mimetype": "audio/ogg; codecs=opus",
            "seconds": seconds,
            "ptt": True,
        }
    }
    if inline_b64:
        msg["base64"] = base64.b64encode(audio_bytes).decode("ascii")
    return {
        "key": {
            "id": "MSG-AUDIO-1",
            "remoteJid": "5561999999999@s.whatsapp.net",
            "fromMe": False,
        },
        "message": msg,
    }


def test_rf13_adaptador_whisper_transcreve_e_descarta_buffer(monkeypatch):
    buffers_criados: list[io.BytesIO] = []
    bytes_io_original = io.BytesIO

    class BytesIORastreado(bytes_io_original):
        def __init__(self, initial_bytes: bytes = b"") -> None:
            super().__init__(initial_bytes)
            buffers_criados.append(self)

    monkeypatch.setattr("app.integracoes.transcricao.io.BytesIO", BytesIORastreado)

    chamadas_transcribe: list[dict] = []

    class ModeloFake:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def transcribe(self, audio, **kwargs):
            chamadas_transcribe.append(kwargs)
            return (
                [SimpleNamespace(text="Gastei 35 na farmácia")],
                SimpleNamespace(duration=3.2),
            )

    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        SimpleNamespace(WhisperModel=ModeloFake),
    )
    AdaptadorWhisper._modelos.clear()

    adaptador = AdaptadorWhisper(modelo="small", compute_type="int8")
    audio_bytes = (FIXTURES_AUDIO / "gasto_curto.ogg").read_bytes()

    texto = adaptador.transcrever(audio_bytes)

    assert texto == "Gastei 35 na farmácia"
    assert chamadas_transcribe[0]["language"] == "pt"
    assert chamadas_transcribe[0]["vad_filter"] is True
    assert len(buffers_criados) == 1
    assert buffers_criados[0].closed is True


def test_rf13_adaptador_whisper_rejeita_audio_vazio():
    adaptador = AdaptadorWhisper()
    with pytest.raises(FalhaTranscricao):
        adaptador.transcrever(b"")


def test_rf13_adaptador_whisper_rejeita_audio_longo(monkeypatch):
    class ModeloLongoFake:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def transcribe(self, audio, **kwargs):
            return ([SimpleNamespace(text="teste")], SimpleNamespace(duration=65.0))

    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        SimpleNamespace(WhisperModel=ModeloLongoFake),
    )
    AdaptadorWhisper._modelos.clear()

    adaptador = AdaptadorWhisper(max_duracao_segundos=60)
    audio_bytes = (FIXTURES_AUDIO / "audio_longo.ogg").read_bytes()

    with pytest.raises(AudioMuitoLongo):
        adaptador.transcrever(audio_bytes)


def test_rf13_reutiliza_parser_rf12_e_salva_origem_audio(ambiente_audio):
    sessao, mensagens_enviadas, registrar = ambiente_audio
    audio_bytes = (FIXTURES_AUDIO / "gasto_curto.ogg").read_bytes()
    data = _payload_audio(audio_bytes, seconds=3)

    resultado = asyncio.run(
        audio_module.processar_audio_mensagem(
            "5561999999999@s.whatsapp.net",
            data,
            adaptador_transcricao=TranscricaoFalsa("gastei 35 na farmácia"),
        )
    )

    assert resultado["status"] == "ok"
    assert resultado["duracao_ms"] < 5000
    assert "R$ 35,00" in mensagens_enviadas[-1]
    assert "Farmácia" in mensagens_enviadas[-1]

    pendencia, _ = sessao.obter_pendencia("5561999999999")
    assert pendencia is not None
    assert pendencia.origem == OrigemTransacao.WHATSAPP_AUDIO

    asyncio.run(
        router_module.processar_responder("5561999999999@s.whatsapp.net", "Sim")
    )

    assert registrar.call_count == 1
    dados_salvos = registrar.call_args.kwargs["dados"]
    assert dados_salvos.valor == Decimal("35.00")
    assert dados_salvos.origem == OrigemTransacao.WHATSAPP_AUDIO


def test_rf13_baixa_audio_via_evolution_api(monkeypatch, ambiente_audio):
    _, mensagens_enviadas, _ = ambiente_audio
    audio_bytes = (FIXTURES_AUDIO / "gasto_ruido.ogg").read_bytes()
    b64_esperado = base64.b64encode(audio_bytes).decode("ascii")

    class RespostaHttpFake:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"base64": b64_esperado}

    class AsyncClientFake:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            assert "/chat/getBase64FromMediaMessage/" in url
            return RespostaHttpFake()

    monkeypatch.setattr(audio_module.httpx, "AsyncClient", AsyncClientFake)

    data = _payload_audio(audio_bytes, seconds=4, inline_b64=False)
    resultado = asyncio.run(
        audio_module.processar_audio_mensagem(
            "5561999999999@s.whatsapp.net",
            data,
            adaptador_transcricao=TranscricaoFalsa("gastei 50 no mercado"),
        )
    )

    assert resultado["status"] == "ok"
    assert "R$ 50,00" in mensagens_enviadas[-1]
    assert "Alimentação" in mensagens_enviadas[-1]


def test_rf13_audio_muito_longo_retorna_mensagem_simples(ambiente_audio):
    _, mensagens_enviadas, registrar = ambiente_audio
    audio_bytes = (FIXTURES_AUDIO / "audio_longo.ogg").read_bytes()
    data = _payload_audio(audio_bytes, seconds=65)

    resultado = asyncio.run(
        audio_module.processar_audio_mensagem(
            "5561999999999@s.whatsapp.net",
            data,
            adaptador_transcricao=TranscricaoFalsa("gastei 35 na farmácia"),
        )
    )

    assert resultado["status"] == "audio_muito_longo"
    assert mensagens_enviadas[-1] == mensagens.audio_muito_longo()
    assert registrar.call_count == 0


def test_rf13_falha_transcricao_retorna_mensagem_simples(ambiente_audio):
    _, mensagens_enviadas, registrar = ambiente_audio
    data = _payload_audio(b"corrompido", seconds=2)

    class AdaptadorQueFalha:
        def transcrever(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
            raise FalhaTranscricao("ruído excessivo")

    resultado = asyncio.run(
        audio_module.processar_audio_mensagem(
            "5561999999999@s.whatsapp.net",
            data,
            adaptador_transcricao=AdaptadorQueFalha(),
        )
    )

    assert resultado["status"] == "falha_transcricao"
    assert mensagens_enviadas[-1] == mensagens.audio_nao_compreendido()
    assert registrar.call_count == 0


def test_rf13_lgpd_nao_persiste_audio_em_disco(tmp_path, monkeypatch, ambiente_audio):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    sessao, _, _ = ambiente_audio
    audio_bytes = (FIXTURES_AUDIO / "gasto_curto.ogg").read_bytes()
    data = _payload_audio(audio_bytes, seconds=3)

    asyncio.run(
        audio_module.processar_audio_mensagem(
            "5561999999999@s.whatsapp.net",
            data,
            adaptador_transcricao=TranscricaoFalsa("gastei 35 na farmácia"),
        )
    )

    assert list(tmp_path.iterdir()) == []
    pendencia, _ = sessao.obter_pendencia("5561999999999")
    assert pendencia is not None
    assert not hasattr(pendencia, "audio_bytes")


@pytest.mark.parametrize(
    ("transcricao", "tipo_esperado", "valor_esperado", "categoria_esperada"),
    [
        ("gastei 35 na farmácia", TipoTransacao.GASTO, 3500, "Farmácia"),
        ("ô moço, paguei 120 de luz viu", TipoTransacao.GASTO, 12000, "Moradia"),
        (
            "é... comprei pão por 6,50 lá na padaria",
            TipoTransacao.GASTO,
            650,
            "Alimentação",
        ),
        ("deu 45 na feira hoje de manhã", TipoTransacao.GASTO, 4500, "Alimentação"),
        ("paguei 25 de uber pro médico", TipoTransacao.GASTO, 2500, "Transporte"),
        (
            "recebi 1500 da aposentadoria",
            TipoTransacao.RECEITA,
            150000,
            "Aposentadoria",
        ),
        (
            "caiu o benefício do INSS de 1412",
            TipoTransacao.RECEITA,
            141200,
            "Aposentadoria",
        ),
        ("gastei 18,50 na drogaria", TipoTransacao.GASTO, 1850, "Farmácia"),
        ("paguei 80 no dentista", TipoTransacao.GASTO, 8000, "Saúde"),
        ("ganhei 150 de bico hoje", TipoTransacao.RECEITA, 15000, "Renda Extra"),
    ],
)
def test_rf13_conjunto_audios_sotaques_e_ruido(
    transcricao: str,
    tipo_esperado: TipoTransacao,
    valor_esperado: int,
    categoria_esperada: str,
):
    resultado = processar_texto_mensagem(transcricao)

    assert resultado.sucesso is True
    assert resultado.tipo == tipo_esperado
    assert resultado.valor == valor_esperado
    assert resultado.categoria == categoria_esperada


def test_rf13_latencia_medida_rnf04(ambiente_audio):
    audio_bytes = (FIXTURES_AUDIO / "gasto_ruido.ogg").read_bytes()
    data = _payload_audio(audio_bytes, seconds=4)
    tempos_ms: list[float] = []

    for _ in range(10):
        resultado = asyncio.run(
            audio_module.processar_audio_mensagem(
                "5561999999999@s.whatsapp.net",
                data,
                adaptador_transcricao=TranscricaoFalsa("gastei 35 na farmácia"),
            )
        )
        tempos_ms.append(resultado["duracao_ms"])

    tempos_ms.sort()
    p95 = tempos_ms[int(0.95 * (len(tempos_ms) - 1))]
    assert p95 <= 5000.0


def test_rf13_webhook_dispara_aviso_imediato_e_enfileira(monkeypatch):
    monkeypatch.setattr(settings, "AUTHENTICATION_API_KEY", "chave-teste")
    avisos: list[str] = []
    enfileirados: list[str] = []

    async def enviar_fake(destinatario: str, texto: str) -> None:
        avisos.append(texto)

    def delay_fake(remetente: str, data: dict) -> None:
        enfileirados.append(remetente)

    monkeypatch.setattr(router_module, "enviar_mensagem", enviar_fake)
    monkeypatch.setitem(
        sys.modules,
        "app.modulos.assistente.tarefas",
        SimpleNamespace(processar_audio_tarefa=SimpleNamespace(delay=delay_fake)),
    )

    audio_bytes = (FIXTURES_AUDIO / "gasto_curto.ogg").read_bytes()
    payload = {
        "event": "messages.upsert",
        "data": _payload_audio(audio_bytes, seconds=3),
    }

    with TestClient(app) as client:
        resposta = client.post(
            "/webhook/whatsapp",
            json=payload,
            headers={"apikey": "chave-teste"},
        )

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "SUCCESS"}
    assert enfileirados == ["5561999999999@s.whatsapp.net"]
    assert avisos == [mensagens.audio_recebido()]

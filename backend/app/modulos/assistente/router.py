import base64
import logging
import secrets
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from sqlalchemy import select

from app.integracoes.leitor_comprovante import obter_leitor_comprovante
from app.modulos.assistente import mensagens
from app.modulos.assistente.audio import processar_audio_mensagem
from app.modulos.assistente.extrator import (
    IntencaoMensagem,
    TipoTransacao,
    eh_saudacao,
    extrair_valor,
    identificar_categoria,
    identificar_tipo_resposta,
    normalizar_texto,
    processar_texto_mensagem,
)
from app.modulos.assistente.sessao import (
    CampoFaltando,
    RegistroPendente,
    normalizar_resposta,
    sessao_assistente,
)
from app.modulos.contas import servico as servico_contas
from app.modulos.identidade.esquemas import normalizar_telefone
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import hash_telefone
from app.modulos.resumo import servico as servico_resumo
from app.modulos.transacoes import servico as servico_transacoes
from app.modulos.transacoes.esquemas import OrigemTransacao, TransacaoRegistroEntrada
from app.modulos.transacoes.esquemas import TipoTransacao as TipoTransacaoBD
from app.nucleo.banco import SessaoLocal
from app.nucleo.config import settings
from app.nucleo.portas import LeituraComprovante

router = APIRouter()
logger = logging.getLogger(__name__)


def enfileirar_processamento_audio(
    remetente: str,
    data: dict,
    background_tasks: BackgroundTasks,
) -> None:
    """Envia a transcrição de áudio para o worker Celery; em dev sem broker, usa BackgroundTasks."""
    try:
        from app.modulos.assistente.tarefas import processar_audio_tarefa

        processar_audio_tarefa.delay(remetente, data)
    except Exception as erro:
        logger.warning(
            "Fila Celery indisponível (%s); processando áudio em background local.",
            type(erro).__name__,
        )
        background_tasks.add_task(processar_audio_mensagem, remetente, data)


@router.post("/webhook/whatsapp")
async def receber_mensagem(
    request: Request,
    background_tasks: BackgroundTasks,
    apikey: str | None = Header(None, alias="apikey"),
):
    payload = await request.json()
    chave_recebida = apikey or payload.get("apikey")

    if not chave_recebida or not secrets.compare_digest(
        chave_recebida, settings.AUTHENTICATION_API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado: API Key inválida ou ausente.",
        )

    event = payload.get("event", "")

    # Filtra apenas mensagens recebidas no evento
    if event == "messages.upsert":
        data = payload.get("data", {})
        key = data.get("key", {})

        remetente = key.get("remoteJid", "")

        # Ignora mensagens enviadas pelo próprio assistente
        if (
            not key.get("fromMe")
            and remetente
            and not remetente.endswith("@broadcast")
            and not remetente.endswith("@g.us")
        ):
            # Extrai o texto ou áudio da mensagem
            message_content = data.get("message", {})
            audio_msg = message_content.get("audioMessage")
            texto = message_content.get("conversation") or message_content.get(
                "extendedTextMessage", {}
            ).get("text")

            if audio_msg:
                duracao = audio_msg.get("seconds")
                if (
                    isinstance(duracao, (int, float))
                    and duracao > settings.AUDIO_MAX_DURACAO_SEGUNDOS
                ):
                    background_tasks.add_task(
                        enviar_mensagem, remetente, mensagens.audio_muito_longo()
                    )
                else:
                    background_tasks.add_task(
                        enviar_mensagem, remetente, mensagens.audio_recebido()
                    )
                    enfileirar_processamento_audio(remetente, data, background_tasks)
            elif texto:
                print("\n[Whatsapp] Mensagem recebida via webhook.")
                # Processa a resposta em background para responder ao webhook
                background_tasks.add_task(processar_responder, remetente, texto)
            elif "imageMessage" in message_content:
                # RF14: foto de comprovante, nota fiscal ou conta
                background_tasks.add_task(processar_foto, remetente, data)

    return {"status": "SUCCESS"}


def buscar_usuario_telefone(telefone: str) -> Usuario | None:
    try:
        tel = normalizar_telefone(telefone)
        hash_tel = hash_telefone(tel)
        with SessaoLocal() as sessao:
            stmt = select(Usuario).where(Usuario.hash_telefone == hash_tel)
            return sessao.scalars(stmt).first()
    except Exception as e:
        print(f"[Aviso] Erro ao buscar usuário no banco: ({e}).")
        return None


async def processar_responder(
    remetente: str,
    texto: str,
    origem: OrigemTransacao = OrigemTransacao.WHATSAPP_TEXTO,
):
    telefone = remetente.split("@")[0] if "@" in remetente else remetente

    usuario = buscar_usuario_telefone(telefone)
    if not usuario:
        resposta = mensagens.usuario_nao_encontrado()
        await enviar_mensagem(remetente, resposta)
        return

    # RF24: "parar resumo" e "voltar resumo" valem a qualquer momento
    resposta_resumo = servico_resumo.tratar_comando(usuario.id, texto)
    if resposta_resumo:
        await enviar_mensagem(remetente, resposta_resumo)
        return

    pendencia, expirou = sessao_assistente.obter_pendencia(telefone)

    if (
        pendencia is None
        and expirou is True
        and (
            sessao_assistente.resposta_sim(texto)
            or sessao_assistente.resposta_nao(texto)
        )
    ):
        await enviar_mensagem(remetente, mensagens.confirmacao_expirada())
        return

    if pendencia and pendencia.faltando:
        # RF16: a mensagem responde ao dado que o assistente pediu
        await enviar_mensagem(
            remetente, completar_lancamento(telefone, pendencia, texto)
        )
        return

    if pendencia:
        if sessao_assistente.resposta_sim(texto):
            resposta = registrar_confirmado(telefone, usuario.id, pendencia)
            await enviar_mensagem(remetente, resposta)
            return

        if sessao_assistente.resposta_nao(texto):
            correcao = processar_texto_mensagem(texto)

            nova_categoria = (
                correcao.categoria
                if correcao.categoria not in {"Outros", "Outras Receitas"}
                else pendencia.categoria
            )

            novo_valor = (
                correcao.valor if correcao.valor is not None else pendencia.valor
            )

            if correcao.valor is not None or nova_categoria != pendencia.categoria:
                sessao_assistente.salvar_pendencia(
                    telefone=telefone,
                    tipo=pendencia.tipo,
                    valor=novo_valor,
                    categoria=nova_categoria,
                    descricao=pendencia.descricao,
                    origem=pendencia.origem,
                )

                if pendencia.tipo == TipoTransacao.RECEITA:
                    resposta = mensagens.confirmacao_renda(novo_valor, nova_categoria)
                else:
                    resposta = mensagens.confirmacao_gasto(novo_valor, nova_categoria)

                await enviar_mensagem(remetente, resposta)
                return

            sessao_assistente.limpar_pendencia(telefone)
            await enviar_mensagem(remetente, mensagens.registro_cancelado())
            return

        sessao_assistente.limpar_pendencia(telefone)

    intencao = processar_texto_mensagem(texto)
    resposta = responder_intencao(telefone, usuario, intencao, origem)
    await enviar_mensagem(remetente, resposta)


def responder_intencao(
    telefone: str,
    usuario: Usuario,
    intencao: IntencaoMensagem,
    origem: OrigemTransacao = OrigemTransacao.WHATSAPP_TEXTO,
) -> str:
    """Pede a confirmação (RF15) ou, se faltou algum dado, explica o motivo em
    linguagem simples e pede só o que falta (RF16)."""
    if intencao.sucesso and intencao.valor is not None:
        return pedir_confirmacao(
            telefone,
            intencao.tipo,
            intencao.valor,
            intencao.categoria,
            intencao.descricao,
            origem,
        )

    if eh_saudacao(intencao.descricao):
        nome_usuario = getattr(usuario, "nome", "") or ""
        primeiro_nome = nome_usuario.split()[0] if nome_usuario.split() else None
        return mensagens.boas_vindas(primeiro_nome)

    if intencao.motivo_recusa == "futuro":
        return mensagens.explicar_futuro()

    if intencao.motivo_recusa == "multiplas_transacoes":
        return mensagens.explicar_varios_valores()

    if intencao.motivo_recusa == "sem_valor":
        sessao_assistente.salvar_pendencia(
            telefone=telefone,
            tipo=intencao.tipo,
            valor=None,
            categoria=intencao.categoria,
            descricao=intencao.descricao,
            faltando=CampoFaltando.VALOR,
            origem=origem,
        )
        return mensagens.pedir_valor(
            intencao.tipo == TipoTransacao.RECEITA, intencao.categoria
        )

    return mensagens.mensagem_nao_compreendida()


def pedir_confirmacao(
    telefone: str,
    tipo: TipoTransacao,
    valor: int,
    categoria: str,
    descricao: str,
    origem: OrigemTransacao = OrigemTransacao.WHATSAPP_TEXTO,
) -> str:
    sessao_assistente.salvar_pendencia(
        telefone=telefone,
        tipo=tipo,
        valor=valor,
        categoria=categoria,
        descricao=descricao,
        origem=origem,
    )
    if tipo == TipoTransacao.RECEITA:
        return mensagens.confirmacao_renda(valor, categoria)
    return mensagens.confirmacao_gasto(valor, categoria)


def quer_cancelar(texto: str) -> bool:
    return normalizar_resposta(texto) in PALAVRAS_CANCELAR


PALAVRAS_CANCELAR = {
    "cancelar",
    "cancela",
    "esquece",
    "deixa",
    "deixa pra la",
    "desisto",
    "nao",
    "n",
    "parar",
}


def proximo_faltando(pendencia: RegistroPendente) -> CampoFaltando | None:
    """Ordem das perguntas: valor, depois se foi gasto ou entrada, depois com o quê.
    Categoria vazia quer dizer que ninguém a identificou (ex.: foto ilegível)."""
    if pendencia.valor is None:
        return CampoFaltando.VALOR
    if pendencia.tipo == TipoTransacao.DESCONHECIDO:
        return CampoFaltando.TIPO
    if not pendencia.categoria:
        return CampoFaltando.CATEGORIA
    return None


def completar_lancamento(telefone: str, pendencia: RegistroPendente, texto: str) -> str:
    """RF16: preenche o dado que faltava com a resposta da pessoa. Se ela não
    responder o que foi pedido, o assistente pergunta de novo em vez de descartar o
    lançamento; só desiste quando a pessoa pede para cancelar."""
    if quer_cancelar(texto):
        sessao_assistente.limpar_pendencia(telefone)
        return mensagens.registro_cancelado()

    campo = pendencia.faltando
    tipo, valor, categoria = pendencia.tipo, pendencia.valor, pendencia.categoria

    if campo == CampoFaltando.VALOR:
        valor, _ = extrair_valor(texto)
        if valor is None:
            _manter_rascunho(telefone, pendencia)
            return mensagens.valor_ainda_nao_entendido()
    elif campo == CampoFaltando.TIPO:
        tipo = identificar_tipo_resposta(texto)
        if tipo == TipoTransacao.DESCONHECIDO:
            _manter_rascunho(telefone, pendencia)
            return mensagens.tipo_ainda_nao_entendido()
    elif campo == CampoFaltando.CATEGORIA:
        # Sem palavra conhecida, fica em "Outros": a pessoa já disse o que foi
        categoria = identificar_categoria(normalizar_texto(texto), tipo)

    atualizada = RegistroPendente(
        tipo=tipo,
        valor=valor,
        categoria=categoria,
        descricao=pendencia.descricao or texto.strip(),
        criado=pendencia.criado,
        origem=pendencia.origem,
    )
    falta = proximo_faltando(atualizada)
    if falta is None:
        return pedir_confirmacao(
            telefone, tipo, valor, categoria, atualizada.descricao, atualizada.origem
        )

    atualizada.faltando = falta
    _manter_rascunho(telefone, atualizada)
    return _pergunta(atualizada)


def _pergunta(pendencia: RegistroPendente, motivo: str | None = None) -> str:
    receita = pendencia.tipo == TipoTransacao.RECEITA
    if pendencia.faltando == CampoFaltando.VALOR:
        desconhecido = pendencia.tipo == TipoTransacao.DESCONHECIDO
        return mensagens.pedir_valor(
            None if desconhecido else receita, pendencia.categoria, motivo
        )
    if pendencia.faltando == CampoFaltando.TIPO:
        return mensagens.pedir_tipo(pendencia.valor, motivo)
    return mensagens.pedir_categoria(receita, pendencia.valor, motivo)


def _manter_rascunho(telefone: str, pendencia: RegistroPendente) -> None:
    sessao_assistente.salvar_pendencia(
        telefone=telefone,
        tipo=pendencia.tipo,
        valor=pendencia.valor,
        categoria=pendencia.categoria,
        descricao=pendencia.descricao,
        faltando=pendencia.faltando,
        origem=pendencia.origem,
    )


# Categoria do assistente -> categoria do app (tblCategoria), para o gasto aparecer
# por categoria no Extrato e no resumo (#138). Entradas não têm categoria no app.
CATEGORIA_NO_APP = {
    "Farmácia": "Saúde",
    "Saúde": "Saúde",
    "Alimentação": "Alimentação",
    "Transporte": "Transporte",
    "Moradia": "Moradia",
    "Lazer": "Lazer",
    "Outros": "Outros",
}


def _categoria_do_app(sessao_db, pendencia: RegistroPendente) -> int | None:
    if pendencia.tipo != TipoTransacao.GASTO:
        return None
    nome = CATEGORIA_NO_APP.get(pendencia.categoria)
    if nome is None:
        return None
    try:
        return servico_contas.id_da_categoria(sessao_db, nome)
    except Exception:
        # A categoria é opcional: sem ela, o gasto é gravado do mesmo jeito
        logger.warning("Categoria do assistente não encontrada no app")
        return None


def registrar_confirmado(
    telefone: str, usuario_id: uuid.UUID, pendencia: RegistroPendente
) -> str:
    """Grava o lançamento confirmado. Se o banco falhar, avisa e guarda a pendência
    para a pessoa tentar de novo: nada é perdido em silêncio (RF16)."""
    tipo_bd = (
        TipoTransacaoBD.ENTRADA
        if pendencia.tipo == TipoTransacao.RECEITA
        else TipoTransacaoBD.SAIDA
    )
    valor_decimal = Decimal(pendencia.valor) / Decimal(100)

    try:
        with SessaoLocal() as sessao_db:
            servico_transacoes.registrar(
                sessao=sessao_db,
                usuario_id=usuario_id,
                dados=TransacaoRegistroEntrada(
                    tipo=tipo_bd,
                    valor=valor_decimal,
                    origem=OrigemTransacao(pendencia.origem),
                    descricao=pendencia.descricao or pendencia.categoria,
                    categoria_id=_categoria_do_app(sessao_db, pendencia),
                ),
            )
    except servico_transacoes.TransacaoJaRegistrada:
        pass
    except Exception:
        # Sem valor nem texto da mensagem no log (RNF05)
        logger.exception("Falha ao registrar transação do assistente")
        _manter_rascunho(telefone, pendencia)
        return mensagens.falha_ao_salvar()

    sessao_assistente.limpar_pendencia(telefone)
    if pendencia.tipo == TipoTransacao.RECEITA:
        return mensagens.confirmacao_sucesso_renda(pendencia.valor, pendencia.categoria)
    return mensagens.confirmacao_sucesso_gasto(pendencia.valor, pendencia.categoria)


# RF14: fotos de comprovantes

# Motivo dito à pessoa quando a foto não trouxe o dado (RF16)
MOTIVOS_FOTO = {
    CampoFaltando.VALOR: "Não consegui ler o valor na foto.",
    CampoFaltando.TIPO: "Não consegui saber pela foto se o dinheiro saiu ou entrou.",
    CampoFaltando.CATEGORIA: "Não consegui saber pela foto com o que foi.",
}


async def processar_foto(remetente: str, dados_mensagem: dict) -> None:
    """Lê a foto e pede a confirmação (RF15). O que a foto não trouxe, o assistente
    pede à pessoa (RF16). A imagem fica só na memória e é descartada no fim (LGPD)."""
    telefone = remetente.split("@")[0] if "@" in remetente else remetente

    usuario = buscar_usuario_telefone(telefone)
    if not usuario:
        await enviar_mensagem(remetente, mensagens.usuario_nao_encontrado())
        return

    # Uma foto nova substitui o que estava pendente, como uma mensagem de texto nova
    sessao_assistente.limpar_pendencia(telefone)

    imagem_msg = dados_mensagem.get("message", {}).get("imageMessage", {})
    legenda = (imagem_msg.get("caption") or "").strip() or None
    inicio = time.perf_counter()
    leitura = LeituraComprovante()
    try:
        imagem, tipo_mime = await baixar_imagem(dados_mensagem)
        leitura = await obter_leitor_comprovante().ler(imagem, tipo_mime, legenda)
    except Exception as erro:
        # Sem o conteúdo da foto no log (RNF05)
        logger.warning("Foto não lida: %s", erro.__class__.__name__)
    # RNF04: resposta em até 5 s. Medido desde a S4 (só o tempo, sem dados no log)
    logger.info("Foto processada em %.2f s", time.perf_counter() - inicio)

    await enviar_mensagem(remetente, responder_leitura(telefone, leitura, legenda))


def responder_leitura(
    telefone: str, leitura: LeituraComprovante, legenda: str | None = None
) -> str:
    tipo = TipoTransacao(leitura.tipo) if leitura.tipo else TipoTransacao.DESCONHECIDO
    if not leitura.categoria and legenda:
        # A legenda ("remédio", "mercado") diz com o que foi quando a foto não diz
        pela_legenda = identificar_categoria(normalizar_texto(legenda), tipo)
        if pela_legenda not in {"Outros", "Outras Receitas"}:
            leitura.categoria = pela_legenda
    pendencia = RegistroPendente(
        tipo=tipo,
        valor=leitura.valor,
        categoria=leitura.categoria,
        descricao=leitura.descricao,
        criado=datetime.now(UTC),
        origem=OrigemTransacao.WHATSAPP_FOTO,
    )
    falta = proximo_faltando(pendencia)
    if falta is None:
        return pedir_confirmacao(
            telefone,
            pendencia.tipo,
            pendencia.valor,
            pendencia.categoria,
            pendencia.descricao,
            pendencia.origem,
        )

    pendencia.faltando = falta
    _manter_rascunho(telefone, pendencia)
    return _pergunta(pendencia, MOTIVOS_FOTO[falta])


async def baixar_imagem(dados_mensagem: dict) -> tuple[bytes, str]:
    """Pega a foto da mensagem: no próprio webhook, se a Evolution API manda o base64
    (WEBHOOK_BASE64=true), ou pedindo à Evolution API."""
    imagem_msg = dados_mensagem.get("message", {}).get("imageMessage", {})
    tipo_mime = (imagem_msg.get("mimetype") or "image/jpeg").split(";")[0].strip()

    conteudo = dados_mensagem.get("message", {}).get("base64")
    if not conteudo:
        url = (
            f"{settings.EVOLUTION_URL}/chat/getBase64FromMediaMessage/"
            f"{settings.INSTANCE_NAME}"
        )
        corpo = {"message": {"key": dados_mensagem.get("key", {})}}
        async with httpx.AsyncClient() as client:
            resposta = await client.post(
                url,
                json=corpo,
                headers={"apikey": settings.AUTHENTICATION_API_KEY},
                timeout=5.0,
            )
            resposta.raise_for_status()
            json_resposta = resposta.json()
        conteudo = json_resposta.get("base64")
        tipo_mime = json_resposta.get("mimetype") or tipo_mime

    if not conteudo:
        raise ValueError("Mensagem sem imagem")
    if conteudo.startswith("data:"):
        conteudo = conteudo.split(",", 1)[1]
    return base64.b64decode(conteudo), tipo_mime


async def enviar_mensagem(destinatario: str, texto: str):
    headers = {
        "apikey": settings.AUTHENTICATION_API_KEY,
        "Content-Type": "application/json",
    }

    numero = destinatario.split("@")[0] if "@" in destinatario else destinatario

    body = {"number": numero, "text": texto}

    # Tenta a URL configurada e alterna entre localhost e evolution-api para funcionar tanto localmente quanto no Docker
    urls = [f"{settings.EVOLUTION_URL}/message/sendText/{settings.INSTANCE_NAME}"]
    if "localhost" in settings.EVOLUTION_URL:
        urls.append(
            f"{settings.EVOLUTION_URL.replace('localhost', 'evolution-api')}/message/sendText/{settings.INSTANCE_NAME}"
        )
    elif "evolution-api" in settings.EVOLUTION_URL:
        urls.append(
            f"{settings.EVOLUTION_URL.replace('evolution-api', 'localhost')}/message/sendText/{settings.INSTANCE_NAME}"
        )

    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.post(
                    url, json=body, headers=headers, timeout=10.0
                )
                response.raise_for_status()
                print(f"[Whatsapp] Resposta enviada com sucesso via {url}.")
                return
            except Exception as e:
                print(f"[Erro de envio] Falha ao enviar mensagem via {url}: {e}")

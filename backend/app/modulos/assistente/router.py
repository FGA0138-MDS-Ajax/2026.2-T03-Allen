from fastapi import APIRouter, Request, BackgroundTasks, Header, HTTPException, status
import httpx
import re
import secrets
from sqlalchemy import select
from decimal import Decimal 

from app.nucleo.config import settings
from app.modulos.assistente.extrator import TipoTransacao, eh_saudacao, processar_texto_mensagem
from app.modulos.assistente import mensagens
from app.modulos.assistente.sessao import sessao_assistente
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.esquemas import normalizar_telefone
from app.modulos.identidade.seguranca import hash_telefone
from app.modulos.transacoes import servico as servico_transacoes
from app.modulos.transacoes.esquemas import (
    OrigemTransacao,
    TipoTransacao as TipoTransacaoBD,
    TransacaoRegistroEntrada
)
from app.nucleo.banco import SessaoLocal

router = APIRouter()

@router.post("/webhook/whatsapp")
async def receber_mensagem(
    request: Request,
    background_tasks: BackgroundTasks,
    apikey: str | None = Header(None, alias="apikey"),
):
    payload = await request.json()
    chave_recebida = apikey or payload.get("apikey")

    if not chave_recebida or not secrets.compare_digest(chave_recebida, settings.AUTHENTICATION_API_KEY):
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
        if not key.get("fromMe") and remetente and not remetente.endswith("@broadcast") and not remetente.endswith("@g.us"):

            # Extrai o texto da mensagem
            message_content = data.get("message", {})
            texto = (
                message_content.get("conversation") or
                message_content.get("extendedTextMessage", {}).get("text")
            )

            if texto:
                print(f"\n[Whatsapp] Mensagem recebida via webhook.")
                # Processa a resposta em background para responder ao webhook
                background_tasks.add_task(processar_responder, remetente, texto)

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

async def processar_responder(remetente: str, texto: str):
    telefone = remetente.split("@")[0] if "@" in remetente else remetente

    usuario = buscar_usuario_telefone(telefone)
    if not usuario:
        resposta = mensagens.usuario_nao_encontrado()
        await enviar_mensagem(remetente, resposta)
        return

    pendencia, expirou = sessao_assistente.obter_pendencia(telefone)

    if pendencia is None and expirou is True and (sessao_assistente.resposta_sim(texto) or sessao_assistente.resposta_nao(texto)):
        await enviar_mensagem(remetente, mensagens.confirmacao_expirada())
        return
    
    if pendencia:
        if sessao_assistente.resposta_sim(texto):
            sessao_assistente.limpar_pendencia(telefone)

            # Mapeia o tipo de transação do assistente para o tipo do banco
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
                        usuario_id=usuario.id,
                        dados=TransacaoRegistroEntrada(
                            tipo=tipo_bd,
                            valor=valor_decimal,
                            origem=OrigemTransacao.WHATSAPP_TEXTO,
                            descricao=pendencia.descricao or pendencia.categoria,
                        ),
                    )
            except Exception as e:
                print(f"[Erro] Falha ao registrar transação no banco: {e}")

            if pendencia.tipo == TipoTransacao.RECEITA:
                resposta = mensagens.confirmacao_sucesso_renda(pendencia.valor, pendencia.categoria)
            else:
                resposta = mensagens.confirmacao_sucesso_gasto(pendencia.valor, pendencia.categoria)
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
                correcao.valor
                if correcao.valor is not None
                else pendencia.valor
            )

            if correcao.valor is not None or nova_categoria != pendencia.categoria:
                sessao_assistente.salvar_pendencia(
                    telefone=telefone,
                    tipo=pendencia.tipo,
                    valor=novo_valor,
                    categoria=nova_categoria,
                    descricao=pendencia.descricao,
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

    if not intencao.sucesso or intencao.valor is None:
        if eh_saudacao(texto):
            nome_usuario = getattr(usuario, "nome", "") or ""
            primeiro_nome = nome_usuario.split()[0] if nome_usuario.split() else None
            resposta = mensagens.boas_vindas(primeiro_nome)
        else:
            resposta = mensagens.mensagem_nao_compreendida()
    else:
        sessao_assistente.salvar_pendencia(
            telefone = telefone,
            tipo = intencao.tipo,
            valor = intencao.valor,
            categoria = intencao.categoria,
            descricao = intencao.descricao,
        )
        if intencao.tipo == TipoTransacao.RECEITA:
            resposta = mensagens.confirmacao_renda(intencao.valor, intencao.categoria)
        else:
            resposta = mensagens.confirmacao_gasto(intencao.valor, intencao.categoria)
    
    await enviar_mensagem(remetente, resposta)

async def enviar_mensagem(destinatario: str, texto: str):
    headers = {
        "apikey": settings.AUTHENTICATION_API_KEY,
        "Content-Type": "application/json"
    }

    numero = destinatario.split("@")[0] if "@" in destinatario else destinatario

    body = {
        "number": numero,
        "text": texto
    }

    # Tenta a URL configurada e alterna entre localhost e evolution-api para funcionar tanto localmente quanto no Docker
    urls = [f"{settings.EVOLUTION_URL}/message/sendText/{settings.INSTANCE_NAME}"]
    if "localhost" in settings.EVOLUTION_URL:
        urls.append(f"{settings.EVOLUTION_URL.replace('localhost', 'evolution-api')}/message/sendText/{settings.INSTANCE_NAME}")
    elif "evolution-api" in settings.EVOLUTION_URL:
        urls.append(f"{settings.EVOLUTION_URL.replace('evolution-api', 'localhost')}/message/sendText/{settings.INSTANCE_NAME}")

    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.post(url, json=body, headers=headers, timeout=10.0)
                response.raise_for_status()
                print(f"[Whatsapp] Resposta enviada com sucesso via {url}.")
                return
            except Exception as e:
                print(f"[Erro de envio] Falha ao enviar mensagem via {url}: {e}")

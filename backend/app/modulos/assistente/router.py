from fastapi import APIRouter, Request, BackgroundTasks, Header, HTTPException, status
import httpx
from sqlalchemy import select

from app.nucleo.config import settings
from app.modulos.assistente.mensagens import mensagem_nao_compreendida
from app.modulos.assistente.mensagens import usuario_nao_encontrado
from app.modulos.assistente.extrator import TipoTransacao, processar_texto_mensagem
from app.modulos.assistente import mensagens
from app.modulos.assistente.sessao import sessao_assistente
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.esquemas import normalizar_telefone
from app.modulos.identidade.seguranca import hash_telefone
from app.nucleo.banco import SessaoLocal

router = APIRouter()

@router.post("/webhook/whatsapp")
async def receber_mensagem(
    request: Request,
    background_tasks: BackgroundTasks,
    apikey: str | None = Header(None, alias="apikey")
):
    payload = await request.json()
    chave_recebida = apikey or payload.get("apikey") or request.query_params.get("apikey")

    if not chave_recebida or chave_recebida != settings.AUTHENTICATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado: API Key inválida ou ausente."
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
                print(f"\n[Whatsapp] Mensagem de {remetente}: {texto}")
                # Processa a resposta em background para responder ao webhook
                background_tasks.add_task(processar_responder, remetente, texto)

    return {"status": "SUCCESS"}

def buscar_usuario_telefone(telefone: str) -> Usuario | None:
    try:
        telefone_normalizado = normalizar_telefone(telefone)
        hash_telefone = hash_telefone(telefone_normalizado)
        with SessaoLocal() as sessao:
            stmt = select(Usuario).where(Usuario.telefone == hash_telefone)
            return sessao.scalars(stmt).first()
    except Exception as e:
        print(f"[Aviso] Erro ao buscar usuário no banco: ({e}).")
        return None

async def processar_responder(remetente: str, texto: str):
    telefone = remetente.split("@")[0] if "@" in remetente else remetente

    usuario = buscar_usuario_telefone(telefone)
    if not usuario:
        resposta = usuario_nao_encontrado()
        await enviar_mensagem(remetente, resposta)
        return

    pendencia, expirou = sessao_assistente.obter_pendencia(telefone)

    if expirou:
        await enviar_mensagem(remetente, mensagens.confirmacao_expirada())
        return

    if pendencia:
        if sessao_assistente.resposta_sim(texto):
            sessao_assistente.limpar_pendencia(telefone)
            if pendencia.tipo == TipoTransacao.RECEITA:
                resposta = mensagens.confirmacao_sucesso_renda(pendencia.valor, pendencia.categoria)
            else:
                resposta = mensagens.confirmacao_sucesso_gasto(pendencia.valor, pendencia.categoria)
            await enviar_mensagem(remetente, resposta)
            return

        if sessao_assistente.resposta_nao(texto):
            sessao_assistente.limpar_pendencia(telefone)
            await enviar_mensagem(remetente, mensagens.registro_cancelado())
            return

        sessao_assistente.limpar_pendencia(telefone)

    intencao = processar_texto_mensagem(texto)

    if not intencao.sucesso or intencao.valor is None:
        resposta = mensagem_nao_compreendida()
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
                print(f"[Whatsapp] Resposta enviada com sucesso para {numero}")
                return
            except Exception as e:
                print(f"[Erro de envio] Falha ao enviar mensagem para {numero} via {url}: {e}")

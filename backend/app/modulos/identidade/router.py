from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.modulos.identidade import servico
from app.modulos.identidade.esquemas import (
    CadastroEntrada,
    LoginPinEntrada,
    TokenSaida,
    UsuarioSaida,
)
from app.modulos.identidade.mensagens import Message
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token
from app.modulos.identidade.servico import Attempts
from app.nucleo.banco import obter_sessao

router = APIRouter(prefix="/api/v1/auth", tags=["autenticação"])


@router.post(
    "/cadastro", response_model=UsuarioSaida, status_code=status.HTTP_201_CREATED
)
def cadastrar(
    dados: CadastroEntrada, sessao: Session = Depends(obter_sessao)
) -> Usuario:
    try:
        return servico.cadastrar(sessao, dados)
    except servico.TelefoneJaCadastrado:
        raise HTTPException(
            status.HTTP_409_CONFLICT, Message.TELEFONE_JA_CADASTRADO.message
        ) from None
    except servico.EmailJaCadastrado:
        raise HTTPException(
            status.HTTP_409_CONFLICT, Message.EMAIL_JA_CADASTRADO.message
        ) from None


@router.post("/login", response_model=TokenSaida)
def entrar_com_pin(
    dados: LoginPinEntrada, sessao: Session = Depends(obter_sessao)
) -> TokenSaida:
    return _entrar(
        sessao,
        dados.telefone,
        dados.pin,
        Message.PIN_ERRADO.message,
    )


@router.post("/pin", response_model=TokenSaida, include_in_schema=False)
def entrar_com_pin_legacy(
    dados: LoginPinEntrada, sessao: Session = Depends(obter_sessao)
) -> TokenSaida:
    return entrar_com_pin(dados, sessao)


def _entrar(
    sessao: Session, telefone: str, segredo: str, mensagem_erro: str
) -> TokenSaida:
    try:
        usuario = servico.autenticar(sessao, telefone, segredo)
    except servico.CredenciaisInvalidas:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, mensagem_erro) from None
    except servico.ContaBloqueada as erro:
        segundos = erro.segundos_restantes
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            Message.CONTA_BLOQUEADA.message.format(segundos=segundos),
            headers={"Retry-After": str(segundos)},
        ) from None
    duracao = Attempts.DURACAO_TOKEN_PIN.value
    token = criar_token(usuario.id, "pin", duracao)
    return TokenSaida(access_token=token, expira_em=int(duracao.total_seconds()))

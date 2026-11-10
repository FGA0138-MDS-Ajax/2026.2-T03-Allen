from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.integracoes.correio import obter_email
from app.modulos.identidade import recuperacao, servico
from app.modulos.identidade.esquemas import (
    CadastroEntrada,
    EsqueciPinEntrada,
    EsqueciPinSaida,
    LoginPinEntrada,
    RedefinirPinEntrada,
    TokenSaida,
    TrocarPinEntrada,
    UsuarioSaida,
)
from app.modulos.identidade.mensagens import Message
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token, usuario_atual
from app.modulos.identidade.servico import Attempts
from app.nucleo.banco import obter_sessao
from app.nucleo.portas import PortaEmail

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


def _entrar(
    sessao: Session, telefone: str, segredo: str, mensagem_erro: str
) -> TokenSaida:
    try:
        usuario = servico.autenticar(sessao, telefone, segredo)
    except servico.CredenciaisInvalidas:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, mensagem_erro) from None
    except servico.ContaBloqueada as erro:
        raise _conta_bloqueada(erro) from None
    return _emitir_token(usuario)


@router.post(
    "/pin/esqueci",
    response_model=EsqueciPinSaida,
    status_code=status.HTTP_202_ACCEPTED,
)
def esqueci_pin(
    dados: EsqueciPinEntrada,
    tarefas: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
    email: PortaEmail = Depends(obter_email),
) -> EsqueciPinSaida:
    """Envia um código de 6 dígitos para o e-mail do cadastro."""
    try:
        usuario, codigo = recuperacao.pedir_codigo(sessao, dados.telefone)
    except recuperacao.CelularSemConta:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, Message.CELULAR_SEM_CONTA.message
        ) from None
    except recuperacao.EspereNovoCodigo as erro:
        segundos = erro.segundos_restantes
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            Message.ESPERE_NOVO_CODIGO.message.format(segundos=segundos),
            headers={"Retry-After": str(segundos)},
        ) from None
    except recuperacao.MuitosCodigos:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, Message.MUITOS_CODIGOS.message
        ) from None
    except recuperacao.RecuperacaoIndisponivel:
        raise _recuperacao_indisponivel() from None

    minutos = int(recuperacao.Limites.VALIDADE_CODIGO.value.total_seconds() // 60)
    texto = Message.EMAIL_CODIGO.message.format(
        nome=usuario.nome, codigo=codigo, minutos=minutos
    )
    tarefas.add_task(email.enviar, usuario.email, Message.EMAIL_ASSUNTO.message, texto)
    return EsqueciPinSaida(
        enviado_para=recuperacao.mascarar_email(usuario.email),
        validade_minutos=minutos,
    )


@router.post("/pin/redefinir", response_model=TokenSaida)
def redefinir_pin(
    dados: RedefinirPinEntrada, sessao: Session = Depends(obter_sessao)
) -> TokenSaida:
    """Confere o código, grava o novo PIN e já entra na conta."""
    try:
        usuario = recuperacao.redefinir_pin(
            sessao, dados.telefone, dados.codigo, dados.novo_pin
        )
    except recuperacao.CodigoErrado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, Message.CODIGO_ERRADO.message
        ) from None
    except recuperacao.RecuperacaoIndisponivel:
        raise _recuperacao_indisponivel() from None
    return _emitir_token(usuario)


@router.put("/pin", response_model=TokenSaida)
def trocar_pin(
    dados: TrocarPinEntrada,
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> TokenSaida:
    """Troca o PIN de quem está logado. Devolve um token novo para este aparelho."""
    try:
        usuario = recuperacao.trocar_pin(
            sessao, usuario, dados.pin_atual, dados.novo_pin
        )
    except servico.CredenciaisInvalidas:
        # 400, e não 401, para o app não achar que a sessão terminou
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, Message.PIN_ATUAL_ERRADO.message
        ) from None
    except servico.ContaBloqueada as erro:
        raise _conta_bloqueada(erro) from None
    return _emitir_token(usuario)


def _emitir_token(usuario: Usuario) -> TokenSaida:
    duracao = Attempts.DURACAO_TOKEN_PIN.value
    token = criar_token(usuario.id, "pin", duracao, usuario.versao_token)
    return TokenSaida(access_token=token, expira_em=int(duracao.total_seconds()))


def _conta_bloqueada(erro: servico.ContaBloqueada) -> HTTPException:
    segundos = erro.segundos_restantes
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        Message.CONTA_BLOQUEADA.message.format(segundos=segundos),
        headers={"Retry-After": str(segundos)},
    )


def _recuperacao_indisponivel() -> HTTPException:
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE, Message.RECUPERACAO_INDISPONIVEL.message
    )

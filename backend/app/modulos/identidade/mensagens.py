from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    TELEFONE_INVALIDO = "Digite o número do celular com DDD. Exemplo: 61 99999-8888."
    PIN_INVALIDO = "O PIN deve ter de 4 a 6 números."
    TELEFONE_JA_CADASTRADO = (
        "Este celular já está cadastrado. Tente entrar na sua conta."
    )
    EMAIL_JA_CADASTRADO = "Este e-mail já está cadastrado. Tente entrar na sua conta."
    PIN_ERRADO = "Celular ou PIN errados. Confira e tente de novamente."
    CONTA_BLOQUEADA = (
        "Muitas tentativas erradas. Espere {segundos} segundos e tente de novo."
    )
    SESSAO_INVALIDA = "Sua sessão terminou. Entre de novo na sua conta."
    CODIGO_FORMATO = "O código tem 6 números."
    CELULAR_SEM_CONTA = "Não encontramos uma conta com este celular. Confira o número."
    ESPERE_NOVO_CODIGO = "Espere {segundos} segundos para pedir outro código."
    MUITOS_CODIGOS = "Você pediu muitos códigos. Tente de novo daqui a uma hora."
    CODIGO_ERRADO = "Código errado ou vencido. Confira ou peça um novo código."
    PIN_ATUAL_ERRADO = "O PIN atual está errado. Confira e tente de novo."
    RECUPERACAO_INDISPONIVEL = (
        "Não conseguimos enviar o código agora. Tente de novo em alguns minutos."
    )
    EMAIL_ASSUNTO = "Seu código para criar um novo PIN no Vero"
    EMAIL_CODIGO = (
        "Olá, {nome}!\n\n"
        "Seu código para criar um novo PIN é: {codigo}\n\n"
        "Ele vale por {minutos} minutos.\n\n"
        "Se não foi você que pediu, ignore este e-mail. Seu PIN continua o mesmo."
    )

    def __init__(self, message: str) -> None:
        self.message = message

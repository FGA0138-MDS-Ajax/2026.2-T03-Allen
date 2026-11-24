from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    NOME_EM_BRANCO = "Falta o nome do investimento. Exemplo: CDB do Banco do Brasil."
    VALOR_INVALIDO = (
        "O valor aplicado precisa ser maior que zero. Confira e tente de novo."
    )
    VALOR_MUITO_ALTO = "O valor aplicado está muito alto. Confira e tente de novo."
    APLICACAO_NO_FUTURO = (
        "O dia em que você aplicou ainda não chegou. Use hoje ou um dia antes."
    )
    VENCIMENTO_ANTES_DA_APLICACAO = (
        "O dia em que o dinheiro volta precisa ser depois do dia em que você aplicou."
    )
    TAXA_PREFIXADA_FORA_DO_LIMITE = (
        "Quanto rende por ano precisa ser mais que 0% e até {maximo}%. "
        "Confira e tente de novo."
    )
    PERCENTUAL_CDI_FORA_DO_LIMITE = (
        "A porcentagem do CDI precisa ser mais que 0% e até {maximo}%. "
        "Confira e tente de novo."
    )

    def __init__(self, message: str) -> None:
        self.message = message

from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    VALOR_INVALIDO = "O valor da conta precisa ser maior que zero."
    VALOR_MUITO_ALTO = "O valor da conta é muito alto. Confira e tente novamente."
    DATA_INVALIDA = (
        "A data de vencimento não está correta, verifique e tente novamente."
    )
    VENCIMENTO_MUITO_ANTIGO = (
        "Essa data de vencimento já passou faz tempo. Use uma data a partir de {data}."
    )
    CATEGORIA_INEXISTENTE = "Essa categoria não existe. Escolha outra."
    CONTA_NAO_ENCONTRADA = (
        "Não encontramos essa conta. Atualize a lista e tente de novo."
    )
    PARCELAS_FORA_DO_LIMITE = "Escolha de {minimo} a {maximo} parcelas."
    PARCELADA_E_FIXA = (
        "Uma compra parcelada não pode ser também conta fixa. Escolha só uma opção."
    )
    VALOR_MENOR_QUE_PARCELAS = (
        "O valor é pequeno demais para tantas parcelas. Diminua o número de parcelas."
    )

    def __init__(self, message: str):
        self.message = message

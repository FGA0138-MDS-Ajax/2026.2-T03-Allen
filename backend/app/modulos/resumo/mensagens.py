from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    # Erros da exportação (RF38)
    MES_INVALIDO = "O mês não está certo. Escreva assim: 2026-11."
    FORMATO_INVALIDO = "Esse formato não existe. Escolha pdf ou csv."

    # Documento exportado (RF38)
    TITULO = "Resumo das suas finanças"
    SECAO_TOTAIS = "Resumo do mês"
    TOTAL_ENTROU = "Dinheiro que entrou"
    TOTAL_GASTOU = "Gastos"
    TOTAL_CONTAS = "Contas do mês"
    TOTAL_DISPONIVEL = "Dinheiro disponível"
    SECAO_CATEGORIAS = "Onde você gastou"
    SEM_CATEGORIA = "Sem categoria"
    SECAO_REGISTROS = "O que entrou e saiu"
    SECAO_CONTAS = "Contas do mês"
    NADA_NO_MES = "Nada registrado neste mês."
    COLUNA_DIA = "Dia"
    COLUNA_TIPO = "Tipo"
    COLUNA_DESCRICAO = "Descrição"
    COLUNA_CATEGORIA = "Categoria"
    COLUNA_VALOR = "Valor (R$)"
    COLUNA_DIA_DE_PAGAR = "Dia de pagar"
    COLUNA_SITUACAO = "Situação"
    TIPO_ENTRADA = "Entrou"
    TIPO_GASTO = "Gastou"
    AUTOMATICO = "{descricao} (automático)"
    SEM_DESCRICAO = "Sem descrição"
    CONTA_PAGA = "Paga"
    CONTA_A_PAGAR = "A pagar"
    CONTA_ATRASADA = "Atrasada"

    def __init__(self, message: str) -> None:
        self.message = message

def formatar_moeda(centavos: int) -> str:
    reais = centavos / 100
    return f"R$ {reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def boas_vindas(nome: str | None = None) -> str:
    saudacao = f"Olá, {nome}!" if nome else "Olá!"
    return (
        f"{saudacao} Seja muito bem-vindo(a) ao Vero! 🎉\n\n"
        "Eu sou seu assistente pessoal e estou aqui para te ajudar a acompanhar seus gastos e entradas no dia a dia sem complicação.\n\n"
        "Sempre que você fizer uma compra ou receber algum dinheiro, é só me mandar uma mensagem por aqui, por exemplo:\n"
        "👉 *Gastei 35 na farmácia*\n"
        "👉 *Comprei 2 pães por 10 reais*\n"
        "👉 *Recebi 1500 da aposentadoria*\n\n"
        "Pode me mandar agora mesmo se quiser registrar algo!"
    )


def confirmacao_gasto(valor_centavos: int, categoria: str) -> str:
    valor = formatar_moeda(valor_centavos)
    return (
        f"Entendi! Você gastou {valor} com {categoria}.\n\n"
        f"Posso anotar esse gasto? (Responda com *Sim* ou *Não*)"
    )


def confirmacao_sucesso_gasto(valor_centavos: int, categoria: str) -> str:
    valor = formatar_moeda(valor_centavos)
    return f"Anotado! Já registrei o seu gasto de {valor} com {categoria}."


def confirmacao_renda(valor_centavos: int, categoria: str) -> str:
    valor = formatar_moeda(valor_centavos)
    return (
        f"Entendi! Você recebeu {valor} de {categoria}.\n\n"
        f"Posso anotar esse rendimento? (Responda com *Sim* ou *Não*)"
    )


def confirmacao_sucesso_renda(valor_centavos: int, categoria: str) -> str:
    valor = formatar_moeda(valor_centavos)
    return f"Anotado! Já registrei a sua entrada de {valor} de {categoria}."


def usuario_nao_encontrado() -> str:
    return (
        "Olá! Não encontrei o seu número cadastrado no Vero.\n\n"
        "Para começar a usar e cuidar do seu dinheiro, por favor, faça seu cadastro no nosso aplicativo."
    )


def mensagem_nao_compreendida() -> str:
    return (
        "Desculpe, não consegui entender bem o valor ou o que foi gasto.\n\n"
        "Você pode me mandar uma mensagem como:\n"
        "👉 *Gastei 35 na farmácia*\n"
        "👉 *Recebi 1500 da aposentadoria*"
    )


def registro_cancelado() -> str:
    return "Tudo bem, não anotei nada. Quando quiser registrar, é só me mandar!"


def confirmacao_expirada() -> str:
    return (
        "Como passei um tempinho sem resposta, acabei não anotando aquele valor por segurança.\n\n"
        "Se quiser registrar, pode me mandar novamente!"
    )


# RF16: quando falta um dado, o assistente diz o motivo e pede só o que falta


def _rotulo(tipo_receita: bool) -> str:
    return "essa entrada" if tipo_receita else "esse gasto"


def pedir_valor(
    tipo_receita: bool | None, categoria: str, motivo: str | None = None
) -> str:
    """`tipo_receita` None: ainda não se sabe se o dinheiro saiu ou entrou (foto)."""
    motivo = motivo or "Não consegui entender o valor na sua mensagem."
    if tipo_receita is None:
        pergunta = "Qual foi o valor?"
    else:
        if not categoria or categoria in {"Outros", "Outras Receitas"}:
            complemento = ""
        elif tipo_receita:
            complemento = f" de {categoria}"
        else:
            complemento = f" com {categoria}"
        pergunta = f"Quanto foi {_rotulo(tipo_receita)}{complemento}?"
    return (
        f"{motivo}\n\n{pergunta} Pode mandar só o número, por exemplo: *35* ou *12,50*"
    )


def valor_ainda_nao_entendido() -> str:
    return (
        "Ainda não consegui entender o valor.\n\n"
        "Mande só o número, por exemplo: *35* ou *12,50*. "
        "Se preferir desistir, responda *cancelar*."
    )


def pedir_tipo(valor_centavos: int, motivo: str | None = None) -> str:
    motivo = motivo or "Não consegui saber se o dinheiro saiu ou entrou."
    return (
        f"{motivo}\n\n"
        f"Esse valor de {formatar_moeda(valor_centavos)} foi um *gasto* ou uma *entrada*?"
    )


def tipo_ainda_nao_entendido() -> str:
    return (
        "Desculpe, não entendi.\n\n"
        "Responda *gasto* se o dinheiro saiu ou *entrada* se o dinheiro entrou. "
        "Se preferir desistir, responda *cancelar*."
    )


def pedir_categoria(
    tipo_receita: bool, valor_centavos: int, motivo: str | None = None
) -> str:
    motivo = motivo or "Não consegui saber com o que foi."
    exemplos = (
        "*aposentadoria*, *salário* ou *venda*"
        if tipo_receita
        else "*mercado*, *farmácia* ou *luz*"
    )
    origem = "De onde veio" if tipo_receita else "Com o que foi"
    return (
        f"{motivo}\n\n"
        f"{origem} {_rotulo(tipo_receita)} de {formatar_moeda(valor_centavos)}? "
        f"Por exemplo: {exemplos}"
    )


def explicar_futuro() -> str:
    return (
        "Eu só anoto o que já aconteceu, para o seu saldo ficar certinho.\n\n"
        "Quando o gasto acontecer, é só me mandar, por exemplo: *Gastei 35 na farmácia*"
    )


def explicar_varios_valores() -> str:
    return (
        "Percebi mais de um valor na mesma mensagem e, para não errar, não anotei nada.\n\n"
        "Me mande um de cada vez, por exemplo:\n"
        "👉 *Gastei 35 na farmácia*\n"
        "👉 *Gastei 20 na padaria*"
    )


def falha_ao_salvar() -> str:
    return (
        "Tive um problema para salvar agora e *ainda não anotei*.\n\n"
        "Responda *Sim* daqui a pouco para eu tentar de novo."
    )

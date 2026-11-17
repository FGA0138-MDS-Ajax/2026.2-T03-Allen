import pytest
import asyncio
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import app.modulos.assistente.router as router_module
from app.modulos.assistente.extrator import TipoTransacao, processar_texto_mensagem
from app.modulos.assistente.mensagens import (
    confirmacao_expirada,
    confirmacao_gasto,
    confirmacao_renda,
    confirmacao_sucesso_gasto,
    confirmacao_sucesso_renda,
    formatar_moeda,
    registro_cancelado,
)
from app.modulos.assistente.sessao import GerenciadorSessao

FRASES_DE_TESTE_RF12 = [
    ("gastei 35 na farmácia", TipoTransacao.GASTO, 3500, "Farmácia"),
    ("comprei remédio de 25 reais", TipoTransacao.GASTO, 2500, "Farmácia"),
    ("deu 18,50 na drogaria", TipoTransacao.GASTO, 1850, "Farmácia"),
    ("comprei dipirona por 8 reais", TipoTransacao.GASTO, 800, "Farmácia"),
    ("paguei 150 na consulta com o médico", TipoTransacao.GASTO, 15000, "Saúde"),
    ("gastei 80 no dentista", TipoTransacao.GASTO, 8000, "Saúde"),
    
    ("gastei 120 no mercado", TipoTransacao.GASTO, 12000, "Alimentação"),
    ("comprei pão por 6,50", TipoTransacao.GASTO, 650, "Alimentação"),
    ("deu 45 na feira", TipoTransacao.GASTO, 4500, "Alimentação"),
    ("paguei 30 no almoço", TipoTransacao.GASTO, 3000, "Alimentação"),
    ("gastei 50 no açougue", TipoTransacao.GASTO, 5000, "Alimentação"),
    ("comprei leite por 5 reais", TipoTransacao.GASTO, 500, "Alimentação"),
    ("deu 200 no supermercado", TipoTransacao.GASTO, 20000, "Alimentação"),
    ("paguei 60 no restaurante", TipoTransacao.GASTO, 6000, "Alimentação"),
    
    ("paguei 25 de uber", TipoTransacao.GASTO, 2500, "Transporte"),
    ("gastei 50 de gasolina", TipoTransacao.GASTO, 5000, "Transporte"),
    ("comprei passagem de 4,40", TipoTransacao.GASTO, 440, "Transporte"),
    ("deu 15 no táxi", TipoTransacao.GASTO, 1500, "Transporte"),

    ("paguei 120 de luz", TipoTransacao.GASTO, 12000, "Moradia"),
    ("gastei 85 de água", TipoTransacao.GASTO, 8500, "Moradia"),
    ("paguei o aluguel de 1200", TipoTransacao.GASTO, 120000, "Moradia"),
    ("deu 90 na conta de gás", TipoTransacao.GASTO, 9000, "Moradia"),

    ("gastei 40 no cinema", TipoTransacao.GASTO, 4000, "Lazer"),
    ("comprei presente de 100 reais", TipoTransacao.GASTO, 10000, "Lazer"),

    ("recebi 1500 da aposentadoria", TipoTransacao.RECEITA, 150000, "Aposentadoria"),
    ("caiu o benefício do inss de 1412", TipoTransacao.RECEITA, 141200, "Aposentadoria"),
    ("recebi meu salário de 3000", TipoTransacao.RECEITA, 300000, "Salário"),
    ("caiu o adiantamento de 800 reais", TipoTransacao.RECEITA, 80000, "Salário"),
    ("ganhei 150 de bico hoje", TipoTransacao.RECEITA, 15000, "Renda Extra"),
    ("recebi um pix de 50 reais", TipoTransacao.RECEITA, 5000, "Renda Extra"),
]

FRASES_ISSUE_71_SUCESSO = [
    ("gastei 1,250.00 no mercado", TipoTransacao.GASTO, 125000, "Alimentação"),
    ("gastei 10.000 no conserto", TipoTransacao.GASTO, 1000000, "Outros"),
    ("1250,5 no aluguel", TipoTransacao.GASTO, 125050, "Moradia"),
    ("dia 12 gastei 35 na farmácia", TipoTransacao.GASTO, 3500, "Farmácia"),
    ("comprei 2 pães por 10 reais", TipoTransacao.GASTO, 1000, "Alimentação"),
    ("recebi o pagamento de 800", TipoTransacao.RECEITA, 80000, "Salário"),
    ("recebi 100 do Claudeu", TipoTransacao.RECEITA, 10000, "Outras Receitas"),
    ("gastei 35 reais e 50 centavos na farmácia", TipoTransacao.GASTO, 3550, "Farmácia"),
]

FRASES_ISSUE_71_RECUSA = [
    "gastei 35 na farmácia e 20 na padaria",
    "recebi 50 do meu filho e gastei 30 no mercado",
    "vou gastar 100 amanhã",
    "pretendo comprar um remédio de 50 reais semana que vem",
    "gastei -35 na farmácia",
    "gastei 0 no mercado",
    "quanto eu tenho?",
    "oi, tudo bem?",
    "gastei na farmácia",
]

@pytest.mark.parametrize(
    ("frase", "tipo_esperado", "valor_esperado", "categoria_esperada"),
    FRASES_DE_TESTE_RF12,
)
def test_rf12_extracao(
    frase: str,
    tipo_esperado: TipoTransacao,
    valor_esperado: int,
    categoria_esperada: str,
):
    resultado = processar_texto_mensagem(frase)

    assert resultado.sucesso is True, f"Falha ao interpretar: '{frase}'"
    assert resultado.tipo == tipo_esperado, f"Tipo incorreto na frase '{frase}'"
    assert resultado.valor == valor_esperado, f"Valor incorreto na frase '{frase}'"
    assert resultado.categoria == categoria_esperada, f"Categoria incorreta na frase '{frase}'"

def test_rf12_formatacao_centavo():
    assert formatar_moeda(3500) == "R$ 35,00"
    assert formatar_moeda(450) == "R$ 4,50"
    assert formatar_moeda(150000) == "R$ 1.500,00"

def test_rf15_fluxo_confirmacao():
    sessao = GerenciadorSessao()
    tel = "5561999999999"

    sessao.salvar_pendencia(tel, TipoTransacao.GASTO, 3500, "Farmácia", "gastei 35 na farmácia")
    pendencia, expirou = sessao.obter_pendencia(tel)

    assert expirou is False
    assert pendencia is not None
    assert pendencia.valor == 3500
    assert pendencia.categoria == "Farmácia"

    assert sessao.resposta_sim("Sim") is True
    assert sessao.resposta_sim("Pode") is True
    sessao.limpar_pendencia(tel)

    pendencia_apos, _ = sessao.obter_pendencia(tel)
    assert pendencia_apos is None

def test_rf15_fluxo_cancelamento():
    sessao = GerenciadorSessao()
    tel = "5561999999999"

    sessao.salvar_pendencia(tel, TipoTransacao.GASTO, 3500, "Farmácia", "gastei 35 na farmácia")
    
    assert sessao.resposta_nao("Não") is True
    assert sessao.resposta_nao("Cancela") is True
    sessao.limpar_pendencia(tel)
    
    pendencia_apos, _ = sessao.obter_pendencia(tel)
    assert pendencia_apos is None

def test_rf15_expiracao():
    sessao = GerenciadorSessao()
    sessao._valkey = None
    tel = "5561999999999"

    sessao.salvar_pendencia(tel, TipoTransacao.GASTO, 3500, "Farmácia", "gastei 35 na farmácia")

    sessao._sessoes_memoria[tel].criado = datetime.now(timezone.utc) - timedelta(minutes=20)

    pendencia, expirou = sessao.obter_pendencia(tel)
    assert pendencia is None
    assert expirou is True

def test_rf15_linguagem_simples():
    msg_gasto = confirmacao_gasto(3500, "Farmácia")
    assert "R$ 35,00" in msg_gasto
    assert "Farmácia" in msg_gasto
    assert "Posso anotar esse gasto?" in msg_gasto

    msg_renda = confirmacao_renda(150000, "Aposentadoria")
    assert "R$ 1.500,00" in msg_renda
    assert "Aposentadoria" in msg_renda
    assert "Posso anotar esse rendimento?" in msg_renda

    assert "Anotado! Já registrei o seu gasto de R$ 35,00 com Farmácia." in confirmacao_sucesso_gasto(3500, "Farmácia")
    assert "Anotado! Já registrei a sua entrada de R$ 1.500,00 de Aposentadoria." in confirmacao_sucesso_renda(150000, "Aposentadoria")
    assert "Tudo bem, não anotei nada. Quando quiser registrar, é só me mandar!" in registro_cancelado()
    assert "Como passei um tempinho sem resposta, acabei não anotando aquele valor por segurança.\n\nSe quiser registrar, pode me mandar novamente!" in confirmacao_expirada()

# Issue #71
@pytest.mark.parametrize(
    ("frase", "tipo_esperado", "valor_esperado", "categoria_esperada"),
    FRASES_ISSUE_71_SUCESSO,
)
def test_rf12_casos_complexos(
    frase: str,
    tipo_esperado: TipoTransacao,
    valor_esperado: int,
    categoria_esperada: str,
):
    resultado = processar_texto_mensagem(frase)
    assert resultado.sucesso is True, f"Deveria ter sucesso na frase: '{frase}'"
    assert resultado.tipo == tipo_esperado, f"Tipo incorreto na frase '{frase}'"
    assert resultado.valor == valor_esperado, f"Valor incorreto na frase '{frase}'"
    assert resultado.categoria == categoria_esperada, f"Categoria incorreta na frase '{frase}'"

@pytest.mark.parametrize("frase", FRASES_ISSUE_71_RECUSA)
def test_rf12_frases_recusadas_com_seguranca(frase: str):
    resultado = processar_texto_mensagem(frase)
    assert resultado.sucesso is False, f"A frase ambígua/inválida NÃO deveria ter sucesso: '{frase}'"

# Issue #72
@pytest.fixture
def ambiente_assistente(monkeypatch):
    sessao = GerenciadorSessao()
    sessao._valkey = None

    mensagens_enviadas = []
    registrar = Mock()

    monkeypatch.setattr(router_module, "sessao_assistente", sessao)
    monkeypatch.setattr(
        router_module,
        "buscar_usuario_telefone",
        lambda telefone: type("UsuarioTeste", (), {"id": "usuario-teste"})(),
    )

    async def enviar(destinatario, texto):
        mensagens_enviadas.append(texto)

    monkeypatch.setattr(router_module, "enviar_mensagem", enviar)
    monkeypatch.setattr(
        router_module, "SessaoLocal", lambda: nullcontext(object())
    )
    monkeypatch.setattr(
        router_module.servico_transacoes, "registrar", registrar
    )

    telefone = "5561999999999"
    remetente = f"{telefone}@s.whatsapp.net"

    def enviar_texto(texto):
        asyncio.run(router_module.processar_responder(remetente, texto))

    return sessao, telefone, mensagens_enviadas, registrar, enviar_texto

@pytest.mark.parametrize("resposta", ["Sim!", "sim, pode anotar", "ok", "👍"])
def test_rf15_aceita_confirmacoes_comuns(ambiente_assistente, resposta):
    sessao, telefone, _, registrar, enviar = ambiente_assistente

    enviar("gastei 35 na farmácia")
    assert registrar.call_count == 0

    enviar(resposta)

    assert registrar.call_count == 1
    assert registrar.call_args.kwargs["dados"].valor == Decimal("35.00")
    assert sessao.obter_pendencia(telefone)[0] is None

def test_rf15_corrige_valor(ambiente_assistente):
    sessao, telefone, _, registrar, enviar = ambiente_assistente

    enviar("gastei 35 na farmácia")
    enviar("nao, foi 45")

    pendencia, expirou = sessao.obter_pendencia(telefone)
    assert expirou is False
    assert pendencia is not None
    assert pendencia.valor == 4500
    assert pendencia.categoria == "Farmácia"
    assert registrar.call_count == 0

    enviar("Sim")

    assert registrar.call_count == 1
    assert registrar.call_args.kwargs["dados"].valor == Decimal("45.00")

def test_rf15_corrige_categoria(ambiente_assistente):
    sessao, telefone, _, registrar, enviar = ambiente_assistente

    enviar("gastei 35 na farmácia")
    enviar("Não, foi no mercado")

    pendencia, expirou = sessao.obter_pendencia(telefone)
    assert expirou is False
    assert pendencia is not None
    assert pendencia.valor == 3500
    assert pendencia.categoria == "Alimentação"
    assert registrar.call_count == 0

def test_rf15_processa_apos_expiracao(ambiente_assistente):
    sessao, telefone, mensagens, _, enviar = ambiente_assistente

    enviar("gastei 35 na farmácia")
    sessao._sessoes_memoria[telefone].criado = (
        datetime.now(timezone.utc) - timedelta(minutes=16)
    )

    enviar("gastei 20 no mercado")

    pendencia, expirou = sessao.obter_pendencia(telefone)
    assert expirou is False
    assert pendencia is not None
    assert pendencia.valor == 2000
    assert pendencia.categoria == "Alimentação"
    assert mensagens[-1] == confirmacao_gasto(2000, "Alimentação")
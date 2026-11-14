"""Ponto de extensão entre o pagamento da conta e o saldo do mês (RF30).

A regra de negócio ainda está em aberto no time de produto. Nesta entrega,
marcar uma conta como paga altera apenas o status da conta: o saldo do mês
não é descontado. O módulo de saldo (RF19) também ainda não existe neste
código, então qualquer efeito financeiro seria prematuro.

Quando a regra for definida, basta trocar ``ESTRATEGIA_SALDO`` por uma
implementação que grave o lançamento correspondente, sem alterar o router,
o serviço de contas ou a interface.
"""

from typing import Protocol

from app.modulos.contas.modelos import Conta


class EstrategiaSaldo(Protocol):  # mais ou menos interface em JAVA
    """Contrato para reagir à mudança de pagamento de uma conta."""

    def ao_alterar_pagamento(self, conta: Conta, paga: bool) -> None:
        """Aplica o efeito no saldo quando a conta muda de pendente/paga."""
        ...


class SaldoInalterado:
    """Regra provisória: pagar ou desfazer não mexe no saldo do mês.

    A conta já representa um compromisso do mês. Descontar novamente no
    pagamento poderia duplicar o valor quando o RF19 for implementado.
    """

    def ao_alterar_pagamento(self, conta: Conta, paga: bool) -> None:
        pass


ESTRATEGIA_SALDO: EstrategiaSaldo = SaldoInalterado()

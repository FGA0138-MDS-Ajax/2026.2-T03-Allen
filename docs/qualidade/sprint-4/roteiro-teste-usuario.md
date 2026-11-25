# Roteiro do 1º teste com pessoa idosa (Sprint 4)

Pedido na #47: 1 ou 2 pessoas idosas reais usando **cadastro, registro de gasto e WhatsApp**. A QA já percorreu esses
caminhos com a persona fictícia [Dona Lurdes](persona.md) e corrigiu o que encontrou ([relatório](relatorio.md)). Este
roteiro é para a sessão com gente de verdade.

## Antes da sessão

- [ ] Fazer o merge dos PRs de correção da S4 (ordem no [relatório](relatorio.md#ordem-sugerida-de-merge)) e subir o
      app num endereço **HTTPS** que abra no celular da pessoa (túnel ou staging)
- [ ] Evolution API conectada, com `ENVIO_WHATSAPP=api`; se possível, `LEITOR_COMPROVANTE=claude` com `AI_API_KEY`
- [ ] Explicar o teste e pedir autorização por escrito (LGPD): só anotamos o que observamos, **sem** nome, telefone ou
      valores reais da pessoa no relatório. Para os gastos, usar valores inventados (combinar antes)
- [ ] Usar o **celular da própria pessoa**, com a fonte e o brilho do jeito que ela usa
- [ ] Uma pessoa conduz e outra anota. Quem conduz **não ajuda** nem aponta na tela; se a pessoa travar por 2 minutos,
      ajude e marque "precisou de ajuda"

## Tarefas (falar assim, sem nomes de botão)

| # | O que pedir | O que observar |
|---|---|---|
| 1 | "Crie sua conta no Vero com este link." | Entendeu "PIN"? Errou o PIN de confirmação? Achou o e-mail obrigatório? |
| 2 | "Anote que a senhora gastou 35 reais e 90 centavos na farmácia hoje." | Achou o botão? Acertou os centavos no teclado? Tocou duas vezes? Viu a confirmação antes de ela sumir? |
| 3 | "Cadastre a conta de luz, que vence todo dia 10." | Marcou "Repetir todo mês"? Entendeu dia e mês? |
| 4 | "A senhora comprou uma geladeira em 10 vezes. Anote." | Achou "Compra parcelada"? Entendeu que o valor é o total? |
| 5 | "Agora me mostre só as contas que ainda faltam pagar." | Usou o filtro? Percebeu qual estava escolhido? |
| 6 | "Mande pelo WhatsApp um gasto, do jeito que a senhora escreveria." | Como escreveu (acento, valor por extenso, áudio)? O assistente entendeu de primeira? Ela respondeu "sim"? |
| 7 | "Mande a foto de um cupom ou de uma conta para o assistente." | Achou como mandar? Quanto tempo esperou? Entendeu o que o assistente pediu? |

## Durante: anotar por tarefa

| Tarefa | Concluiu? (sozinha / com ajuda / não) | Tempo | Onde travou | Frase marcante dela |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |

## Depois

- Três perguntas: "O que foi mais difícil?", "Usaria isso no dia a dia?" e "Pelo app ou pelo WhatsApp?"
- Transformar cada trava em issue de bug (`sprint-4` ou da sprint corrente), citando "teste com usuário, pessoa 1"
- Resumir no relatório da S4: quantas tarefas foram feitas sozinha, com ajuda e não concluídas

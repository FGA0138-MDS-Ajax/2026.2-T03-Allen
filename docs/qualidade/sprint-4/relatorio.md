# Relatório de QA da Sprint 4

Período planejado: 28/10–01/11 · Validação em 23/11 · Responsável: Beatriz (QA) · Commit: `e2b3c19` (`dev`)

## Resumo

Os sete cartões da S4 (#21–#27) estão fechados, mas a sprint **não passa** no aceite na `dev` como está. O achado mais
grave é de processo: **a leitura de fotos (RF14) não chegou à `dev`.** O PR #130 era empilhado no #129 e foi mergeado
na branch do #129 depois que ela já tinha entrado, e a #21 foi fechada assim mesmo (#132).

Os outros defeitos que pesam para a pessoa idosa:

- **Lembrete (RF28) e resumo (RF24) nunca chegam ao WhatsApp:** o adaptador de envio era um `TODO` (#152).
- **Compra parcelada (RF37) só existia na API:** não havia campo na tela (#134).
- **Apagar conta não apagava:** a tela dizia "apagada com sucesso" e a conta voltava ao recarregar (#133).
- **Conta fixa do dia 31 ficava no dia 28** depois de fevereiro (#153).

O teste foi feito com a persona fictícia [Dona Lurdes](persona.md): 74 anos, celular simples com fonte grande, 3G
instável, catarata e tremor leve, escreve no WhatsApp sem acento e com valor por extenso. Essa simulação **não
substitui** o teste com pessoa idosa real pedido na issue; ele está preparado no
[roteiro do teste com usuário](roteiro-teste-usuario.md).

Foram **14 bugs registrados** (#132–#143, #152, #153) e 1 reaberto (#111), **todos com PR de correção** (10 PRs). As
dez branches mesclam juntas sem conflito; nessa versão combinada, 307 testes do backend, 132 do front e 32 do E2E
passam, e o axe não acusa nada nas 7 telas.

O que está bom: o RF16 (o assistente explica o que faltou e não perde lançamento), o app com internet lenta e sem
conexão (avisa, não duplica e não perde o valor digitado), o toque duplo no cadastro e no salvar, e a regressão da
S1–S3.

## Números

| Verificação | Resultado |
|---|---|
| Critérios de aceite (23) | 13 ✅ · 6 ❌ · 3 ⚠️ · 1 ⏳ na `dev` ([detalhes](validacao-criterios.md)). Todos os ❌ e ⚠️ têm PR |
| RNF04, foto em até 5 s (20 amostras) | ⏳ sem `AI_API_KEY`. Sem a IA: média 12 ms, pior caso 21 ms. Medição real com `scripts/medir-rnf04.py` |
| Regressão S1–S3, E2E (Playwright, 360 px e desktop) | 32/32 na `dev`; 32/32 com as correções e as checagens novas (um `main` só e alvos ≥ 44 px) |
| Backend (pytest, Postgres 16 e Valkey locais) | 307/307 com as 10 correções mescladas |
| Frontend (vitest, lint, Prettier, `tsc`, build) | 132/132 e ok, com as correções mescladas |
| axe (WCAG 2.1 AA + best-practice), dados reais | Na `dev`: `main` duplicado em 4 telas e cadastro sem `h1`. Com as correções: 0 nas 7 telas |
| 1º teste com pessoa idosa real | ⏳ [roteiro](roteiro-teste-usuario.md) pronto |

## Situação dos cartões

| Cartão | Issue | Situação na QA |
|---|---|---|
| RF14 · Fotos no WhatsApp | #21 fechada | ❌ Código fora da `dev` (#132). Leitura real e RNF04 sem medir (falta a chave) |
| RF16 · Preenchimento manual | #22 fechada | ✅ Explica o motivo e não perde lançamento |
| RF24 · Resumo proativo | #23 fechada | ⚠️ Não é enviado (#152); "parar resumo" só com a frase exata (#137); sem categoria dos gastos do WhatsApp (#138) |
| RF26 · Contas fixas | #24 fechada | ⚠️ Dia 31 vira 28 para sempre (#153) |
| RF28 · Aviso de vencimento | #25 fechada | ❌ Sem aviso de "hoje" no app (#139) e sem envio no WhatsApp (#152) |
| RF33 · Filtro de contas | #26 fechada | ⚠️ Filtro escolhido só muda de cor (#141) |
| RF37 · Parcelas | #27 fechada | ❌ Sem campo na tela (#134) |

## Bugs registrados

| Issue | Gravidade | Stack | Resumo | PR |
|---|---|---|---|---|
| #132 | Crítica | back-end | RF14 não está na `dev`: o #130 entrou na branch do #129 | #144 |
| #133 | Alta | front + back | Apagar conta diz "apagada", mas a API não tinha `DELETE` e a conta volta | #148 |
| #134 | Alta | front-end | RF37 sem tela; parcelas sem número; "A vencer" somava meses futuros | #149 |
| #152 | Alta | back-end | Lembrete (RF28) e resumo (RF24) não chegam: adaptador "api" era `TODO` | #154 |
| #135 | Média | back-end | Assistente ignora "20,5" e "2000" e não entende valor por extenso | #145 |
| #136 | Média | back-end | Dinheiro recebido ("me deu", "vendi") vira gasto | #145 |
| #137 | Média | back-end | "Parar resumo por favor" não desliga; "não quero mais receber resumo" vira entrada | #146 |
| #138 | Média | back-end | Gastos do WhatsApp sem categoria | #147 |
| #139 | Média | front-end | Conta que vence hoje sem aviso no app | #150 |
| #140 | Média | front-end | Conta nova: "Você já gastou todo o saldo" sem gasto nenhum | #150 |
| #142 | Média | front-end | Alvos de toque abaixo de 48 px (28, 30, 14 px…) | #151 |
| #153 | Média | back-end | Conta fixa do dia 31 fica no dia 28 depois de fevereiro | #155 |
| #141 | Baixa | front-end | Filtro escolhido só muda de cor (critério do RF33) | #151 |
| #143 | Baixa | front-end | Duas regiões `main` por tela; botão dentro de link | #151 |
| #111 | Média | front-end | (S3, **reaberta**) Cadastro sem `h1` no celular: fechada sem correção | #151 |

## Ordem sugerida de merge

1. **#144** (RF14 na `dev`), antes de tudo: o **#147** inclui os commits dele de propósito. Se o #147 entrar primeiro,
   leva o RF14 junto em vez de deixá-lo de fora.
2. Os demais, em qualquer ordem: #145, #146, #147, #148, #149, #150, #151, #154 e #155. Foram mesclados juntos sem
   conflito nesta QA.
3. Depois do merge, rodar `scripts/medir-rnf04.py` com a chave da API e fechar o RNF04.

**Para não repetir a #132:** em PR empilhado, mudar a base do PR de cima para `dev` à mão logo depois do merge do de
baixo, antes de mergear o de cima. O GitHub só faz isso sozinho quando a branch de baixo é apagada.

## O que ficou para a próxima sprint

- O **teste com 1 ou 2 pessoas idosas reais** ([roteiro](roteiro-teste-usuario.md)), já com as correções na `dev` e o
  app em HTTPS.
- **RNF04 real:** 20 fotos de comprovantes, notas e contas com `LEITOR_COMPROVANTE=claude`. Se passar de 5 s, testar
  um modelo mais rápido em `AI_MODELO`.
- O assistente ignora "ontem" e anota com a data de hoje ("ontem gastei 40 no mercado"). Vale um cartão no RF12.
- "Você recebeu R$ 50,00 de Outras Receitas" soa estranho: trocar a frase quando não houver categoria de entrada.
- Material do ponto de controle de 09/11 e 11/11: as datas já passaram. Este relatório e a validação servem de
  material para o próximo.

## Riscos

- **Cartão fechado sem o código na `dev`:** a #21 foi fechada pelo PR #130, mergeado numa branch que não era a `dev`.
  Antes de fechar um cartão, conferir que o PR entrou na `dev`. Marcar o "CI ok" como obrigatório na proteção da
  `dev` não pega esse caso.
- **Foto enviada a terceiro (LGPD):** a leitura do RF14 manda a imagem à API da Anthropic. Precisa estar na política de
  privacidade e na auditoria do RNF05 (#43).
- **Mensagens proativas pela Evolution API:** sem template, mas com risco de bloqueio do número se a Meta entender como
  envio em massa. O resumo já é opcional e diz como parar; o lembrete só sai no dia do vencimento.
- **Teste com pessoa real atrasado:** era da S4 e ainda não aconteceu. Os achados da persona são o que um especialista
  prevê; o que trava de verdade só aparece com gente.

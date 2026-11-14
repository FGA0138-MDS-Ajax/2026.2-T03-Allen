# Relatório de QA da Sprint 2

Período planejado: 14/10–18/10 · Validação em 10/11 · Responsável: Beatriz (QA)

## Resumo

As 8 issues da S2 (#9–#16) estão **fechadas**, mas foram fechadas manualmente, sem PR. Na `dev` só entraram o RF17
(#53, backend) e o RF30 (#52, backend). O assistente do WhatsApp está numa branch fora da `dev` e o frontend no PR #64,
ainda aberto. A sprint **não passa** no aceite.

O principal problema é o fluxo do WhatsApp: o assistente entende a maioria das frases e pede confirmação, mas responde
"Anotado! Já registrei" **sem gravar nada no banco**. O app também não escuta o canal em tempo real. Ou seja, o
caminho WhatsApp → banco → app (RF12 + RF15 + RF17), coração da sprint, não acontece de ponta a ponta.

O que está bom: a API de contas com pagamento e desfazer (RF30), o canal `/ws` (o evento chega em 37 ms e é isolado por
usuário), os três estados de conta com cor + ícone + texto e a linguagem das mensagens do assistente.

Não existe staging nem número sandbox. A validação foi local, com Postgres e Valkey em Docker, e o assistente foi
testado chamando o extrator e a sessão diretamente, sem WhatsApp real.

## Números

| Verificação | Resultado |
|---|---|
| Critérios de aceite (28) | 9 ✅ · 10 ⚠️ · 8 ❌ · 1 ⏳ ([detalhes](validacao-criterios.md)) |
| Frases do assistente (47) | 37 corretas · 10 erradas, 6 delas com valor ou tipo errado sem aviso ([frases](frases-assistente.md)) |
| Testes do backend na `dev` (pytest) | 20/20 passaram |
| Teste de integração do RF17 (QA, fora do repositório) | evento em 37 ms · isolamento entre usuários ok · token inválido fecha com 1008 · chave repetida não duplica · 10/10 eventos perdidos quando publicados logo após o `conectado` |
| Testes do frontend do PR #64 (vitest) | 41/47. As 6 falhas são do `localStorage` nativo do Node 25 local, não do código. Build ok · lint com 1 erro (`no-explicit-any` em `Entrar.test.tsx`) |
| Testes do assistente | nenhum |
| Bugs registrados | 13 (2 críticos, 6 altos, 4 médios, 1 baixo) |

## Situação dos cartões

| Cartão | Issue | Situação na QA |
|---|---|---|
| RF04 · Direcionamento ao WhatsApp | #9 fechada | ❌ Link fixo, sem mensagem pré-preenchida (#67). Front fora da `dev` |
| RF10 · Edição e exclusão | #10 fechada | ❌ Sem edição, exclusão sem confirmação, dados de exemplo no navegador (#68) |
| RF12 · Assistente por texto | #11 fechada | ❌ Não grava (#69), atende número sem cadastro (#70), valores errados (#71), sem testes (#73). Fora da `dev` |
| RF15 · Confirmar antes de salvar | #12 fechada | ⚠️ Fluxo existe, mas não permite corrigir e só aceita "sim"/"não" exatos (#72) |
| RF17 · Reflexo instantâneo no app | #13 fechada | ⚠️ Backend ok, com perda de evento logo após conectar (#75). App não escuta (#74) |
| RF22 · Gráfico de saldo | #14 fechada | ⚠️ Barra mostra o disponível, não o gasto, e o texto alternativo é genérico (#76) |
| RF30 · Marcar conta como paga | #15 fechada | ⚠️ API e tela ok, mas pagar uma conta aumenta o saldo na tela (#77) |
| RF32 · Lista de contas por cores | #16 fechada | ⚠️ Estados ok, sem agrupar por dia (#78) e sem teste de fuso (#79) |

## Regressão da Sprint 1

Os 9 bugs da S1 (#54–#62) continuam **abertos**. Alguns estão em andamento em branches fora da `dev`:
`update/celular-texto-puro` (#62), `feat/RF01-esqueci-pin` (#55) e o PR #65 (cadastro).

| Fluxo da S1 | Situação |
|---|---|
| Backend da `dev` (contas, identidade) | 20/20 testes passaram, sem regressão |
| Login por PIN (#56) | O PR #64 já chama `POST /api/v1/auth/pin`. Cadastro e gasto continuam só no navegador |
| Saldo e lançamentos (#57) | Continua sem API. A tela inicial soma um salário fixo de exemplo (R$ 3.300,00) |
| Tela inicial sem `h1` (#60) | Continua sem `h1` no PR #64 |
| E2E `fluxo-principal.spec.ts` | Foi escrito para o front da branch `alteracoes-frontend` (Next.js). O PR #64 é outro front (Vite, outras rotas e textos), então o E2E precisa ser refeito quando ele entrar na `dev` |

## Bugs registrados

| Issue | Gravidade | Stack | Resumo |
|---|---|---|---|
| #69 | Crítica | back-end | Assistente confirma "Anotado!" mas não grava a transação |
| #74 | Crítica | front-end | App não escuta o `/ws`: gasto do WhatsApp não aparece sem recarregar |
| #70 | Alta | back-end | Número sem cadastro é atendido como "Usuário Teste"; busca por 8 dígitos; API key aceita na URL |
| #71 | Alta | back-end | Extrator grava valor ou tipo errado sem avisar (data, quantidade, "1,250.00", "Claudeu") |
| #72 | Alta | back-end | Confirmação só aceita "sim"/"não" exatos e "Não" não permite corrigir |
| #67 | Alta | front-end | Link do WhatsApp fixo, sem mensagem pré-preenchida e fora do fim do cadastro |
| #68 | Alta | front-end | Histórico sem edição, exclusão sem confirmação e com lançamentos de exemplo |
| #77 | Alta | front-end | Marcar conta como paga aumenta o saldo da tela inicial |
| #73 | Média | back-end | Assistente sem testes e com telefone e mensagem impressos no log (RNF05) |
| #75 | Média | back-end | Evento publicado logo após o `conectado` do `/ws` se perde |
| #76 | Média | front-end | Barra de saldo mostra o disponível, não o gasto; texto alternativo genérico |
| #78 | Média | front-end | Contas não agrupadas por dia |
| #79 | Baixa | back-end | Falta teste do "em atraso" na virada do dia no fuso de Brasília |

## O que ficou para a próxima sprint

- Reabrir #9–#16 ou movê-las de volta para desenvolvimento no Trello: foram fechadas sem PR e sem passar pela QA.
- Levar o assistente para a `dev`, ligado ao `transacoes.servico.registrar` (os contratos não batem: o assistente usa
  centavos e `GASTO`/`RECEITA`, o módulo de transações usa `Decimal` e `saida`/`entrada`).
- Ajustar a busca do usuário pelo telefone quando o #62 (hash do celular) entrar, senão o assistente para de achar todo mundo.
- Merge do PR #64 com o app ligado ao `/ws` e aos lançamentos da API (#57), e refazer o E2E para esse front.
- Staging e número sandbox do WhatsApp, para o teste ponta a ponta que a issue pede.
- Teste em aparelho real e com leitor de tela, que continuam pendentes da S1.

## Riscos

- **Issues fechadas sem PR:** o quadro mostra a S2 como entregue, mas dois terços do código não estão na `dev`. A DoD
  exige PR revisado e validação da QA antes de fechar.
- **Dados financeiros errados:** o extrator troca data e quantidade por valor, e a tela inicial aumenta o saldo ao pagar
  uma conta. Para o público do Vero, um saldo errado é pior do que nenhum.
- **Número sem cadastro atendido:** qualquer pessoa que mandar mensagem para o número do assistente é atendida, e
  quando a gravação for ligada esses registros cairiam num usuário inexistente ou no usuário errado.
- **Sem staging:** a inspeção do repositório é em 16/11 e nenhuma sprint foi validada no ambiente oficial.

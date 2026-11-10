# Sprint 2: validação dos critérios de aceite

Ambiente: **local** (ainda não existe staging nem número sandbox configurado). Data da validação: 10/11 · Responsável: Beatriz (QA)

Código avaliado, porque as issues da S2 foram fechadas sem PR e só RF17 (#53) e RF30 (#52) entraram na `dev`:

| Parte | Origem |
|---|---|
| Backend: contas, pagamento, transações, `/ws` | `dev`, com Postgres 17 e Valkey 8.1 em Docker |
| Assistente do WhatsApp (RF12, RF15) | branch `feature/whatsapp-texto` (fora da `dev`, 14 commits atrás) |
| Frontend (RF04, RF10, RF22, RF30, RF32) | branch `feature/frontend`, PR #64 aberto |

Legenda: ✅ passou · ❌ falhou (abrir issue) · ⚠️ passou em parte · ⏳ não entregue · ➖ não se aplica

## RF04 · Direcionamento para o assistente no WhatsApp

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Ao fim do primeiro acesso, botão grande "Falar com o assistente no WhatsApp" | ⚠️ | #67: o botão "Anotar gasto pelo WhatsApp" fica na tela inicial, mas não aparece ao fim do cadastro |
| 2 | Link `wa.me` abre a conversa com mensagem inicial pré-preenchida | ❌ | #67: `https://wa.me/5561999998888`, sem `?text=` |
| 3 | Número de teste em staging e oficial em produção, via variável de ambiente | ❌ | #67: número fixo no código (`Inicio.tsx`) |

## RF10 · Edição e exclusão no histórico de transações

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Lista do histórico com ícone da categoria, valor e data | ⚠️ | #68: a lista existe, mas com dados do navegador. Um usuário novo vê seis lançamentos de exemplo (salário de R$ 3.300,00, mercado, farmácia…) como se fossem dele |
| 2 | Editar valor, categoria e data | ⏳ | #68: não há edição |
| 3 | Excluir pede confirmação ("Tem certeza?") com botões grandes | ❌ | #68: a lixeira apaga na hora, no Início e no Extrato |
| 4 | Saldo e barra (RF19/RF22) recalculados na hora | ⚠️ | Recalcula na tela, mas sem API de lançamentos (#57) |

## RF12 · Assistente: processamento de gastos por texto

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | "gastei 35 na farmácia" → R$ 35,00, gasto, Farmácia | ⚠️ | Interpreta certo, mas **nada é gravado** (#69). 37 de 47 frases da QA corretas; as erradas registram valor errado sem avisar (#71). Ver [frases-assistente.md](frases-assistente.md) |
| 2 | Identifica receita ("recebi 1500 da aposentadoria") | ✅ | R$ 1.500,00, receita, Aposentadoria. Falha em "recebi o pagamento de 800" (#71) |
| 3 | Usuário identificado pelo número do WhatsApp (o mesmo do RF03) | ❌ | #70: número sem cadastro vira "Usuário Teste" e é atendido; a busca usa só os 8 últimos dígitos |
| 4 | Respostas em linguagem simples (RNF02) | ✅ | "Entendi! Você gastou R$ 35,00 com Farmácia. Posso anotar esse gasto?" e exemplos na mensagem de erro |
| 5 | Pelo menos 30 frases de teste rodando no CI | ❌ | #73: o assistente não tem nenhum teste. As 47 frases da QA estão prontas para virar fixture |

## RF15 · Assistente confirma antes de salvar

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Resumo "Gasto de R$ 35,00 em Farmácia. Está certo?" com respostas Sim/Não | ⚠️ | #72: o resumo existe, mas só aceita "sim"/"não" exatos. "Sim!", "sim, pode anotar", "ok" e 👍 descartam o registro e o assistente responde "não entendi" |
| 2 | "Não" permite corrigir | ❌ | #72: "Não" só cancela. "Não, foi 45" é tratado como mensagem nova |
| 3 | Sem resposta, não salva (tempo de expiração definido) | ✅ | Expira em 15 min. A pendência fica na memória do processo: se a API reiniciar ou tiver mais de um worker, ela se perde |

## RF17 · Registro do assistente reflete instantaneamente no app

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Gasto do WhatsApp aparece no saldo, no indicador e no histórico sem recarregar | ❌ | O app não abre o `/ws` (#74) e o assistente não grava (#69). Hoje o fluxo WhatsApp → app não existe |
| 2 | Teste de integração webhook → banco → app | ⚠️ | No repositório não há. A QA testou `registrar` → Valkey → `/ws`: o evento chega em **37 ms** e outro usuário não recebe. Mas um evento publicado logo depois do `conectado` se perde (#75) |
| 3 | Mecanismo documentado no Doc de Arquitetura | ✅ | WebSocket `/ws` autenticado por token, eventos pelo Valkey |

## RF22 · Elemento gráfico de saldo

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Barra na tela principal com o % do dinheiro do mês já gasto | ⚠️ | #76: a barra mostra o que **sobra**, não o que foi gasto |
| 2 | Faixas de cor, sem depender só da cor (ícone ou texto) | ✅ | Verde/amarelo/vermelho com frase abaixo ("Menos da metade do seu dinheiro continua disponível.") |
| 3 | Texto alternativo ("Você já gastou 60% do dinheiro do mês") | ⚠️ | #76: `aria-label="Fração do dinheiro disponível no mês"` + `aria-valuenow`. O leitor lê só o número |

## RF30 · Marcar conta como paga

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Botão "Paga" em cada conta pendente | ✅ | Com nome acessível "Marcar a conta X como paga" |
| 2 | Status muda na hora, com confirmação visual (RF20) | ✅ | `PATCH /api/v1/contas/{id}/pagamento` e lista atualizada |
| 3 | Possível desfazer | ✅ | API e tela. Desfazer conta vencida volta para "em atraso" (teste) |
| 4 | Regra "pagar desconta do saldo?" registrada | ⚠️ | #77: o backend registrou que **não** desconta (`contas/saldo.py`), mas a tela inicial tira só as contas pendentes do saldo. Ao pagar uma conta, o saldo **sobe** |

## RF32 · Lista diária de contas com cores e ícones

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Contas do mês agrupadas por dia | ❌ | #78: lista única ordenada por vencimento, com filtros por situação |
| 2 | Três estados com cor + ícone + texto | ✅ | Relógio "A vencer", alerta "Em atraso", check "Paga" |
| 3 | "Em atraso" calculado pela data, com testes incluindo o fuso de Brasília | ⚠️ | #79: o cálculo usa `America/Sao_Paulo`, mas não há teste da virada do dia (21h–23h59 em Brasília = dia seguinte em UTC) |

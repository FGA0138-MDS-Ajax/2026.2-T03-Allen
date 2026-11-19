# Relatório de QA da Sprint 3

Período planejado: 21/10–25/10 · Validação em 18/11 · Responsável: Beatriz (QA) · Commit: `686ae96` (`dev`)

## Resumo

As quatro issues da S3 (#17–#20) estão fechadas e o código está na `dev`: RF05 pelo PR #83, RF07 pelo PR #84, RF20 e
RF21 com os componentes que vieram do PR #64. A sprint **não passa** no aceite ainda.

O maior problema não é da S3: um merge resolveu mal o conflito da migration `0008_recorrencia_conta.py` e a `dev`
**não sobe num banco novo** (`SyntaxError`), o que também quebra o `scripts/rodar-local.sh` e o CI do backend. Isso
bloqueia o teste em celular que a issue pede.

Na S3, o RF07 não cumpre o critério principal: no QR Code mais comum (2.0 online, usado no DF e em SP) o app só lê a
chave, sem valor e sem nome da loja, e preenche a data com o dia 01. A pessoa idosa precisa digitar o valor de qualquer
jeito. O RF05 funciona e tem legenda, mas três riscos da revisão do PR #83 seguem no código. O RF20 tem dois componentes
de confirmação em vez de um e a exclusão de gasto no Início não confirma nada. O RF21 lê "R$ 1.250,00" para a voz do
aparelho, sem conversão por extenso.

O que está bom: legenda e aviso de "sem áudio" no tour, botão "Ouvir explicação" para reabrir, o leitor de QR com
alternativa de foto e de digitar, a correção do valor acima de R$ 999 e da data fora do mês (achados do PR #84), e a
regressão da S1/S2: 122 testes no backend e 86 no frontend passando.

**Ainda falta** a parte que só dá para fazer com o aparelho na mão: câmera, voz no Chrome Android e no Safari iOS e as
notas fiscais reais de 2 estabelecimentos. Está no [roteiro no celular](roteiro-celular.md), para preencher.

## Números

| Verificação | Resultado |
|---|---|
| Critérios de aceite (16) | 4 ✅ · 6 ⚠️ · 4 ❌ · 2 ⏳ ([detalhes](validacao-criterios.md)) |
| Teste em celular real | ⏳ pendente ([roteiro](roteiro-celular.md)) |
| Notas fiscais reais (mín. 2 estabelecimentos) | ⏳ pendente |
| Parser de NFC-e, execução isolada | 6 tipos de QR e 8 valores digitados; QR 2.0 online sem valor e sem loja; `1,250.00` vira R$ 1,25 |
| Testes do backend (pytest, Postgres 16 local) | 122/122 passaram |
| Migrations num banco novo (`alembic upgrade head`) | ❌ `SyntaxError` na 0008. Com a versão anterior ao merge (`1c77d30`), sobe até a 0010 |
| Lint do backend (`ruff check`) | ❌ 7 erros (2 de sintaxe na 0008, 5 de import) |
| Testes do frontend (vitest) | 86/86 passaram (com `NODE_OPTIONS=--no-experimental-webstorage`; sem isso, 21 falham pelo `localStorage` nativo do Node 25+, o CI usa Node 22) |
| Lint, formatação e build do frontend | ok |
| CI da `dev` em `686ae96` | ❌ Backend (lint), E2E e Trivy falhando |

## Situação dos cartões

| Cartão | Issue | Situação na QA |
|---|---|---|
| RF05 · Tour em áudio | #17 fechada | ⚠️ Funciona com legenda e reabertura. A fala começa sem toque, erro de fala trava o avanço, passo 1 recomeça e "tour visto" é por navegador (achados do PR #83 não tratados) |
| RF07 · QR Code da nota | #18 fechada | ❌ No QR 2.0 online não vem valor nem loja e a data vira dia 01. Spike da SEFAZ não registrado. Câmera só em HTTPS |
| RF20 · Confirmação visual | #19 fechada | ❌ Dois componentes; exclusão no Início sem confirmação; modal sem `aria-live` |
| RF21 · Botão de áudio | #20 fechada | ⚠️ Um botão por tela; lê "R$ 1.250,00" sem extenso; rótulo genérico "Ouvir mensagem" no Início e no Extrato |

## Regressão da S1 e S2

| Fluxo | Situação |
|---|---|
| Bugs da S1 (#54–#62, #82) | Todos fechados |
| Bugs da S2 | Fechados, exceto #67 (link do WhatsApp), #72 (confirmação "sim"/"não"), #74 (app no `/ws`) e #75 (evento perdido) |
| #74 · app escuta o `/ws` | O Início já usa `useTempoReal`, mas a issue segue aberta. Verificar no celular e fechar ou atualizar |
| Backend (contas, pagamento, parcelas, recorrência, identidade, PIN, transações) | 122/122 testes, sem regressão |
| Telas com `h1` (#60) | Todas as páginas têm um `h1` |
| Subir o app do zero (`rodar-local.sh`) | ❌ Quebra na migration 0008 |
| E2E no CI | ❌ O job ainda roda `npx next start` (front antigo em Next.js); o front atual é Vite. Mesmo problema apontado na S2 |

## Bugs registrados

| Issue | Gravidade | Stack | Resumo |
|---|---|---|---|
| #97 | Crítica | back-end | Migration 0008 com erro de sintaxe após o merge `95b23f7` (PR #91): `alembic upgrade head` falha e o app não sobe |
| #98 | Alta | front-end | RF07: QR 2.0 online não traz valor nem loja e a data é preenchida com o dia 01 |
| #99 | Alta | front-end | RF05: tour trava se a fala for bloqueada ou der erro; passo 1 recomeça quando as vozes carregam |
| #100 | Média | front-end | RF20: exclusão no Início sem confirmação e confirmações não anunciadas ao leitor de tela |
| #101 | Média | front-end | RF21: valores lidos como "R$ 1.250,00" e rótulo genérico "Ouvir mensagem" |
| #102 | Média | front-end | RF05: "tour visto" fica no navegador e não é por pessoa |
| #103 | Média | CI | CI: E2E ainda sobe o front em Next.js; Trivy acusa Dockerfile rodando como root |
| #104 | Baixa | front-end | Valor `1,250.00` digitado na nota vira R$ 1,25 sem aviso |

## O que ficou para a próxima sprint

- Corrigir a migration 0008 (#97) antes de qualquer outro teste: sem ela ninguém sobe o app do zero.
- Fazer o teste no celular e com as notas fiscais reais pelo [roteiro](roteiro-celular.md), e só então fechar a #46.
- Decidir em time o escopo do RF07: consultar a SEFAZ pelo backend ou reduzir formalmente a #18 para "lê a chave e a
  pessoa informa o valor" (pendente desde a revisão do PR #84).
- Refazer o job de E2E para o front em Vite.
- Ambiente HTTPS acessível pelo celular (staging ou túnel), necessário para a câmera.

## Riscos

- **Sem staging e sem HTTPS:** a câmera do RF07 não abre pelo IP da rede local; sem um endereço HTTPS a QA não testa o
  cartão como a pessoa idosa vai usar.
- **RF07 promete mais do que entrega:** a US14 diz "sem que eu precise digitar nada", mas na maioria das notas do DF a
  pessoa vai digitar o valor. Se o escopo não for revisto, a demonstração vai mostrar o contrário do cartão.
- **Merge sem CI:** o merge quebrado (`95b23f7`) entrou pelo PR #91, que só rodou a checagem "PR referencia issue"; o
  CI do backend não rodou nele. A DoD pede CI verde antes do merge, e o CI precisa ser obrigatório na proteção da `dev`.
- **Prova única em 21/10 e capacidade reduzida:** a S3 foi entregue com atraso e sem o teste em aparelho; isso se soma às
  pendências de aparelho real e leitor de tela desde a S1.

# Plano de Testes do Vero

Este documento define como a qualidade do Vero é verificada ao longo das sprints. As metas e restrições daqui alimentam as seções correspondentes do Documento de Arquitetura.

## 1. Pirâmide de testes

A maior parte dos testes fica na base (rápidos e baratos); poucos testes ficam no topo (lentos, mas cobrem o fluxo completo).

| Nível | O que cobre | Ferramentas | Onde roda |
|---|---|---|---|
| **Unitário** | Regras de saldo (valor disponível no mês, lançamentos recorrentes), classificação de categorias, parser do assistente (interpretação de "gastei 30 no mercado"), validações de formulário | Backend: pytest. Frontend: Vitest + Testing Library | A cada PR, no CI |
| **Integração** | API + banco (endpoints com PostgreSQL real no CI), webhook do WhatsApp (recebimento, verificação de assinatura, confirmação antes de salvar) | pytest + `TestClient` do FastAPI (httpx) + PostgreSQL do CI; serviços externos (WhatsApp, IA) simulados | A cada PR, no CI |
| **E2E** | Fluxos críticos: cadastro com celular e PIN, registrar gasto, marcar conta como paga | Playwright | Antes de fechar a sprint (rito de QA) e, quando estável, no CI |

Regras gerais:

- Toda regra de negócio nova chega com teste unitário no mesmo PR.
- Integrações externas (WhatsApp, IA, OCR) nunca são chamadas de verdade nos testes automáticos; usamos dublês.
- Bug corrigido ganha um teste que reproduz o problema, para não voltar.

## 2. Acessibilidade (RNF01, WCAG 2.1 AA)

**Automática**

- axe (via `@axe-core/playwright`) nas telas dos fluxos críticos: nenhuma violação crítica ou séria.
- Lighthouse com nota de acessibilidade ≥ 90 nas telas principais.

**Roteiro manual** (a cada sprint, nas telas novas)

1. Navegar a tela inteira só com teclado: foco visível e ordem lógica.
2. Usar leitor de tela (NVDA no Windows ou TalkBack no Android): todo botão e ícone de categoria é anunciado com nome compreensível.
3. Aplicar zoom de 200%: nada se sobrepõe ou some, sem rolagem horizontal.
4. Conferir contraste dos textos e o tamanho dos alvos de toque (mínimo 44×44 px).
5. Conferir a linguagem: sem termos contábeis (RNF02).

## 3. Metas

| Meta | Valor | A partir de |
|---|---|---|
| Cobertura de testes no backend | ≥ 70% (o CI falha abaixo disso) | S1 |
| Cobertura de testes no frontend | Acompanhada, sem bloqueio no CI | S1 |
| RNF04: reconhecimento de áudio e imagem | ≤ 5 s, medido do recebimento da mensagem até a resposta de confirmação | S4 |
| Tempo do pipeline de CI | < 10 min | S1 |
| Acessibilidade automática | 0 violações críticas ou sérias | S3 |

O RNF04 é medido registrando o tempo de cada processamento de áudio e imagem e acompanhando o percentil 95 a cada sprint.

## 4. Restrições

- Testes não usam dados reais de usuários; apenas dados fictícios.
- Segredos de teste vêm de variáveis de ambiente, nunca do código.
- Um PR só pode ser mergeado com o CI verde (lint, formatação, testes, cobertura e build).

## 5. Rito semanal de QA

Todo **domingo**, antes de fechar a sprint:

1. Rodar a regressão: suíte E2E dos fluxos críticos e o roteiro manual de acessibilidade.
2. Validar os critérios de aceite das histórias da sprint.
3. Registrar os bugs encontrados (seção 6).
4. Levar à revisão da sprint um resumo: o que passou, o que falhou e a cobertura atual.

## 6. Registro de bugs

- Cada bug vira uma **issue no GitHub** com o rótulo `bug`, contendo: passos para reproduzir, resultado esperado, resultado obtido, tela ou print e gravidade.
- A issue ganha um cartão no quadro: em **Bloqueado**, se impede alguma entrega, ou na **sprint atual**, se será corrigida nela.
- O PR da correção referencia a issue (`Closes #número`) e inclui um teste que reproduz o bug.

## 7. Teste com usuários reais

- **Quem:** 1 ou 2 pessoas idosas, do público-alvo.
- **Quando:** na **S4** (fluxos básicos) e na **S7** (produto quase completo).
- **Como:** tarefas guiadas (cadastrar-se, registrar um gasto, marcar uma conta como paga, registrar um gasto pelo WhatsApp), com observação sem interferência. Anotamos onde a pessoa hesita, erra ou pede ajuda.
- **Resultado:** os problemas encontrados viram issues e entram no backlog priorizados pelo PO.

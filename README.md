# Vero

[![CI](https://github.com/beatrizbranfb/Vero/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/beatrizbranfb/Vero/actions/workflows/ci.yml)
[![Segurança](https://github.com/beatrizbranfb/Vero/actions/workflows/seguranca.yml/badge.svg?branch=main)](https://github.com/beatrizbranfb/Vero/actions/workflows/seguranca.yml)

**Gestão financeira simples, acessível e sem linguagem contábil.**

O Vero é uma plataforma web de gestão financeira pessoal e familiar, pensada para pessoas com mais dificuldade com tecnologia, como idosos, mas abrangente o bastante para atender qualquer perfil. Com ele, o usuário registra o que entra e sai, sabe quanto ainda tem disponível no mês e é avisado antes de as contas vencerem, pelo aplicativo ou por mensagens no WhatsApp.

Projeto desenvolvido pela equipe **Allen** na disciplina de Métodos de Desenvolvimento de Software (MDS), Universidade de Brasília, 2026/2.

---

## Sumário

- [O problema](#o-problema)
- [A solução](#a-solução)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Planejamento das sprints](#planejamento-das-sprints)
- [Processo de desenvolvimento](#processo-de-desenvolvimento)
- [Documentação](#documentação)
- [Equipe](#equipe)

---

## O problema

Controlar as finanças continua sendo uma tarefa trabalhosa. Muita gente recorre a planilhas, cadernos ou à memória, e os aplicativos disponíveis costumam supor familiaridade com tecnologia e com o vocabulário contábil. Três fatores se destacam:

1. **Registro trabalhoso:** os gastos exigem digitação repetitiva e o tratamento manual de notas e comprovantes.
2. **Retrabalho todo mês:** planilhas obrigam a refazer a estrutura a cada mês, mesmo para contas que se repetem (água, energia, aluguel, salário).
3. **Ferramentas complexas e silenciosas:** são difíceis para quem tem pouca familiaridade com tecnologia e não avisam antes de as contas vencerem.

O resultado é a dificuldade de saber, com segurança, quanto ainda se tem disponível e quando as contas vencem.

## A solução

| | |
|---|---|
| **Para** | Pessoas que desejam organizar suas finanças pessoais e familiares, em especial idosos e pessoas com pouca familiaridade com tecnologia. |
| **Que precisam** | Controlar receitas, despesas e contas a pagar de forma simples, sem refazer o controle a cada mês. |
| **O Vero** | É uma aplicação web de gestão financeira com interface simples e amigável. |
| **Que** | Permite registrar o dinheiro manualmente, por QR Code da nota fiscal ou por mensagens ao assistente do WhatsApp, lança automaticamente os gastos fixos, mostra o valor disponível no mês e avisa sobre as contas antes do vencimento. |
| **Ao contrário de** | Planilhas e aplicativos com linguagem contábil, que exigem refazer o controle todo mês e dependem de muita digitação. |
| **Nosso diferencial** | Interface acessível, registro via WhatsApp (texto, áudio e foto), lançamento automático de gastos fixos, calendário de vencimentos com avisos antecipados e perfil de acompanhante. |

## Funcionalidades

As prioridades seguem o método MoSCoW: **Must** (obrigatório), **Should** (desejável) e **Could** (opcional).

### Acesso e suporte

- Cadastro pelo número de celular e acesso com PIN numérico curto *(Must)*
- Acesso por biometria *(Could)*
- Atalho de um clique para iniciar a conversa com o assistente no WhatsApp *(Must)*
- Navegação guiada por áudio no primeiro acesso *(Should)*
- Perfil de **acompanhante**, para que um familiar ajude a acompanhar as finanças *(Could)*

### Registro de transações

- **No aplicativo:** teclado numérico grande e categorias representadas por ícones *(Must)*; leitura do QR Code da nota fiscal *(Should)*; edição e exclusão no histórico *(Must)*; botão de desfazer por 10 segundos *(Should)*
- **No WhatsApp:** registro por mensagem de texto *(Must)*, áudio *(Should)* ou foto de comprovante *(Should)*, sempre com confirmação antes de salvar e orientação para preenchimento manual quando a leitura falhar *(Must)*
- Lançamento recorrente automático dos gastos fixos *(Should)*
- Tudo que o assistente registra aparece na hora no saldo e no calendário do aplicativo *(Must)*

### Situação financeira

- Valor disponível no mês em destaque na tela inicial *(Must)*
- Indicador gráfico simples de quanto já foi gasto, sem exigir leitura de números *(Must)*
- Botão de áudio ao lado de valores e resumos, para ouvir as informações *(Should)*
- Consulta do saldo pelo WhatsApp *(Should)* e resumo semanal ou mensal enviado pelo assistente *(Could)*

### Contas e vencimentos

- Cadastro de contas com data e valor *(Must)* e de contas fixas mensais *(Should)*
- Lista diária com cores e ícones para contas pagas, a vencer e em atraso *(Must)*, com filtro *(Should)*
- Marcar conta como paga no aplicativo *(Must)* ou respondendo ao aviso no WhatsApp *(Should)*
- Avisos de vencimento com antecedência *(Must)*
- Calendário visual mensal de vencimentos *(Could)*

### Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF01 | Interface usável e acessível para o público-alvo (WCAG 2.1 AA) |
| RNF02 | Simplicidade linguística |
| RNF03 | Aplicação responsiva |
| RNF04 | Reconhecimento de áudio e imagem em até 5 segundos |
| RNF05 | Dados financeiros e biométricos criptografados em trânsito e em repouso, conforme a LGPD |

A lista completa (RF01 a RF34 e histórias de usuário US01 a US34) está nos documentos de [Requisitos](../Docs/Requisitos%20de%20Software%20v1.pdf) e [Backlog](../Docs/Backlog%20v1.pdf).

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, Next.js |
| Banco de dados | PostgreSQL com Supabase |
| Integrações | WhatsApp (texto, áudio e foto), leitura de QR Code de nota fiscal, API REST/JSON sobre HTTPS |
| Infraestrutura | Docker |

O detalhamento de como essas tecnologias se conectam será descrito no Documento de Arquitetura.

## Planejamento das sprints

| Sprint | Entrega | Período | Requisitos |
|:---:|---|---|---|
| 1 | Acesso, cadastro e entrada manual | 07/10 a 11/10 | RF01, RF03, RF08, RF09, RF19, RNF01–03 |
| 2 | Gestão visual, contas e integração de texto | 14/10 a 18/10 | RF04, RF10, RF12, RF17, RF22, RF25, RF30, RF32 |
| 3 | Acessibilidade e OCR | 21/10 a 25/10 | RF05, RF07, RF20, RF21 |
| 4 | Assistente, filtros e alertas | 28/10 a 01/11 | RF14, RF24, RF26, RF28, RF33 |
| 5 | Acompanhante e áudio no WhatsApp | 04/11 a 08/11 | RF06, RF13, RF18, RF23 |
| 6 | Calendário e avisos antecipados | 11/11 a 15/11 | RF27, RF29, RF31, RF34 |
| 7 | Biometria, confirmações e ajustes | 18/11 a 22/11 | RF02, RF11, RF15, RF16 |
| 8 | Requisitos não funcionais e lançamento | 25/11 a 29/11 | Auditoria de segurança (LGPD), testes de desempenho e implantação |

As sprints 3 a 6 são uma proposta inicial e podem ser reordenadas pelo PO conforme a priorização do backlog.

## Processo de desenvolvimento

O projeto segue um ciclo de vida **iterativo e incremental**, com **Scrum** como framework principal e práticas de **XP**:

- **Eventos:** planejamento, alinhamentos diários, revisão com o cliente e retrospectiva a cada sprint.
- **Práticas:** integração contínua, testes unitários das regras de negócio, refatoração, revisão de código por pull request, programação em par em tarefas complexas e padronização de código.
- **Conceito de pronto:** código revisado, testes aprovados, critérios de aceite atendidos e validação do PO.

## Documentação

Os documentos do projeto ficam na pasta [`Docs`](../Docs):

- Documento de Visão do Produto e do Projeto
- Requisitos de Software
- Backlog do Produto
- Planejamento das Sprints
- Documento de Arquitetura *(em elaboração)*
- [Plano de Testes](docs/qualidade/plano-de-testes.md)

## Equipe

| Integrante | Matrícula | Papel |
|---|---|---|
| Andris Geraldo | 251018246 | Product Owner, Arquitetura |
| Beatriz Brandão | 242005202 | Analista de Qualidade, Arquitetura |
| Ryan Hicky | 242005436 | Scrum Master, Desenvolvedor Frontend |
| Sabrina Pariz | 241031979 | Desenvolvedora Frontend |
| João Vitor | 231012254 | Desenvolvedor Backend |
| Gabriel Monsores | 232002735 | Desenvolvedor Backend, Cliente |
| Gabriel Severiano | 231012209 | Desenvolvedor Backend, Cliente |

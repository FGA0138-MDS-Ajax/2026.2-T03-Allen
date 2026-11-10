# Relatório de QA da Sprint 1

Período planejado: 07/10–11/10 · Validação em 09/11 · Responsável: Beatriz (QA)

## Resumo

Os cartões da S1 estão em **Pronto** no Trello, mas a sprint **não passa** no aceite. As telas e a API existem, porém
separadas: o frontend (branch `alteracoes-frontend`, ainda fora da `dev`) é um protótipo navegável que não chama o
backend, e o backend não tem verificação por código, recuperação de PIN nem lançamentos/saldo. Os componentes de
acessibilidade estão bons: teclado numérico, categorias, confirmação, contraste e foco passaram.

Como ainda não existe staging, a validação foi feita localmente, com o backend da `dev` (commit `1881226`) num Postgres
em Docker e o frontend em build de produção.

## Números

| Verificação | Resultado |
|---|---|
| Critérios de aceite (33) | 16 ✅ · 10 ⚠️ · 3 ❌ · 4 ⏳ ([detalhes](validacao-criterios.md)) |
| Testes do backend (pytest) | 20/20 passaram · cobertura 78% (módulo de identidade: 38–59%, sem testes próprios) |
| Testes do frontend (vitest) | 35/35 passaram · build ok |
| E2E Playwright (360px e 1280px) | 30/30 passaram: fluxo principal, valor zero, PIN incompleto, axe nas 6 telas, zoom 200% |
| Roteiro de acessibilidade | [resultado por tela](roteiro-acessibilidade.md) · 2 itens dependem de aparelho real |
| Bugs registrados | 9 (2 críticos, 2 altos, 4 médios, 1 baixo) |

## Situação dos cartões

| Cartão | Coluna no Trello | Situação na QA |
|---|---|---|
| RF03 · Cadastro por celular | Pronto | ❌ API exige e-mail/senha (#54), sem código de verificação (#55) |
| RF01 · Acesso por PIN | Pronto | ⚠️ Hash e bloqueio ok na API, mas o login da tela aceita qualquer PIN (#56) e não há "Esqueci meu PIN" (#55) |
| RF08 · Teclado numérico | Pronto | ✅ Todos os critérios |
| RF09 · Categorias por ícones | Pronto | ⚠️ Rótulo pequeno (#59), lista fora do back-end (#57) |
| RF19 · Saldo na tela inicial | Pronto | ❌ Não existe API de saldo (#57). Na tela, funciona com dados do navegador |
| RNF01 · Acessibilidade WCAG | Pronto | ⚠️ Menu fora do tamanho mínimo (#58), sem `h1` na tela inicial (#60) |
| RNF02 · Guia de linguagem | Pronto | ⏳ `docs/linguagem.md` não existe e há termos a trocar (#61) |
| RNF03 · Responsividade | Pronto | ⚠️ Sem rolagem horizontal em 360px e 1280px. Falta testar 768px e aparelhos reais |

## O que passou

- Teclado numérico (RF08) completo: teclas de 64px, valor em R$ ao digitar, "Apagar" visível e bloqueio de valor zero.
- Na API: validação do celular BR, mensagem de celular repetido, PIN com bcrypt e bloqueio de 30 s após 5 erros.
- Nenhuma violação grave do axe (WCAG 2.1 AA) nas 6 telas, e nenhuma rolagem horizontal em 360px nem com zoom de 200%.
- Mensagens de erro da API no formato "o que aconteceu + o que fazer".
- Fluxo E2E cadastro → código → PIN → login → gasto → saldo automatizado e agora no CI (job `e2e`, com relatório como artefato).

## Bugs registrados

| Issue | Gravidade | Resumo |
|---|---|---|
| #56 | Crítica | Telas de cadastro, login e gasto não usam a API |
| #57 | Crítica | Não existe API de lançamentos/saldo nem lista única de categorias |
| #54 | Alta | Cadastro na API exige e-mail e senha |
| #55 | Alta | Falta verificação do celular por código e "Esqueci meu PIN" na API |
| #58 | Média | Links do menu superior com 32px de altura e fonte abaixo de 16px |
| #59 | Média | Rótulos das categorias com 13px no celular |
| #61 | Média | "Login" e "senha" na tela de PIN; guia de linguagem não existe |
| #62 | Média | Celular gravado em texto puro no banco |
| #60 | Baixa | Tela inicial sem `h1` |

## O que ficou para a próxima sprint

- Corrigir os 9 bugs acima. Os cartões RF03, RF01, RF09, RF19 e RNF02 deveriam voltar de **Pronto** para desenvolvimento.
- Levar o frontend para a `dev` e integrar com a API. Quando isso acontecer, o E2E precisa trocar os dados do navegador
  por um usuário de teste e pelo código simulado (`E2E_CODIGO_VERIFICACAO`).
- Ambiente de staging, que continua sendo pré-requisito para o aceite oficial.
- Itens que dependem de aparelho real: escuta com TalkBack/NVDA, teclado do sistema sobre o botão, Chrome Android, Safari iOS e 768px.
- Testes do módulo de identidade no backend (cadastro, PIN e bloqueio estão sem testes próprios).

## Riscos

- **Cartões em Pronto sem passar no aceite:** a DoD exige validação da QA antes de mover para Pronto.
- **Front e back divergentes:** o cadastro da tela (nome + celular) não bate com o da API (nome + celular + e-mail + senha). Precisam alinhar antes de integrar.
- **Sem staging:** a inspeção do repositório é em 16/11, e a S1 ainda não foi validada no ambiente oficial.

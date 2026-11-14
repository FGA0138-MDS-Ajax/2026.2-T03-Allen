# Sprint 1: validação dos critérios de aceite

Ambiente: **local** (ainda não existe staging), com o backend da `dev` (commit `1881226`) num Postgres 17 em Docker e o
frontend da branch `alteracoes-frontend` em build de produção · Data da validação: 09/11 · Responsável: Beatriz (QA)

Legenda: ✅ passou · ❌ falhou (abrir issue) · ⚠️ passou em parte · ⏳ não entregue · ➖ não se aplica

> O frontend ainda não chama a API: cadastro, login e gastos funcionam só como protótipo navegável, com os dados no
> navegador (#56). Por isso cada critério foi conferido nas duas pontas, e o status mostra o pior dos dois lados.

## RF03 · Cadastro por número de celular

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Cadastro pede celular (com DDD), nome, e-mail (para recuperar o PIN) e PIN, sem senha | ❌ | #54: a API exige senha e o PIN só é criado depois; a tela pede só nome e celular. Critério atualizado em 10/11: e-mail obrigatório por decisão do time |
| 2 | Número validado no formato BR | ✅ | API recusa `123` com 422 e normaliza para `55DDDNÚMERO`. A tela ainda não valida (#56) |
| 3 | Número verificado por código (SMS ou WhatsApp) | ⏳ | #55: a tela `/codigo-sms` existe, mas não há envio nem conferência de código |
| 4 | Número já cadastrado mostra mensagem clara oferecendo "Entrar" | ⚠️ | API devolve 409 com "Este celular já está cadastrado. Tente entrar na sua conta."; a tela não mostra (#56) |
| 5 | Telefone armazenado protegido e ausente dos logs (RNF05) | ⚠️ | #62: fica fora dos logs de acesso, mas é gravado em texto puro |

## RF01 · Acesso por PIN numérico curto

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | PIN numérico criado no cadastro (tamanho definido pelo time) | ⚠️ | 4 a 6 dígitos na API (recusa 3 dígitos e letras). Só pode ser criado depois de entrar com senha (#55) |
| 2 | Teclado numérico grande na tela de login | ✅ | Teclas de 64px, com nomes acessíveis ("1"…"9", "Limpar", "Apagar") |
| 3 | PIN guardado com hash (bcrypt/argon2), nunca em texto puro | ✅ | `hashPin` com bcrypt (`$2b$12$`) |
| 4 | Bloqueio temporário após N tentativas erradas, com mensagem simples | ✅ | Bloqueia por 30 s após 5 erros, inclusive para o PIN certo: "Muitas tentativas erradas. Espere 30 segundos e tente de novo." |
| 5 | Fluxo "Esqueci meu PIN" via verificação do celular | ⏳ | #55: só as telas existem, sem API. O texto fala em "senha" (#61) |

## RF08 · Digitação em teclado numérico

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Teclado próprio com botões ≥ 44px e alto contraste | ✅ | 64px de altura, borda escura, sem violações do axe |
| 2 | Valor exibido em R$ enquanto digita (1250 → R$ 12,50) | ✅ | Coberto pelo E2E |
| 3 | Botão de apagar visível | ✅ | "Apagar" com ícone e texto |
| 4 | Valor zero ou vazio não pode ser salvo | ✅ | "Salvar" desabilitado, com a dica "Digite um valor maior que zero para salvar." (E2E) |
| 5 | Funciona em celular de 360px | ✅ | E2E no projeto `celular-360` |

## RF09 · Seleção de categoria por ícones

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Categoria obrigatória no registro manual | ✅ | Sempre há uma selecionada (Mercado por padrão) |
| 2 | Cada categoria tem ícone + rótulo curto | ⚠️ | #59: rótulos com 13px no celular |
| 3 | Ícones com texto alternativo para leitor de tela | ✅ | Ícone com `aria-hidden` e botão nomeado pelo rótulo, com `aria-pressed` |
| 4 | Lista de categorias definida num único lugar do back-end (mesma do RF12) | ❌ | #57: lista fixa em `frontend/src/lib/categorias.ts` |

## RF19 · Saldo disponível na tela inicial

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Tela inicial mostra "Disponível no mês" em fonte grande | ✅ | "Você ainda tem disponível no mês:" com o valor em 34–50px |
| 2 | Saldo = receitas − gastos do mês, com testes unitários (virada de mês, negativos) | ❌ | #57: regra só no frontend (`lib/lancamentos.ts`, com testes). Não existe API de saldo |
| 3 | Saldo atualiza logo após registrar um gasto manual | ⚠️ | Funciona no protótipo (E2E), mas com dados do navegador (#56) |
| 4 | Legível com zoom de 200% sem quebrar o layout | ✅ | Sem rolagem horizontal a 640px com escala 2 (E2E) |

## RNF01 · Acessibilidade WCAG 2.1 AA

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Guia de estilo: contraste ≥ 4.5:1, corpo ≥ 16px, tamanho mínimo de botão, foco visível | ⚠️ | Contraste e foco ok. #58 (menu com 32px e 15,75px) e #59 (categorias com 13px) |
| 2 | Componentes base acessíveis (botão, campo, teclado numérico, confirmação) | ✅ | Diálogo de confirmação leva o foco ao título; mensagens com `role="status"`/`role="alert"` |
| 3 | Teste axe automatizado rodando no CI | ⚠️ | O axe roda no E2E, que entrou no `ci.yml` (job `e2e`). Fica ativo quando o frontend chegar à `dev` |

## RNF02 · Simplicidade linguística

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | `docs/linguagem.md` com regras e lista de palavras proibidas/substitutas | ⏳ | #61 |
| 2 | Mensagens de erro no formato "o que aconteceu + o que fazer" | ✅ | API: "Este celular já está cadastrado. Tente entrar na sua conta.", "Alguns dados não estão certos. Confira e tente de novo." |
| 3 | Textos de cada tela revisados pela QA | ⚠️ | Revisados: "Login" no menu e "senha" na tela de PIN (#61) |

## RNF03 · Aplicativo responsivo

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Testado em 360px, 768px e 1280px | ⚠️ | 360px e 1280px no E2E. 768px ainda não testado |
| 2 | Sem rolagem horizontal | ✅ | Todas as 6 telas, em 360px, 640px (zoom 200%) e 1280px |
| 3 | Testes E2E em viewport de celular no CI | ⚠️ | Job `e2e` no CI com o projeto `celular-360`, pendente do frontend na `dev` |
| 4 | Funciona em Chrome Android e Safari iOS | ⏳ | Precisa de aparelho real ou de staging |

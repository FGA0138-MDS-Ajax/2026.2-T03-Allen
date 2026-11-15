# Sprint 1: roteiro manual de acessibilidade

Segue o roteiro da seção 2 do [plano de testes](../plano-de-testes.md). Repetir para cada tela da S1:
**Cadastro**, **Verificação do código**, **Criação do PIN**, **Login com PIN**, **Registrar gasto** (teclado + categorias) e **Tela inicial (saldo)**.

Ambiente: local, frontend da branch `alteracoes-frontend` · Dispositivo/navegador: Chromium (Playwright) em 360×800, 640×400 com escala 2 e 1280×720 · Data: 09/11

Legenda: [x] passou · [ ] falhou ou pendente (ver observação)

> Nesta rodada, a árvore de acessibilidade foi conferida com o Playwright (nomes acessíveis, papéis e `aria-live`).
> A escuta com TalkBack ou NVDA de verdade fica para quando houver staging. O item pendente está marcado abaixo.

## 1. Leitor de tela (TalkBack no Android ou NVDA no Windows)

- [x] Título da tela anunciado ao abrir: `<title>` próprio e `lang="pt-BR"` em todas as telas
- [ ] Título principal `<h1>` em todas as telas: falta na tela inicial (#60)
- [x] Todo botão é anunciado com nome compreensível (axe sem `button-name`/`link-name`)
- [x] Teclas do teclado numérico anunciadas como números ("1", "2"…, "Limpar", "Apagar"), dentro do grupo "Teclado numérico"
- [x] Ícones de categoria anunciados pelo rótulo ("Mercado", "Farmácia"…), com `aria-pressed` indicando a escolhida
- [x] Campos com rótulo associado ("Seu nome completo", "Número de celular com DDD", "Código recebido por SMS")
- [x] Mensagens de erro e de confirmação anunciadas sem precisar mover o foco (`role="alert"`, `role="status"`, `aria-live` no valor)
- [x] Saldo anunciado com valor e moeda ("Você ainda tem disponível no mês: R$ …"), com o botão "Ouvir"
- [x] Ordem de leitura segue a ordem visual
- [ ] Escuta real com TalkBack/NVDA: pendente (sem staging nem aparelho nesta rodada)

## 2. Zoom de 200% (navegador desktop, 1280px)

- [x] Nenhum texto cortado, sobreposto ou escondido
- [x] Sem rolagem horizontal (E2E: as 6 telas a 640px com escala 2)
- [x] Teclado numérico continua utilizável
- [x] Saldo da tela inicial continua legível e inteiro

## 3. Celular 360px (aparelho real ou DevTools em 360×800)

- [x] Sem rolagem horizontal em nenhuma tela (E2E `celular-360`)
- [ ] Alvos de toque ≥ 44×44px: teclas (64px), categorias e botões ok, mas os links do menu superior têm 32px (#58)
- [x] Teclado numérico próprio cabe inteiro na tela. Obs.: no login ele termina em 877px, então é preciso rolar um pouco para ver o "Entrar"
- [ ] Teclado do sistema não cobre o botão de confirmar: pendente (precisa de aparelho real)

## 4. Complementares

- [x] Navegação só com teclado (Tab/Shift+Tab/Enter): foco visível em todos os elementos e ordem lógica. O teclado numérico também aceita as teclas do computador
- [x] Contraste de texto ≥ 4.5:1 (axe sem `color-contrast` em nenhuma tela)
- [ ] Linguagem sem termos contábeis ou técnicos (RNF02): "Login" no menu e "senha" na tela de PIN (#61)
- [ ] Texto ≥ 16px: menu com 15,75px (#58) e categorias com 13px (#59)

## Resultado por tela

| Tela | Leitor de tela | Zoom 200% | 360px | Issues |
|---|---|---|---|---|
| Cadastro | ✅ | ✅ | ⚠️ | #58 |
| Verificação do código | ✅ | ✅ | ⚠️ | #58 |
| Criação do PIN | ✅ | ✅ | ⚠️ | #58 |
| Login com PIN | ✅ | ✅ | ⚠️ | #58, #61 |
| Registrar gasto | ✅ | ✅ | ⚠️ | #58, #59 |
| Tela inicial (saldo) | ⚠️ | ✅ | ⚠️ | #58, #60 |

Cada falha vira issue com o template **Bug** (rótulo `bug`).

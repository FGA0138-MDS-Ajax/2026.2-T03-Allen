# PR #83 · RF05 · Explicação guiada em áudio no primeiro acesso

Data: 14/11/2026 · Responsável: Beatriz (QA) · Issue: #17 · Commit: `7b5a392` · Branch: `feature/RF05-navegacao-audio` → `dev`

## Ambiente

- Arch Linux, Node 22.
- Código obtido pelo tarball do commit `7b5a392` via API do GitHub; dependências com `npm ci --ignore-scripts`.
- O comportamento da fala (Web Speech API) **não** foi testado em navegador; os achados de fala são por análise de código.

## Testes automatizados

| Verificação | Comando (em `frontend/`) | Resultado |
|---|---|---|
| Testes unitários (Node 22) | `npx vitest run` | ✅ 65/65 (18 arquivos) |
| Tipos | `npx tsc -b` | ✅ |
| Lint | `npx eslint .` | ✅ |
| Formatação | `npx prettier --check src` | ✅ |
| CI no GitHub | — | ⚠️ Só rodou "PR referencia issue" (o `ci.yml` dispara apenas em PR para `main`) |

## Critérios de aceite (#17)

| Critério | Resultado | Observação |
|---|---|---|
| No primeiro acesso, tour em áudio explica botões e telas | ⚠️ | Abre sozinho após o login, mas o "primeiro acesso" é por navegador, não por usuário (achado 3), e a fala pode não sair (achados 1 e 2) |
| Controles grandes de pausar, repetir e pular | ✅ | "Continuar" recomeça o passo em vez de retomar (achado 5) |
| Pode ser reativado ("Ouvir explicação") | ✅ | Botão na barra de navegação |
| Legenda/texto equivalente | ✅ | Mesmo texto da fala exibido no modal |

## Achados

### 1. Tour trava se o navegador bloquear a fala sem interação

- Método: Risco (análise de código; não reproduzido em navegador)
- Onde: `frontend/src/components/TourAudio/TourAudio.tsx`, efeito que chama `speechSynthesis.speak`
- Evidência: o tour fala sem toque na tela. Chrome e Safari recusam `speak()` sem interação prévia (ex.: primeiro acesso logado após F5). A fala dispara `onerror`, que só zera `falando`; o tour fica no passo 1 em "Em espera", sem aviso e sem avançar
- Esperado: tratar o erro (avisar e pedir um toque) ou iniciar o tour por botão

### 2. Qualquer erro de fala para o avanço automático

- Método: Risco (análise de código)
- Evidência: o avanço depende só do `onend`. Vozes do Google no Chrome, priorizadas por `pontuarVoz` em `servicos/voz.ts`, costumam cortar falas longas (passos 2 e 4) sem disparar `onend`
- Esperado: fallback no `onerror` ou textos divididos; testar no Chrome

### 3. "Tour visto" é por navegador, não por usuário

- Método: Análise de código
- Onde: `servicos/tourAudio.ts` (chave `vero_tour_audio_visto`); `servicos/api.ts`, `limparSessao` não remove a chave
- Evidência: uma segunda pessoa no mesmo aparelho nunca vê o tour do primeiro acesso

### 4. Passo 1 é cortado e recomeça quando as vozes carregam

- Método: Análise de código
- Onde: `TourAudio.tsx`, `voz` nas dependências do efeito de fala
- Evidência: quando `voiceschanged` chega depois da primeira fala (comum no Chrome), o efeito reexecuta, cancela e fala o passo de novo

### 5. Menores (análise de código)

- "Pausar" cancela a fala; "Continuar" recomeça o passo do início.
- Modal não fecha com Esc nem prende o foco.
- Aberto pelo botão na tela Anotar, os dígitos digitados vão para o teclado numérico atrás do modal.
- Não verificado: se o envio de gasto pelo WhatsApp, citado no passo 7 do tour, já funciona na `dev`.

## Conclusão

**Alterações pedidas.** Para aprovar: tratar os achados 1 a 4 e testar a fala no Chrome e no Safari (celular) com
registro nesta pasta.

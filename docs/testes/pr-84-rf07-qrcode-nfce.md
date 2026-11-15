# PR #84 · RF07 · Leitura do QR Code da nota fiscal

Data: 14/11/2026 · Responsável: Beatriz (QA) · Issue: #18 · Commit: `9058407` · Branch: `feat/rf07-qrcode-nfce` → `dev`

## Ambiente

- Arch Linux, Node 22 (testes e build) e Node 25.8.0 (comparação).
- Código obtido pelo tarball do commit `9058407` via API do GitHub; dependências com `npm ci --ignore-scripts`.
- Sem aparelho móvel: câmera e leitura de foto **não** foram testadas em dispositivo real.

## Testes automatizados

| Verificação | Comando (em `frontend/`) | Resultado |
|---|---|---|
| Testes unitários (Node 22) | `npx vitest run` | ✅ 57/57 (15 arquivos) |
| Testes unitários (Node 25) | `npx vitest run` | ❌ 14 falhas: `localStorage.clear is not a function`. O `localStorage` nativo do Node 25 sobrepõe o jsdom; mesmo erro na `dev`, não é causado pelo PR |
| Build | `vite build` (Node 22) | ✅ |
| Tipos | `npx tsc -b` | ✅ |
| Lint | `npx eslint .` | ✅ |
| Formatação | `npx prettier --check src` | ✅ |
| CI no GitHub | — | ⚠️ Só rodou "PR referencia issue". O `ci.yml` dispara apenas em PR para `main`, então PRs para `dev` não rodam lint, testes nem build |

## Critérios de aceite (#18)

| Critério | Resultado | Observação |
|---|---|---|
| Botão abre a câmera e lê o QR Code da NFC-e | ✅ | Verificado no código; não testado em celular |
| Extrai valor total, data e estabelecimento e mostra para confirmar | ⚠️ | A tela de confirmação existe. No QR 2.0 (padrão atual) não vêm valor nem nome, e a data é estimada; só o QR 1.0 e o JSON de teste trazem os três |
| Se falhar: mensagem simples + opção de digitar | ✅ | QR ilegível, câmera negada e sem câmera. "SEFAZ fora do ar" não se aplica: não há consulta |
| Spike de consulta à NFC-e por estado | ❌ | Não encontrado; card no Trello segue ⛔ Bloqueado |

## Achados

### 1. Valor acima de R$ 999 é salvo errado

- Método: **Executado** (expressão do PR isolada no Node)
- Onde: `frontend/src/pages/AnotarGasto/AnotarGasto.tsx`, função `confirmarNfce`
- Passos: aplicar a mesma limpeza do PR ao texto `1.234,56`:
  ```
  node -e 'const v="1.234,56"; const l=v.replace(/[^\d.,]/g,"").replace(",","."); const n=parseFloat(l); console.log(l, n, Math.round(n*100))'
  ```
- Esperado: 123456 centavos (R$ 1.234,56)
- Obtido: `1.234.56 1.234 123`, ou seja, **R$ 1,23**, sem aviso

### 2. Mês e ano da data da nota são descartados

- Método: Análise de código
- Onde: `AnotarGasto.tsx`, `confirmarNfce` (`nfcePendente.data.split('-')[2]`); `servicos/dadosDoMes.ts` guarda só o mês atual
- Evidência: só o dia é repassado a `adicionarLancamento`. Uma nota de 28/10 é gravada como dia 28 do mês corrente (28/11, no futuro). O campo `type="date"` não tem `min`/`max`
- Esperado: limitar ao mês atual até hoje, ou avisar quando a nota é de outro mês

### 3. Descrição e categoria ruins no QR 2.0

- Método: Análise de código
- Onde: `frontend/src/utils/nfce.ts`, `parsearQrCodeNfce`
- Evidência: sem nome da loja, a descrição salva é "Compra (UF) · CNPJ ..." e aparece assim no Extrato; `sugerirCategoriaPorEstabelecimento` cai sempre em "mercado"

### 4. Menores (análise de código)

- O QR 2.0 de contingência traz dia e valor no `p` (`chave|2|tpAmb|dia|vNF|...`); o parser ignora.
- O caminho JSON aceita qualquer `{"valor": ...}` como nota fiscal em produção.
- Modal do leitor não fecha com Esc nem prende o foco; após falha na foto, a câmera ao vivo não volta.
- Sem testes para `LeitorQrCode` e para o fluxo de confirmação do `AnotarGasto`.
- Descrição do PR com formatação quebrada.

## Conclusão

**Alterações pedidas.** Para aprovar: corrigir os achados 1 e 2, e decidir em time entre consultar a SEFAZ pelo backend
ou reduzir formalmente o escopo da #18 para "lê a chave e o usuário informa o valor".

# Registro de testes

Todo teste feito no Vero (revisão de PR, aceite de sprint, teste manual ou com usuário) fica registrado nesta pasta, em
um arquivo `.md` por rodada. O objetivo é que qualquer pessoa consiga saber **o que foi testado, em qual versão, como, e
qual foi o resultado**, e consiga repetir o teste.

Os relatórios de aceite de sprint continuam em `qualidade/` (ver o [plano de testes](../qualidade/plano-de-testes.md)); aqui ficam os testes do dia a dia.

## Índice

| Data | Arquivo | Alvo | Issue | Resultado |
|---|---|---|---|---|
| 14/11/2026 | [pr-83-rf05-tour-audio.md](pr-83-rf05-tour-audio.md) | PR #83 · `feature/RF05-navegacao-audio` | #17 | ❌ Alterações pedidas |
| 14/11/2026 | [pr-84-rf07-qrcode-nfce.md](pr-84-rf07-qrcode-nfce.md) | PR #84 · `feat/rf07-qrcode-nfce` | #18 | ❌ Alterações pedidas |
| 14/11/2026 | [2026-11-14-script-rodar-local.md](2026-11-14-script-rodar-local.md) | PR #89 · `chore/script-rodar-local` | #88 | ✅ Aprovado |

## Como nomear

- Revisão de PR: `pr-<número>-<rf>-<assunto>.md`
- Teste manual ou exploratório: `AAAA-MM-DD-<assunto>.md`

## Legenda do método

Cada achado diz como foi verificado, para não confundir o que foi executado com o que foi deduzido lendo o código:

- **Executado**: rodado de fato (comando, teste automatizado, navegador); a saída está no registro.
- **Análise de código**: encontrado lendo o diff; o trecho e o raciocínio estão no registro.
- **Risco**: depende de ambiente (navegador, aparelho) e ainda não foi reproduzido.

## Modelo

```markdown
# <Alvo do teste>

Data: DD/MM/AAAA · Responsável: <nome> · Issue: #<n> · Commit: `<sha curto>`

## Ambiente
SO, versão do Node/Python, navegador, como o código foi obtido.

## Testes automatizados
| Verificação | Comando | Resultado |
|---|---|---|

## Critérios de aceite
| Critério | Resultado | Observação |
|---|---|---|

## Achados
### 1. <título>
- Método: Executado | Análise de código | Risco
- Onde: `arquivo:linha`
- Passos / evidência:
- Esperado:
- Obtido:

## Conclusão
Aprovado | Alterações pedidas, e o que falta para aprovar.
```

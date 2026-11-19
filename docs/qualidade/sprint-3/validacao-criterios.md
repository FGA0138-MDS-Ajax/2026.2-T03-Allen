# Sprint 3: validação dos critérios de aceite

Ambiente: **local** (ainda não existe staging). Data da validação: 18/11 · Responsável: Beatriz (QA) · Commit: `686ae96` (`dev`)

As quatro issues da S3 (#17–#20) estão fechadas. RF05 entrou pelo PR #83 e RF07 pelo PR #84. RF20 e RF21 não têm PR
próprio: os componentes `ConfirmacaoSucesso`, `AlertaStatus` e `BotaoAudio` vieram do PR #64 (frontend da S2).

Esta rodada cobre testes automatizados, execução isolada de funções e análise de código. A parte em **celular real**
(câmera, áudio, notas fiscais de verdade) segue o [roteiro no celular](roteiro-celular.md) e está marcada com ⏳ até ser
preenchida.

Legenda: ✅ passou · ❌ falhou (abrir issue) · ⚠️ passou em parte · ⏳ aguardando teste no celular · ➖ não se aplica

## RF05 · Navegação guiada por áudio no primeiro acesso (#17)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | No primeiro acesso, um tour em áudio explica os botões e as telas principais | ⚠️ ⏳ | #99. 8 passos cobrindo Início, Ouvir, Anotar, Extrato, Contas e WhatsApp. Os achados 1, 2 e 4 da [revisão do PR #83](../../testes/pr-83-rf05-tour-audio.md) **continuam no código**: a fala começa sem toque (o Safari do iPhone costuma recusar), qualquer erro de fala para o avanço e o passo 1 recomeça quando as vozes carregam. Confirmar no celular (roteiro, C1–C4) |
| 2 | Controles grandes de pausar, repetir e pular | ⚠️ | Botões com `min-height: var(--toque-teclado)` e texto + ícone. "Pausar" cancela a fala e "Continuar" recomeça o passo do início, em vez de continuar de onde parou |
| 3 | Pode ser reativado depois (botão "Ouvir explicação") | ✅ | Botão "Ouvir explicação" na barra de navegação (`BarraNavegacao.tsx`) |
| 4 | Legenda/texto equivalente disponível | ✅ | O mesmo texto falado aparece na tela (`#tour-legenda`). Sem voz no aparelho, mostra aviso e deixa seguir por "Pular" |
| – | (extra) "Tour visto" é por pessoa | ❌ | #102. A marca fica no navegador (`vero_tour_audio_visto`) e não é apagada ao sair. Uma segunda pessoa no mesmo aparelho nunca ouve o tour (achado 3 do PR #83) |

## RF07 · Escaneamento de QR Code da nota fiscal (#18)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Botão abre a câmera e lê o QR Code da NFC-e | ⏳ | Usa `getUserMedia` + `@zxing/library`, com alternativa de tirar foto. A câmera **só abre em HTTPS**: pelo IP da rede (`http://192.168...`) só sobra a foto. Ver preparação do roteiro |
| 2 | Extrai valor total, data e nome do estabelecimento e mostra para confirmar | ❌ | A tela de confirmação existe e é editável, e a data vem certa (hoje, se a nota é do mês; de outro mês, avisa e pede para ajustar). Mas no QR 2.0 *online*, o mais comum (DF, SP), o código só traz a chave: **sem valor e sem nome da loja**. Ninguém consulta a SEFAZ (decisão de escopo pendente desde a revisão do PR #84). Não é bug de código: a #98, aberta sobre a data e a descrição, foi fechada como falso positivo |
| 3 | Se falhar: mensagem simples + opção de digitar | ✅ | QR que não é de nota → "não reconhecido" e volta para o teclado. Valor vazio ou zero e data fora do mês são barrados com mensagem. "SEFAZ fora do ar" não se aplica porque não há consulta |
| 4 | Spike técnico: validar a consulta à NFC-e antes da sprint | ❌ | Não há registro do spike no repositório nem na issue |

Executado (parser isolado no Node, `utils/nfce.ts`):

| Entrada | Resultado |
|---|---|
| QR 2.0 online DF `?p=<chave>\|2\|1\|1\|<hash>` | válido, UF DF, CNPJ ok, `centavos: null`, `estabelecimento: ""`. Data: hoje se a chave é do mês atual; dia 01 (com aviso na tela) se for de outro mês |
| QR 2.0 online SP | igual ao DF |
| QR 2.0 contingência GO `...\|15\|87.90\|...` | válido, R$ 87,90, dia 15 |
| QR v1 com `vNF=1234.56` | válido, R$ 1.234,56 |
| URL qualquer | inválido |
| Valor digitado `1.234,56` / `R$ 45,90` / `12,5` | 123456 / 4590 / 1250 centavos ✅ (achado 1 do PR #84 corrigido) |
| Valor digitado `1,250.00` | **125 centavos (R$ 1,25)**, sem aviso (#104) |

A data fora do mês atual agora é barrada (achado 2 do PR #84 corrigido).

## RF20 · Respostas visuais de confirmação (#19)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Componente único (ícone + texto + cor) usado em todas as ações | ❌ | #100. Há dois: o modal `ConfirmacaoSucesso` (só em Anotar gasto) e o `AlertaStatus` de sucesso (Contas, Extrato). Excluir um gasto pela tela Início fecha o modal **sem nenhuma confirmação** |
| 2 | Anunciado para leitor de tela (`aria-live`) | ⚠️ | #100. `AlertaStatus` tem `role="status"` + `aria-live`, mas é criado junto com o texto, e leitores de tela costumam ignorar região viva recém-criada. `ConfirmacaoSucesso` não tem `aria-live` e a mensagem não está ligada ao diálogo (`aria-describedby`): o foco vai para "Tudo certo!" e o valor salvo pode não ser lido. Confirmar com TalkBack (roteiro, C12) |
| 3 | Visível por ≥ 5 s ou até o usuário fechar | ✅ | Os dois ficam até a pessoa fechar ou fazer outra ação. O "Desfazer" fica 10 s |

## RF21 · Botão de áudio para leitura de valores (#20)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Alto-falante ao lado de todo valor e resumo | ⚠️ | Um botão por tela: saldo (Início), resumo do Extrato e resumo de Contas. Itens do extrato e cada conta não têm |
| 2 | Lê em português natural, não "R$ 1.250,00" | ⚠️ ⏳ | #101. O texto enviado à voz é `formatarMoeda`, ou seja, literalmente "R$ 1.250,00". Não existe conversão por extenso; a leitura depende da voz do aparelho. Confirmar no celular (roteiro, C9–C10) |
| 3 | Funciona no Chrome Android e no Safari iOS | ⏳ | Web Speech API. Sem suporte, aparece um `alert` |
| 4 | Rótulo acessível ("Ouvir saldo") | ⚠️ | #101. Contas usa "Ouvir resumo de contas". Início e Extrato usam o padrão "Ouvir mensagem: <texto inteiro>" |

## Resumo

| RF | ✅ | ⚠️ | ❌ | ⏳ só celular |
|---|---|---|---|---|
| RF05 (4 + 1 extra) | 2 | 2 | 1 | – |
| RF07 (4) | 1 | – | 2 | 1 |
| RF20 (3) | 1 | 1 | 1 | – |
| RF21 (4) | – | 3 | – | 1 |
| **Total (16)** | **4** | **6** | **4** | **2** |

Os ⚠️ marcados também com ⏳ dependem do celular para virar ✅ ou ❌.

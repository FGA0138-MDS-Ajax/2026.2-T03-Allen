# Sprint 4: validação dos critérios de aceite

Ambiente: **local** (ainda não existe staging), com banco novo (`vero_qa`, todas as migrations) · Data: 23/11 ·
Responsável: Beatriz (QA) · Commit: `e2b3c19` (`dev`)

Os sete cartões da S4 (#21–#27) estão fechados. A validação seguiu o caminho da persona fictícia
[Dona Lurdes](persona.md), de 74 anos e com pouca familiaridade com internet:

- **app:** Chromium com tela de 360 px e toque (Playwright), contra a API e o banco de verdade, sem simulação;
- **WhatsApp:** o roteador do assistente foi chamado direto, com as frases do jeito dela; só o envio pela Evolution
  API foi interceptado.

Legenda: ✅ passou · ❌ falhou (issue aberta) · ⚠️ passou em parte · ⏳ depende de algo fora do alcance da QA local
· 🔧 corrigido em PR aberto (status antes da correção ao lado)

## RF14 · Assistente lê fotos de comprovantes (#21)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Foto de comprovante, nota ou conta → valor, tipo e categoria | ❌ 🔧 | **#132: o código não está na `dev`.** O PR #130 foi mergeado na branch do #129, 14 s depois de o #129 entrar, e a #21 foi fechada assim mesmo. Na branch da correção (PR #144) o fluxo funciona com o leitor falso; a leitura real com a API do Claude ficou ⏳ (sem `AI_API_KEY` no ambiente). No teste apareceu "Quanto foi esse gasto com ?" com a foto ilegível, corrigido no mesmo PR |
| 2 | Resposta em até 5 s (RNF04), medida desde esta sprint | ⏳ | Sem a chave, só deu para medir o caminho sem a IA: 20 amostras, média **12 ms**, pior caso **21 ms**. O tempo total vai depender quase todo da API. Script pronto para as 20 amostras reais: `scripts/medir-rnf04.py` |
| 3 | Imagem guardada com segurança ou descartada (LGPD) | ✅ | Revisão de código: a imagem só fica na memória e não vai para disco, banco nem log. A foto é enviada à Anthropic para ser lida: precisa constar na política de privacidade e na auditoria do RNF05 (#43) |

## RF16 · Preenchimento manual quando o assistente falha (#22)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Explica o motivo em linguagem simples e pede só o que falta | ✅ | "gastei na farmácia" → "Não consegui entender o valor… Quanto foi esse gasto com Farmácia?". Gasto no futuro e vários valores também explicam o motivo. Com valor por extenso ("trinta"), o assistente pedia o valor e repetia "Ainda não consegui entender" (#135, 🔧 PR #145) |
| 2 | Nenhum lançamento perdido em silêncio | ✅ | Resposta que não serve → pergunta de novo; só desiste com "cancelar". Banco fora do ar → "ainda não anotei", e a pendência fica guardada |

## RF24 · Resumo proativo do assistente (#23)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Resumo semanal e/ou mensal automático (job agendado) | ⚠️ 🔧 | Agenda e texto ok (segunda 9h30 e dia 1º 10h). **Mas não chega a ninguém:** o adaptador `api` do WhatsApp era um `TODO` (#152, PR #154). Vale também para o RF28 |
| 2 | Conteúdo curto: gastou, resta, maiores categorias | ⚠️ 🔧 | O texto está certo, mas os gastos do WhatsApp ficavam sem categoria e não entravam em "onde mais gastou" (#138, PR #147) |
| 3 | Usuário pode desativar ("parar resumo") | ❌ 🔧 | Só com a frase exata. "Parar resumo por favor" não funcionava e "não quero mais receber resumo" abria uma **entrada** de dinheiro (#137, PR #146) |
| 4 | Regras de mensagens proativas do WhatsApp verificadas | ✅ | Registrado no PR #131: a Evolution API não exige template; o texto já está no formato de template, caso o envio passe para a API oficial |

## RF26 · Contas fixas mensais (#24)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Opção "Repete todo mês" | ✅ | Com a opção marcada, o formulário pede só dia e mês (#120) |
| 2 | Gera a conta do mês seguinte | ✅ | Conta de luz paga no dia 23/11 → a de 23/12 apareceu sozinha |
| 3 | Regra para 29/30/31 em mês curto, com teste | ❌ 🔧 | Fevereiro certo (31 → 28), mas depois **fica no 28 para sempre** (28/03, 28/04…). O teste só olhava fevereiro (#153, PR #155) |
| 4 | Base para o RF18 | ✅ | `lancar_gastos_fixos` lançou a conta de luz no dia do vencimento |

## RF28 · Aviso de contas a vencer, no app e no WhatsApp (#25)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Aviso no app **e** no WhatsApp | ❌ 🔧 | App: a conta do dia aparecia como "Vence em 23 de nov.", sem destaque (#139, PR #150). WhatsApp: o adaptador não enviava (#152, PR #154) |
| 2 | Job diário no fuso de Brasília | ✅ | `crontab(hour=9)` com `America/Sao_Paulo` |
| 3 | Não avisa conta paga | ✅ | `test_lembretes_whatsapp.py` |
| 4 | Teste do agendamento sem WhatsApp real | ✅ | Idem, mais o teste que confere se toda rotina do Beat aponta para uma tarefa registrada (ficou à prova da ordem dos testes no PR #155) |

## RF33 · Filtro de contas pagas e pendentes (#26)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Filtro com botões grandes: Todas / Pendentes / Pagas | ✅ | Quatro abas de 48 px: "A vencer" e "Em atraso" no lugar de "Pendentes" |
| 2 | Filtro escolhido visível com mais que só cor | ❌ 🔧 | Só o fundo mudava. Agora fica sublinhado e com a borda mais grossa (#141, PR #151) |
| 3 | Funciona na lista diária (RF32) | ✅ | Também no calendário: "Pagas" filtra a lista do dia |

## RF37 · Registro de parcelas (#27)

| # | Critério | Status | Issue / observação |
|---|---|---|---|
| 1 | Informar o número de parcelas ao registrar | ❌ 🔧 | **Só existia na API** (PR #92): não havia campo na tela (#134, PR #149) |
| 2 | Calcula o valor e divide pelos meses seguintes | ✅ | R$ 2.500 em 10 vezes → 10 × R$ 250 a partir do mês seguinte; o centavo que sobra vai na 1ª |
| 3 | Parcelas futuras nos meses correspondentes | ⚠️ 🔧 | Aparecem em Contas e no calendário de cada mês. No Extrato, entram como gasto no vencimento (RF18). Na lista, eram dez "Geladeira R$ 250,00" iguais, e o resumo "A vencer" somava até 2027 (#134) |

## Acessibilidade com a persona (RNF01)

| Verificação | Status | Issue / observação |
|---|---|---|
| axe WCAG 2.1 AA, sem violação grave, nas 7 telas | ✅ | Com dados reais. Com `best-practice`: `main` duplicado nas telas logadas (#143) e cadastro sem `h1` no celular (#111, reaberta) |
| Zoom de 200% e 360 px sem rolagem lateral | ✅ | E2E |
| Alvo de toque mínimo de 48 px (`--toque-minimo`) | ❌ 🔧 | Atalhos de nome com 28 px, lixeira de 30 px, caixa de seleção de 14 px… (#142, PR #151) |
| Internet lenta (3G, 2 s de latência) | ✅ | "Salvando…" aparece, e o toque duplo grava uma vez só (1 POST) |
| Sem conexão no meio do salvamento | ✅ | "Não foi possível salvar agora. Verifique a internet e tente de novo.", e o valor digitado continua na tela |
| Toque duplo em "Confirmar e salvar" no cadastro | ✅ | Uma conta só |
| Apagar conta | ❌ 🔧 | Dizia "apagada com sucesso", mas a API não apagava (#133, PR #148) |
| Conta nova, sem gasto nenhum | ❌ 🔧 | "Você já gastou 100% / todo o saldo" (#140, PR #150) |
| Linguagem: "PIN" | ➖ | Decisão do time em `docs/linguagem.md`. A persona não conhece a palavra; observar no teste com pessoa real |

## Assistente: frases do jeito da persona

| Frase | Antes | Depois (PRs abertos) |
|---|---|---|
| gastei 30 conto na farmasia | ✅ R$ 30,00 · Farmácia | igual, agora gravado na categoria Saúde (#138) |
| gastei 20,5 no onibus | ❌ não entendeu o valor | ✅ R$ 20,50 (#135) |
| gastei 2000 no conserto | ❌ não entendeu o valor | ✅ R$ 2.000,00 (#135) |
| gastei trinta reais no mercado | ⚠️ pediu o valor, e "trinta" não servia | ✅ R$ 30,00 (#135) |
| o neto me deu 50 | ❌ gasto | ✅ entrada (#136) |
| vendi um bolo por 30 | ❌ gasto "com Renda Extra" | ✅ entrada · Renda Extra (#136) |
| paguei 2 contas de luz 120 e 80 | ✅ pede um de cada vez | igual |
| [foto ilegível, legenda "remedio"] | ⚠️ "Quanto foi esse gasto com ?" | ✅ "Qual foi o valor?", e a categoria vem da legenda (#132) |
| ontem gastei 40 no mercado | ⚠️ anotado com a data de hoje | sem mudança: fica como observação para o RF12 |

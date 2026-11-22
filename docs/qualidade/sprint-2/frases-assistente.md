# Sprint 2: frases de teste do assistente (RF12)

Rodadas contra `processar_texto_mensagem` da branch `feature/whatsapp-texto` em 10/11. Resultado: **37 de 47 corretas**.
As frases "sem registro" deveriam ser recusadas ou gerar uma pergunta ao usuário.

Este conjunto cobre o critério "pelo menos 30 frases de teste no CI" (#73) e pode virar fixture de `pytest` direto.

## Frases que falharam

| Grupo | Frase | Esperado | Obtido | Gravidade |
|---|---|---|---|---|
| Decimal | gastei 1,250.00 no mercado | R$ 1.250,00 | **R$ 1,25** | Alta: valor errado sem aviso |
| Ambígua | dia 12 gastei 35 na farmácia | R$ 35,00 | **R$ 12,00** | Alta: pega a data como valor |
| Ambígua | comprei 2 pães por 10 reais | R$ 10,00, Alimentação | **R$ 2,00**, Outros | Alta: pega a quantidade como valor; "pães" não casa com "pao" |
| Ambígua | gastei 35 na farmácia e 20 na padaria | pedir para mandar um por vez | R$ 35,00 (o segundo some) | Média |
| Ambígua | recebi 50 do meu filho e gastei 30 no mercado | pedir para mandar um por vez | **gasto** de R$ 50,00 | Alta |
| Ambígua | recebi o pagamento de 800 | receita | **gasto** ("pagamento" está na lista de verbos de gasto) | Alta |
| Ambígua | recebi 100 do Claudeu | receita | **gasto** ("deu" casa dentro de "Claudeu") | Alta |
| Ambígua | vou gastar 100 amanhã | não registrar (futuro) | gasto de R$ 100,00 | Média |
| Ambígua | gastei -35 na farmácia | recusar ou perguntar | R$ 35,00 | Baixa |
| Decimal | gastei 35 reais e 50 centavos na farmácia | R$ 35,50 | R$ 35,00 | Média |
| Extenso | gastei trinta reais na farmácia | R$ 30,00 | não entendeu (pede para reenviar) | Baixa: falha segura |

## Frases que passaram

| Grupo | Frases |
|---|---|
| Base | gastei 35 na farmácia · recebi 1500 da aposentadoria · paguei 120 de luz · comprei pão 8 reais · uber 22 · caiu o salário 2300 |
| Vírgula e ponto | 35,50 · 35.50 · R$ 1.250,00 · 1.250 · 1250,5 · 0,99 · R$35 · 1.500,00 do inss · 10.000 |
| Erros de digitação | gstei · farmasia · farmacia · aposentadorria · supermecado · remedio · CAIXA ALTA · com emoji |
| Ambíguas | gastei 35 na farmácia dia 12 · o pix de 200 caiu · fiz um pix de 200 pro meu filho · conta de água 90 · quanto eu tenho? · oi · gastei na farmácia (sem valor) · gastei 0 · foi 45 a consulta · ganhei 300 de presente · deu 60 o gás · liguei pro banco, paguei 35 · dinheiro foi embora 40 no bar · gastei 50 conto no mercado |

## Respostas de confirmação (RF15)

| Resposta do usuário | Reconhecida como |
|---|---|
| Sim · N · Não | sim / não ✅ |
| sim! · Sim. · SIM 👍 · sim, pode anotar · 👍 · ok | **nada**: o registro é descartado e a resposta vira mensagem nova (#72) |
| não! · nao, foi 45 | **nada** (#72) |

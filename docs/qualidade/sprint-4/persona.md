# Persona de teste: Dona Lurdes

Pessoa **fictícia**, criada pela QA para o teste de acessibilidade da Sprint 4. Os dados abaixo não são de ninguém real:
o telefone e o e-mail são inventados e só existem no banco de QA (`vero_qa`).

> Ela **não substitui** o teste com uma pessoa idosa real pedido na #47: serve para a QA percorrer o app com os mesmos
> obstáculos que esse público enfrenta e chegar ao teste real com os defeitos óbvios já corrigidos.

## Quem é

| | |
|---|---|
| Nome | Lurdes Aparecida Souza ("Dona Lurdes") |
| Idade | 74 anos |
| Onde mora | Ceilândia (DF), sozinha; a filha mora em Goiânia |
| Renda | Aposentadoria do INSS (R$ 1.518,00) e uma costura de vez em quando |
| Escolaridade | Fundamental incompleto. Lê devagar; números ela entende bem, mas escreve "trinta" em vez de "30" às vezes |
| Celular | Android básico, tela pequena (360 px de largura), **fonte grande** ligada nas configurações e brilho baixo para economizar bateria |
| Internet | Pré-paga, 3G que cai na cozinha. A franquia acaba no fim do mês e aí só o WhatsApp funciona |
| Visão | Catarata no começo: letra pequena e cinza-claro somem |
| Mãos | Tremor leve: erra o toque em botão pequeno e às vezes toca duas vezes |

## Como ela usa o celular

- **WhatsApp é o que ela domina:** manda áudio, foto e mensagem curta, quase sempre sem acento e sem pontuação
  ("gastei 30 conto na farmasia", "paguei a luz deu 120").
- Não sabe o que é "PIN", "login", "token", "sessão" nem "categoria". Conhece "senha" e "tipo de gasto".
- Quando a tela demora, **toca de novo** no botão. Quando aparece mensagem em inglês ou com número de erro, acha que
  quebrou o celular e desiste.
- Não usa o botão "voltar" do navegador; fecha o app e abre de novo.
- Precisa de um tempo para ler: se a mensagem some sozinha em poucos segundos, ela não chega a ver.

## O que ela quer fazer no Vero (cenários do teste)

1. **Criar a conta** com a ajuda das instruções da tela, sem ninguém do lado.
2. **Anotar um gasto** da farmácia pelo app, com a fonte grande ligada e a internet lenta.
3. **Cadastrar a conta de luz** que vence todo dia 10 e se repete todo mês (RF26), e ver só o que falta pagar (RF33).
4. **Registrar a geladeira** comprada em 10 vezes (RF37).
5. **Anotar pelo WhatsApp** do jeito dela: texto sem acento, valor por extenso, foto do cupom (RF14) e corrigir quando
   o assistente não entende (RF16).
6. **Parar o resumo** semanal (RF24) porque "não quer mensagem toda semana".

## Dados da conta de teste (somente no banco de QA)

| Campo | Valor |
|---|---|
| Nome | Lurdes Aparecida Souza |
| Celular | (61) 99000-0174 (inventado) |
| E-mail | dona.lurdes@exemplo.com (domínio reservado para exemplos) |
| Senha (PIN) | 1952 (o ano em que ela nasceu, como ela escolheria) |

## Como a QA simula as dificuldades dela

| Dificuldade | Como foi simulada |
|---|---|
| Tela pequena e fonte grande | Viewport de 360 × 800 e texto do navegador em 150% e 200% |
| Baixa visão | Verificação de contraste (axe, WCAG 2.1 AA) e tamanho mínimo de letra |
| Tremor e toque duplo | Alvos de toque medidos (mín. 44 × 44 px) e duplo clique nos botões de salvar |
| Internet lenta ou caindo | Rede limitada a 3G lento (400 kb/s, 2 s de latência) e sem conexão no meio do salvamento |
| Pouca familiaridade digital | Busca por termos técnicos ou em inglês nas mensagens da tela; tempo para ler avisos |
| Escrita do dia a dia | Frases no WhatsApp sem acento, com gíria ("conto"), valor por extenso e erro de digitação |

# Guia de Linguagem e Identidade — O Vero

Este guia estabelece os princípios de simplicidade linguística, tom de voz e vocabulário do **Vero**, atendendo ao requisito não-funcional **RNF02** (Simplicidade Linguística).

---

## 1. Identidade e Tratamento

- O aplicativo é sempre tratado no gênero masculino: **"O Vero"**, **"no Vero"**, **"do Vero"**.
- O tom de voz deve ser **calmo, direto, acolhedor e transparente**.
- O público-alvo prioritário é composto por pessoas idosas e com baixo letramento digital/financeiro. As mensagens devem ser curtas e com palavras do cotidiano.

---

## 2. Princípios de Redação

1. **Evitar Termos em Inglês**:
   - ❌ *Login* $\rightarrow$ ✅ **Entrar**
   - ❌ *Logout* / *Sign out* $\rightarrow$ ✅ **Sair**
   - ❌ *Dashboard* $\rightarrow$ ✅ **Início** / **Seu dinheiro do mês**
   - ❌ *Settings* $\rightarrow$ ✅ **Configurações**

2. **Evitar Jargões Contábeis e Bancários**:
   - ❌ *Receitas / Créditos / Lançamentos positivos* $\rightarrow$ ✅ **Entrou dinheiro** / **Entradas do mês**
   - ❌ *Despesas / Débitos / Saídas* $\rightarrow$ ✅ **Gasto** / **Contas a pagar**
   - ❌ *Superávit / Disponibilidade líquida* $\rightarrow$ ✅ **Dinheiro livre** / **Saldo que sobra**
   - ❌ *Status de inadimplência* $\rightarrow$ ✅ **Conta em atraso**

3. **Autenticação e Acesso**:
   - O acesso é realizado por **PIN numérico curto** (4 dígitos).
   - ❌ *Senha* / *Password* $\rightarrow$ ✅ **PIN** / **PIN numérico** / **Seu PIN de 4 números**
   - ❌ *Recuperar senha* $\rightarrow$ ✅ **Recuperar meu PIN**
   - ❌ *Credenciais inválidas* $\rightarrow$ ✅ **Número de celular ou PIN incorreto**

4. **Instruções e Ações no Formulário**:
   - Botões devem expressar claramente o que vai acontecer:
     - ✅ **"Continuar"**
     - ✅ **"Confirmar e salvar"**
     - ✅ **"Marcar como paga"**
     - ✅ **"Sim, apagar"**
     - ✅ **"Cancelar"**

---

## 3. Mensagens e Feedbacks de Erro

- Mensagens de erro nunca devem culpar o usuário ou exibir termos técnicos (como *exception*, *HTTP 401*, *stacktrace*).
- Devem orientar o que fazer a seguir:
  - ❌ *"Falha na requisição ao endpoint de autenticação."*
  - ✅ *"Não foi possível entrar no Vero. Verifique seus dados e tente novamente."*
  - ❌ *"Campo numérico nulo."*
  - ✅ *"Digite um valor maior que zero para o gasto."*

---

## 4. Comunicação do Assistente no WhatsApp

- Mensagens curtas e com no máximo 2 frases por envio.
- Respostas diretas confirmando o valor e categoria com perguntas de confirmação simples (*"Você gastou R$ 30,00 no Mercado. Confirma?"*).

# Sprint 3: roteiro de teste no celular

Responsável: Beatriz (QA) · Data: __/__ · Commit testado: `_______`

A issue #46 pede validação **em celular real** (câmera e áudio) e o QR Code com notas fiscais de **pelo menos 2
estabelecimentos**. Este roteiro é para preencher durante o teste. Cada ❌ vira uma issue com o modelo de bug.

## Preparação

1. Migrations: a `dev` em `686ae96` **não sobe** (`0008_recorrencia_conta.py` com erro de sintaxe, #97).
   Testar depois da correção ou com ela aplicada localmente.
2. Subir o app: `scripts/rodar-local.sh`.
3. **HTTPS é obrigatório para a câmera.** Pelo IP da rede (`http://192.168.x.x:5173`) o navegador não libera
   `getUserMedia` e só sobra a opção de foto. Opções:
   - túnel HTTPS para a porta 5173 (ex.: `cloudflared tunnel --url http://localhost:5173`); pode ser preciso liberar o
     host em `server.allowedHosts` no `vite.config.ts`;
   - ou `@vitejs/plugin-basic-ssl` + `npm run dev -- --host` e aceitar o certificado no celular.
4. Criar uma conta nova no celular (o tour só abre sozinho no primeiro acesso daquele navegador). Para repetir o
   primeiro acesso: aba anônima ou apagar os dados do site.
5. Volume do celular alto e modo silencioso desligado (no iPhone, a chave lateral corta a Web Speech API).

## Aparelhos

| | Aparelho | Sistema | Navegador | Voz pt-BR usada |
|---|---|---|---|---|
| A | | Android | Chrome | |
| B | | iOS | Safari | |

Se não houver iPhone na equipe, registrar como pendente; o critério do RF21 pede os dois.

## Casos

| # | RF | Passo | Esperado | A | B |
|---|---|---|---|---|---|
| C1 | RF05 | Entrar pela primeira vez | Tour abre e **fala** o passo 1 sem precisar tocar de novo | | |
| C2 | RF05 | Deixar o tour correr sozinho | Avança até o passo 8 sem travar (atenção aos passos 2 e 4, que são longos) | | |
| C3 | RF05 | Pausar, Continuar, Repetir, Pular | Cada botão responde ao primeiro toque; anotar se "Continuar" recomeça o passo | | |
| C4 | RF05 | Recarregar a página logado, depois "Ouvir explicação" | Tour reabre e fala | | |
| C5 | RF07 | "Ler QR Code da nota fiscal" | Pede permissão e abre a câmera traseira | | |
| C6 | RF07 | Negar a permissão da câmera | Mensagem simples e opção de foto ou digitar | | |
| C7 | RF07 | Ler as notas da tabela abaixo | Valor, data e loja aparecem para conferir antes de salvar | | |
| C8 | RF07 | Confirmar e abrir o Extrato | Gasto com o valor, a data e a descrição certos; saldo do Início atualizado | | |
| C9 | RF21 | "Ouvir" no Início com saldo de R$ 1.250,00 | Fala "mil duzentos e cinquenta reais", sem "R cifrão" nem "um ponto duzentos" | | |
| C10 | RF21 | "Ouvir" no Extrato e em Contas | Mesma naturalidade; tocar de novo para a fala | | |
| C11 | RF20 | Anotar gasto, cadastrar conta, pagar conta, excluir gasto | Toda ação mostra confirmação com ícone, texto e cor, por ≥ 5 s | | |
| C12 | RF20 | Repetir C11 com TalkBack (A) / VoiceOver (B) ligado | A confirmação é lida em voz alta, incluindo o valor | | |

Preencher com ✅, ❌ ou ⚠️ e uma frase do que aconteceu.

## Notas fiscais

Usar notas de compras reais, de **pelo menos 2 estabelecimentos diferentes** (de preferência um mercado e uma
farmácia ou restaurante). Não fotografar nem anexar a nota no repositório: o QR traz o CNPJ da loja e a chave da compra.

| # | Estabelecimento (tipo) | UF | Valor na nota | Leu? | Valor preenchido | Data preenchida | Loja preenchida | Salvo certo? |
|---|---|---|---|---|---|---|---|---|
| N1 | | | | | | | | |
| N2 | | | | | | | | |
| N3 | | | | | | | | |

O esperado pela análise de código, para comparar: nota do DF com QR 2.0 online → lê, mas **valor e loja vazios** e
data no dia 01. Se a nota for de contingência (impressa sem internet), o valor e o dia vêm preenchidos.

## Resultado

- Casos: __ ✅ · __ ⚠️ · __ ❌
- Issues abertas:

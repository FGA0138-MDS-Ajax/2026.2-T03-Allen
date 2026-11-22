# Rodar o Vero em localhost

Um comando sobe a aplicação inteira na sua máquina: banco (Postgres), Valkey, API (FastAPI) e app (Vite).

```bash
scripts/rodar-local.sh
```

| Comando | O que faz |
|---|---|
| `scripts/rodar-local.sh` | Sobe tudo e abre o app. Ctrl+C fecha só o app; os containers seguem rodando |
| `scripts/rodar-local.sh logs` | Log da API (inclui o código do "esqueci meu PIN") |
| `scripts/rodar-local.sh parar` | Para os containers e mantém os dados |
| `scripts/rodar-local.sh limpar` | Para os containers e apaga o banco local |

Endereços:

- App: <http://localhost:5173>
- API (Swagger): <http://localhost:8000/docs>
- Banco: `localhost:5433`, usuário `vero`, senha `vero`, banco `vero`

## Pré-requisitos

- Docker com o daemon rodando (`sudo systemctl start docker` no Linux)
- Node 22 e npm
- `curl`

## O que o script faz

1. Confere se Docker e npm estão disponíveis.
2. Cria o `.env` a partir do `.env.example`, se ele ainda não existir.
3. Sobe Postgres e Valkey e espera o Postgres ficar saudável.
4. Aplica as migrations (`alembic upgrade head`), reconstruindo a imagem do backend se o `requirements.txt` mudou.
5. Sobe a API e espera ela responder em `/docs`.
6. Instala as dependências do front (só quando o `package-lock.json` mudou) e roda `npm run dev`.

## Por que existe um `scripts/docker-compose.local.yml`

O `docker-compose.yml` principal espera o banco do Supabase no `DATABASE_URL` do `.env` e não sobe Postgres. O arquivo
local complementa o principal:

- adiciona o serviço `postgres` (porta 5433 na máquina, para não brigar com outro Postgres na 5432), com volume
  `vero-pg-local` para os dados sobreviverem ao `parar`;
- sobrepõe as variáveis do backend (`DATABASE_URL`, `VALKEY_URL`, `ENVIO_EMAIL=falso`, `APP_ENV=development`), então o
  script funciona mesmo que o `.env` aponte para o Supabase.

O app usa o proxy do Vite (`/api` → `localhost:8000`), então não precisa configurar CORS nem `VITE_API_URL`.

## Testando um PR

```bash
gh pr checkout <número>
scripts/rodar-local.sh
```

Se a branch tiver migrations novas, o script já aplica. Para começar com banco vazio, rode `scripts/rodar-local.sh limpar`
antes.

## Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| `http proxy error ... ECONNRESET` no terminal do Vite | A API caiu ao iniciar | `scripts/rodar-local.sh logs` |
| `Can't load plugin: sqlalchemy.dialects:https` | `DATABASE_URL` com a URL do projeto Supabase (`https://...`) rodando sem o script | Use o script, ou ponha uma URL `postgresql://` no `.env` |
| `Multiple head revisions are present` | Duas migrations com o mesmo `revision` | Cada migration precisa de `revision` único e `down_revision` apontando para a anterior |
| Porta 5173, 8000 ou 5433 em uso | Outro processo ou container usando a porta | Pare o processo ou o container (`docker ps`) |
| 14 testes do front falham com `localStorage.clear is not a function` | Node 25 | Rode os testes no Node 22 |

## Histórico

Criado em 14/11/2026 durante a validação dos PRs #83 e #84, quando subir o ambiente à mão falhou por causa do
`DATABASE_URL` e da migration duplicada. Os testes do script estão em
[`testes/2026-11-14-script-rodar-local.md`](../testes/2026-11-14-script-rodar-local.md).

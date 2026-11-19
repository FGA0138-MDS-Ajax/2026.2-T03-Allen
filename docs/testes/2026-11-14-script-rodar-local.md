# Script para rodar o Vero em localhost

Data: 14/11/2026 · Responsável: Beatriz (QA) · Base: `dev` + `scripts/rodar-local.sh` e `scripts/docker-compose.local.yml`

## Ambiente

- Arch Linux, Docker 29.3.0, Node 25.8.0 (servidor do Vite), Python 3.12 no container do backend.
- Testes 1 a 7 com o `DATABASE_URL` do `.env` apontando para um Postgres local; teste 8 com o `.env` original, apontando
  para o Supabase.

## Contexto

Subir o ambiente à mão falhou de dois jeitos antes do script:

1. A API caía ao iniciar com `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:https`, porque
   o `DATABASE_URL` do `.env` tinha a URL do projeto Supabase (`https://...`) em vez de uma URL de Postgres. O Vite
   mostrava `http proxy error: /api/v1/auth/cadastro ... ECONNRESET`.
2. `alembic upgrade head` falhava com `Multiple head revisions are present`: `0006_recorrencia_conta.py` usava o
   `revision` `"0005"`, igual ao de `0005_tbl_usuario.py`.

## Testes

| # | Teste | Método | Resultado |
|---|---|---|---|
| 1 | `bash -n scripts/rodar-local.sh` (sintaxe) | Executado | ✅ |
| 2 | Rodar `scripts/rodar-local.sh` do zero | Executado | ✅ Postgres saudável, migrations aplicadas, API respondendo, Vite em `http://localhost:5173` |
| 3 | `GET http://localhost:5173/` | Executado | ✅ 200 |
| 4 | `GET http://localhost:8000/docs` | Executado | ✅ 200 |
| 5 | `POST /api/v1/auth/cadastro` pelo proxy do Vite (`localhost:5173`) com nome, telefone, e-mail e PIN | Executado | ✅ 201, devolve `id, nome, telefone, email, tem_pin` |
| 6 | Status dos serviços (`docker compose ... ps`) | Executado | ✅ `postgres` healthy, `backend` e `valkey` up |
| 7 | Migration renumerada para `0008` (`down_revision` `0007`): `alembic downgrade 0007 && alembic upgrade head && alembic heads` | Executado | ✅ uma única head, `0008` |
| 8 | Backend recriado com o `.env` original (`DATABASE_URL=https://...` do Supabase) | Executado | ✅ `/docs` 200, `alembic current` = `0008`, e `printenv DATABASE_URL` no container mostra `postgresql://vero:vero@postgres:5432/vero`: o `docker-compose.local.yml` sobrepõe o `.env` |

Não testado: opções `parar`, `limpar` e `logs` (comandos diretos do Docker Compose), primeira execução sem `.env`, e
macOS/Windows (o script é bash; no Windows, use WSL).

## Achados fora do escopo do script

### Migration de recorrência não altera o banco

- Método: Análise de código + Executado (consulta ao banco)
- Onde: `backend/migracoes/versions/0008_recorrencia_conta.py` (antes `0006_recorrencia_conta.py`)
- Evidência: o `upgrade()` só cria objetos `sa.Column(...)` sem `op.add_column`, e o `downgrade()` é `pass`. Depois de
  `upgrade head`, a `tblConta` tem só `idConta, idUsuario, descConta, vrSaldo, dtProximoVencimento, idCategoria,
  dhPagamento, dhCriacao`

### Marcar conta como paga deve quebrar

- Método: Executado (inspeção do modelo) + Análise de código
- Onde: `backend/app/modulos/contas/servico.py` (`if paga and conta.recorrente:`); `app/modulos/contas/modelos.py`
- Evidência: `hasattr(Conta, 'recorrente')` devolve `False` no container do backend. Ao marcar uma conta como paga, a
  leitura de `conta.recorrente` deve gerar `AttributeError` (erro 500). O endpoint não foi chamado

Os dois achados foram registrados na issue #87.

## Conclusão

Script aprovado para uso local. A renumeração da migration é necessária para o `upgrade head` funcionar na `dev` e vai
junto no mesmo PR; a migration de recorrência e o modelo `Conta` continuam pendentes na #87.

#!/usr/bin/env bash
# Sobe o Vero inteiro em localhost: Postgres, Valkey, API (FastAPI) e app (Vite).
#
# Uso:
#   scripts/rodar-local.sh          sobe tudo e abre o app em http://localhost:5173
#   scripts/rodar-local.sh parar    para os containers (mantém os dados)
#   scripts/rodar-local.sh limpar   para e apaga o banco local
#   scripts/rodar-local.sh logs     mostra o log da API (inclui o código do "esqueci meu PIN")
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

COMPOSE=(docker compose -f docker-compose.yml -f scripts/docker-compose.local.yml)

info() { printf '\033[1;35m[vero]\033[0m %s\n' "$*"; }
erro() { printf '\033[1;31m[vero]\033[0m %s\n' "$*" >&2; exit 1; }

case "${1:-}" in
  parar)  "${COMPOSE[@]}" stop; exit 0 ;;
  limpar) "${COMPOSE[@]}" down -v; exit 0 ;;
  logs)   "${COMPOSE[@]}" logs -f backend; exit 0 ;;
  "")     ;;
  *)      erro "Opção desconhecida: $1 (use parar, limpar ou logs)" ;;
esac

command -v docker >/dev/null || erro "Docker não encontrado."
docker info >/dev/null 2>&1 || erro "O Docker não está rodando (tente: sudo systemctl start docker)."
command -v npm >/dev/null || erro "npm não encontrado. Instale o Node 22."

if [ ! -f .env ]; then
  info "Criando .env a partir do .env.example"
  cp .env.example .env
fi

info "Subindo Postgres e Valkey"
"${COMPOSE[@]}" up -d --wait postgres valkey

info "Aplicando migrations"
"${COMPOSE[@]}" run --rm --build backend alembic upgrade head

info "Subindo a API"
"${COMPOSE[@]}" up -d backend
for _ in $(seq 1 60); do
  curl -s -o /dev/null http://localhost:8000/docs && break
  sleep 1
done
curl -s -o /dev/null http://localhost:8000/docs \
  || erro "A API não respondeu. Veja o log com: scripts/rodar-local.sh logs"

cd frontend
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules/.package-lock.json ]; then
  info "Instalando dependências do front"
  npm ci --no-audit --no-fund
fi

info "Tudo pronto:"
info "  App:  http://localhost:5173"
info "  API:  http://localhost:8000/docs"
info "  Banco: localhost:5433 (usuário vero, senha vero)"
info "Ctrl+C fecha o app; os containers seguem rodando (scripts/rodar-local.sh parar para desligar)."
exec npm run dev

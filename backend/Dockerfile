FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Correções de segurança do Debian (ex.: zlib1g, CVE-2026-85091)
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Usuário sem privilégios (Trivy DS-0002). UID 1000 bate com o dono da pasta
# montada em ./backend no docker compose da maioria das máquinas.
RUN useradd --create-home --uid 1000 vero

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY --chown=vero:vero . .

USER vero

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

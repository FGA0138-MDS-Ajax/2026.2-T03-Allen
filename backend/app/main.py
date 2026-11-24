from fastapi import FastAPI

from app.modulos.assistente.router import router as whatsapp_router
from app.modulos.contas.router import (
    categorias_router,
)
from app.modulos.contas.router import (
    router as contas_router,
)
from app.modulos.identidade.router import router as identidade_router
from app.modulos.investimentos.router import router as investimentos_router
from app.modulos.tempo_real.router import router as tempo_real_router
from app.modulos.transacoes.router import router as transacoes_router
from app.nucleo.config import settings
from app.nucleo.erros import registrar_tratadores

app = FastAPI(title=settings.APP_NAME)
registrar_tratadores(app)

# Rotas
app.include_router(identidade_router)
app.include_router(whatsapp_router)
app.include_router(contas_router)
app.include_router(transacoes_router)
app.include_router(tempo_real_router)
app.include_router(categorias_router)
app.include_router(investimentos_router)


@app.get("/")
def health_check():
    return {"status": "online", "app": settings.APP_NAME}

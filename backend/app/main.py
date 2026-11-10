from fastapi import FastAPI

from app.modulos.contas.router import router as contas_router
from app.modulos.identidade.router import router as identidade_router
from app.modulos.tempo_real.router import router as tempo_real_router
from app.nucleo.config import settings
from app.nucleo.erros import registrar_tratadores

app = FastAPI(title=settings.APP_NAME)
registrar_tratadores(app)

app.include_router(identidade_router)
app.include_router(contas_router)
app.include_router(tempo_real_router)


@app.get("/")
def health_check():
    return {"status": "online", "app": settings.APP_NAME}

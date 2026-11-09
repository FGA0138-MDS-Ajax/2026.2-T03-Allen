from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modulos.contas.modelos import Conta  # noqa: F401
from app.modulos.contas.router import router as contas_router
from app.modulos.identidade.modelos import Usuario  # noqa: F401
from app.modulos.identidade.router import router as identidade_router
from app.nucleo.banco import Base, engine
from app.nucleo.config import settings
from app.nucleo.erros import registrar_tratadores


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Garante que as tabelas necessárias existam no banco configurado
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
registrar_tratadores(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identidade_router)
app.include_router(contas_router)


@app.get("/")
def health_check():
    return {"status": "online", "app": settings.APP_NAME}

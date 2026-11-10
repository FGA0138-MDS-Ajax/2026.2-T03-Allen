import re
import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, StringConstraints

from app.modulos.identidade.mensagens import Message


def normalizar_telefone(valor: str) -> str:
    """Guarda o celular só com dígitos, com o código do país (ex.: 5561999998888)."""
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) in (10, 11):
        digitos = "55" + digitos
    if not (len(digitos) in (12, 13) and digitos.startswith("55")):
        raise ValueError(Message.TELEFONE_INVALIDO.message)
    return digitos


def validar_pin(valor: str) -> str:
    if not re.fullmatch(r"\d{4,6}", valor):
        raise ValueError(Message.PIN_INVALIDO.message)
    return valor


Telefone = Annotated[str, AfterValidator(normalizar_telefone)]
Pin = Annotated[str, AfterValidator(validar_pin)]
Nome = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]


class CadastroEntrada(BaseModel):
    nome: Nome
    telefone: Telefone
    email: EmailStr
    pin: Pin


class LoginPinEntrada(BaseModel):
    telefone: Telefone
    pin: str


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    telefone: str
    email: str
    tem_pin: bool


class TokenSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_em: int

"""Mede o RNF04 (resposta do assistente em até 5 s) na leitura de fotos (RF14).

Para cada amostra, chama o mesmo caminho do webhook (`processar_foto`) com uma foto
de verdade e mede o tempo até a resposta ficar pronta para ser enviada. O envio pela
Evolution API não entra na conta (é interceptado), e nada é gravado no banco: a
pessoa não confirma o lançamento.

Uso (na raiz do repositório, com o .env do backend):

    LEITOR_COMPROVANTE=claude AI_API_KEY=... \\
      PYTHONPATH=backend backend/.venv/bin/python scripts/medir-rnf04.py fotos/ -n 20

`fotos/` tem os JPG/PNG de comprovantes, notas e contas. Com menos fotos do que
amostras, as fotos se repetem em rodízio. Precisa de um usuário cadastrado com o
telefone passado em --telefone.
"""

import argparse
import asyncio
import base64
import statistics
import sys
import time
from pathlib import Path

LIMITE_SEGUNDOS = 5.0
TIPOS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pasta", type=Path, help="pasta com as fotos")
    parser.add_argument("-n", "--amostras", type=int, default=20)
    parser.add_argument("--telefone", default="5561990000174")
    args = parser.parse_args()

    import app.modulos.assistente.router as router
    from app.nucleo.config import settings

    fotos = sorted(f for f in args.pasta.iterdir() if f.suffix.lower() in TIPOS)
    if not fotos:
        print(f"Nenhuma foto JPG/PNG em {args.pasta}")
        return 2

    respostas: list[str] = []

    async def capturar(_destinatario: str, texto: str) -> None:
        respostas.append(texto)

    router.enviar_mensagem = capturar
    remetente = f"{args.telefone}@s.whatsapp.net"
    tempos: list[float] = []
    print(f"Leitor: {settings.LEITOR_COMPROVANTE} · modelo: {settings.AI_MODELO}")

    for i in range(args.amostras):
        foto = fotos[i % len(fotos)]
        dados = {
            "key": {"id": f"rnf04-{i}", "remoteJid": remetente},
            "message": {
                "imageMessage": {"mimetype": TIPOS[foto.suffix.lower()]},
                "base64": base64.b64encode(foto.read_bytes()).decode(),
            },
        }
        inicio = time.perf_counter()
        asyncio.run(router.processar_foto(remetente, dados))
        tempos.append(time.perf_counter() - inicio)
        lida = "pediu confirmação" if "Posso anotar" in respostas[-1] else "pediu dados"
        print(f"{i + 1:>3}. {foto.name:<30} {tempos[-1]:6.2f} s  ({lida})")
        # Descarta a pendência para a próxima amostra começar do zero
        asyncio.run(router.processar_responder(remetente, "cancelar"))

    acima = sum(t > LIMITE_SEGUNDOS for t in tempos)
    print(
        f"\nAmostras: {len(tempos)} · média {statistics.mean(tempos):.2f} s · "
        f"mediana {statistics.median(tempos):.2f} s · pior {max(tempos):.2f} s · "
        f"acima de {LIMITE_SEGUNDOS:.0f} s: {acima}"
    )
    return 0 if acima == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

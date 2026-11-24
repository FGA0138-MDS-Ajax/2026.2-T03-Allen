"""Script de medição de desempenho (RNF04: <= 5 s no p95) para áudios do RF13.

Uso:
    python scripts/medir_rnf04_audio.py [pasta_com_audios]
"""

import sys
import time
from pathlib import Path

from app.integracoes.transcricao import AdaptadorWhisper
from app.modulos.assistente.extrator import processar_texto_mensagem


def medir_pasta(pasta: Path) -> int:
    arquivos = sorted(
        p
        for p in pasta.iterdir()
        if p.suffix.lower() in {".ogg", ".mp3", ".wav", ".m4a"}
    )
    if not arquivos:
        print(f"Nenhum áudio encontrado em {pasta}")
        return 1

    adaptador = AdaptadorWhisper()
    print("Pré-carregando modelo Whisper (int8)...")
    adaptador.precarregar()

    tempos_ms: list[float] = []
    for arquivo in arquivos:
        audio_bytes = arquivo.read_bytes()
        inicio = time.perf_counter()
        try:
            texto = adaptador.transcrever(audio_bytes)
            intencao = processar_texto_mensagem(texto)
            status = "OK" if intencao.sucesso else "NAO_COMPREENDIDO"
        except Exception as erro:
            status = type(erro).__name__
        finally:
            del audio_bytes

        duracao_ms = (time.perf_counter() - inicio) * 1000
        tempos_ms.append(duracao_ms)
        print(f"  {arquivo.name}: {duracao_ms:.0f} ms ({status})")

    tempos_ms.sort()
    p95 = tempos_ms[int(0.95 * (len(tempos_ms) - 1))]
    print(f"\nAmostras: {len(tempos_ms)} | p95: {p95:.0f} ms (meta RNF04 <= 5000 ms)")
    return 0 if p95 <= 5000.0 else 2


if __name__ == "__main__":
    pasta_alvo = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "audios"
    )
    raise SystemExit(medir_pasta(pasta_alvo))

import React, { useEffect, useRef, useState } from 'react';
import { BrowserQRCodeReader } from '@zxing/library';
import { AlertaStatus } from '../AlertaStatus/AlertaStatus';
import { IconCamera, IconQrCode } from '../Icones/Icones';
import styles from './LeitorQrCode.module.css';

interface LeitorQrCodeProps {
  aoLerCodigo: (texto: string) => void;
  aoFechar: () => void;
}

export const LeitorQrCode: React.FC<LeitorQrCodeProps> = ({
  aoLerCodigo,
  aoFechar,
}) => {
  const modalRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const inputArquivoRef = useRef<HTMLInputElement | null>(null);
  const leitorRef = useRef<BrowserQRCodeReader | null>(null);
  const jaLidoRef = useRef(false);

  const [iniciando, setIniciando] = useState(true);
  const [erroCamera, setErroCamera] = useState<string | null>(null);
  const [erroFoto, setErroFoto] = useState<string | null>(null);
  const [lendoFoto, setLendoFoto] = useState(false);

  const encerrarCamera = () => {
    try {
      leitorRef.current?.reset();
    } catch {
      // ignora erro no reset
    }
    const videoEl = videoRef.current;
    if (videoEl && videoEl.srcObject) {
      const stream = videoEl.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoEl.srcObject = null;
    }
  };

  const fecharModal = () => {
    encerrarCamera();
    aoFechar();
  };

  // Acessibilidade do modal: Esc para fechar, foco inicial e focus trap
  useEffect(() => {
    const focoAnterior = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;

    const obterFocaveis = () => {
      if (!modal) return [];
      return Array.from(
        modal.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input:not(:disabled):not([type="file"]), [tabindex]:not([tabindex="-1"])'
        )
      );
    };

    const focaveisIniciais = obterFocaveis();
    if (focaveisIniciais.length > 0) {
      focaveisIniciais[0].focus();
    } else {
      modal?.focus();
    }

    const aoPressionarTecla = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        encerrarCamera();
        aoFechar();
        return;
      }

      if (e.key === 'Tab') {
        const focaveis = obterFocaveis();
        if (focaveis.length === 0) return;

        const primeiro = focaveis[0];
        const ultimo = focaveis[focaveis.length - 1];

        if (e.shiftKey) {
          if (
            document.activeElement === primeiro ||
            !modal?.contains(document.activeElement)
          ) {
            e.preventDefault();
            ultimo.focus();
          }
        } else if (
          document.activeElement === ultimo ||
          !modal?.contains(document.activeElement)
        ) {
          e.preventDefault();
          primeiro.focus();
        }
      }
    };

    document.addEventListener('keydown', aoPressionarTecla);
    return () => {
      document.removeEventListener('keydown', aoPressionarTecla);
      focoAnterior?.focus?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let ativo = true;
    const leitor = new BrowserQRCodeReader();
    leitorRef.current = leitor;

    const iniciar = async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (ativo) {
          setIniciando(false);
          setErroCamera(
            'Seu navegador não liberou a câmera ao vivo. Você pode tirar uma foto da nota abaixo ou digitar o valor.'
          );
        }
        return;
      }

      try {
        if (!videoRef.current) return;
        await leitor.decodeFromConstraints(
          { video: { facingMode: { ideal: 'environment' } } },
          videoRef.current,
          (resultado) => {
            if (!ativo || jaLidoRef.current) return;
            if (resultado) {
              jaLidoRef.current = true;
              encerrarCamera();
              aoLerCodigo(resultado.getText());
            }
          }
        );
        if (ativo) {
          setIniciando(false);
        }
      } catch (err) {
        if (!ativo) return;
        setIniciando(false);
        const nomeErro = err instanceof Error ? err.name : '';
        if (
          nomeErro === 'NotAllowedError' ||
          nomeErro === 'PermissionDeniedError'
        ) {
          setErroCamera(
            'A permissão da câmera foi negada. Libere o acesso no navegador, envie uma foto da nota ou digite manualmente.'
          );
        } else if (
          nomeErro === 'NotFoundError' ||
          nomeErro === 'DevicesNotFoundError'
        ) {
          setErroCamera(
            'Nenhuma câmera foi encontrada neste aparelho. Você pode enviar uma foto da nota ou digitar manualmente.'
          );
        } else {
          setErroCamera(
            'Não foi possível abrir a câmera agora. Tente enviar uma foto do QR Code ou digite o valor.'
          );
        }
      }
    };

    iniciar();

    return () => {
      ativo = false;
      encerrarCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const aoSelecionarFoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = e.target.files?.[0];
    if (!arquivo) return;

    setLendoFoto(true);
    setErroFoto(null);

    const urlObjeto = URL.createObjectURL(arquivo);
    try {
      const leitorFoto = new BrowserQRCodeReader();
      const resultado = await leitorFoto.decodeFromImageUrl(urlObjeto);
      if (resultado) {
        jaLidoRef.current = true;
        encerrarCamera();
        aoLerCodigo(resultado.getText());
      }
    } catch {
      setErroFoto(
        'Não conseguimos ler o QR Code nessa foto. Tente aproximar mais do código ou digite o valor manualmente.'
      );
    } finally {
      URL.revokeObjectURL(urlObjeto);
      setLendoFoto(false);
      e.target.value = '';
    }
  };

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-leitor-qr"
    >
      <div className={styles.modal} ref={modalRef} tabIndex={-1}>
        <div className={styles.cabecalho}>
          <h2 id="titulo-leitor-qr" className={styles.titulo}>
            Ler QR Code da nota fiscal
          </h2>
          <p className={styles.instrucao}>
            Aponte a câmera para o quadradinho do QR Code que fica na nota
            fiscal.
          </p>
        </div>

        {erroCamera && <AlertaStatus tipo="erro">{erroCamera}</AlertaStatus>}
        {erroFoto && <AlertaStatus tipo="erro">{erroFoto}</AlertaStatus>}

        {!erroCamera && (
          <div className={styles.areaCamera}>
            <video
              ref={videoRef}
              className={styles.video}
              muted
              playsInline
              aria-label="Visualização da câmera para leitura de QR Code"
            />
            <div className={styles.miraGuia} aria-hidden="true" />
            {(iniciando || lendoFoto) && (
              <div className={styles.statusCarregando}>
                <IconQrCode size={36} />
                <span>
                  {lendoFoto
                    ? 'Lendo o QR Code da foto...'
                    : 'Abrindo a câmera...'}
                </span>
              </div>
            )}
          </div>
        )}

        <div className={styles.acoesSecundarias}>
          <input
            ref={inputArquivoRef}
            type="file"
            accept="image/*"
            capture="environment"
            className={styles.inputOculto}
            onChange={aoSelecionarFoto}
            aria-label="Selecionar foto do QR Code da nota fiscal"
          />

          <button
            type="button"
            className={styles.btnFoto}
            onClick={() => inputArquivoRef.current?.click()}
            disabled={lendoFoto}
          >
            <IconCamera size={22} />
            <span>
              {lendoFoto ? 'Lendo imagem...' : 'Usar foto ou imagem da nota'}
            </span>
          </button>

          <button
            type="button"
            className={styles.btnDigitar}
            onClick={fecharModal}
          >
            Digitar o valor manualmente
          </button>
        </div>
      </div>
    </div>
  );
};

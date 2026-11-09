import { useState, useEffect, useRef } from 'react';
import {
  Botao,
  CampoTexto,
  TecladoNumerico,
  AlertaStatus,
  IconVero,
} from '../../components';
import { useNavegacao } from '../../router';
import { entrarComPin, ErroApi } from '../../servicos';
import { formatarCelular, validarCelular } from '../../utils/telefone';
import styles from '../Cadastro/Cadastro.module.css';

export const Entrar = () => {
  const { navegar } = useNavegacao();
  const [celular, setCelular] = useState('(61) 99999-8888');
  const [pin, setPin] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const campoCelularRef = useRef<HTMLInputElement>(null);

  const digitarPin = (digito: string) => {
    if (pin.length < 4 && !carregando) {
      setPin((anterior) => anterior + digito);
      if (erro) setErro(null);
    }
  };

  const apagarPin = () => {
    if (!carregando) {
      setPin((anterior) => anterior.slice(0, -1));
      if (erro) setErro(null);
    }
  };

  const entrar = async () => {
    if (!celular.trim() || !validarCelular(celular)) {
      setErro('Digite um número de celular válido com DDD.');
      return;
    }

    if (pin.length !== 4) {
      setErro('Digite os 4 números do seu PIN.');
      return;
    }

    setCarregando(true);
    setErro(null);

    try {
      await entrarComPin(celular, pin);
      navegar('/inicio');
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível entrar no Vero. Verifique os dados e tente novamente.');
      }
    } finally {
      setCarregando(false);
    }
  };

  // Suporte à digitação pelo teclado físico do computador
  useEffect(() => {
    const tratarTeclaPressionada = (evento: KeyboardEvent) => {
      // Se o usuário estiver focado no campo de celular, o input nativo cuida da digitação
      const elementoAtivo = document.activeElement;
      const estaNoInputCelular =
        elementoAtivo && elementoAtivo.tagName === 'INPUT' && elementoAtivo !== document.body;

      if (evento.key === 'Enter') {
        evento.preventDefault();
        if (pin.length === 4) {
          entrar();
        } else if (estaNoInputCelular && validarCelular(celular)) {
          // Desfoca do celular para permitir digitar o PIN
          (elementoAtivo as HTMLElement).blur();
        }
        return;
      }

      if (estaNoInputCelular) {
        return;
      }

      if (/^[0-9]$/.test(evento.key)) {
        evento.preventDefault();
        digitarPin(evento.key);
      } else if (evento.key === 'Backspace') {
        evento.preventDefault();
        apagarPin();
      }
    };

    window.addEventListener('keydown', tratarTeclaPressionada);
    return () => window.removeEventListener('keydown', tratarTeclaPressionada);
  }, [celular, pin, carregando]);

  return (
    <div className={styles.pageContainer}>
      <header className={styles.navbar}>
        <a
          href="/"
          className={styles.brandLogo}
          onClick={(e) => {
            e.preventDefault();
            navegar('/');
          }}
          aria-label="Vero - Início"
        >
          <IconVero size={34} />
          <span>Vero</span>
        </a>

        <Botao
          variant="secondary"
          onClick={() => navegar('/cadastro')}
        >
          Criar conta
        </Botao>
      </header>

      <div style={{ maxWidth: '520px', margin: '0 auto', width: '100%' }}>
        <section className={styles.card} aria-live="polite">
          <h1 className={styles.titulo}>Entrar no Vero</h1>
          <p className={styles.subtitulo}>
            Digite seu celular e seu PIN de <strong>4 números</strong> usando seu teclado físico ou o teclado na tela.
          </p>

          {erro && (
            <div style={{ marginBottom: 20 }}>
              <AlertaStatus tipo="erro">{erro}</AlertaStatus>
            </div>
          )}

          <div style={{ marginBottom: 24 }}>
            <CampoTexto
              ref={campoCelularRef}
              rotulo="Número de celular"
              placeholder="(61) 99999-8888"
              type="tel"
              inputMode="numeric"
              maxLength={15}
              value={celular}
              onChange={(e) => {
                setCelular(formatarCelular(e.target.value));
                if (erro) setErro(null);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && validarCelular(celular)) {
                  e.preventDefault();
                  campoCelularRef.current?.blur();
                }
              }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <span
              style={{
                display: 'block',
                fontSize: 16,
                fontWeight: 700,
                color: 'var(--ardosia)',
                marginBottom: 8,
              }}
            >
              Seu PIN de 4 números
            </span>

            <div
              className={styles.pinDisplay}
              tabIndex={0}
              role="textbox"
              aria-label={`PIN: ${pin.length} de 4 dígitos preenchidos. Digite os 4 números no teclado.`}
              onClick={() => {
                // Ao clicar no PIN, garante que o campo de celular perca o foco
                if (document.activeElement instanceof HTMLElement) {
                  document.activeElement.blur();
                }
              }}
            >
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className={`${styles.pinDigito} ${
                    pin.length > i ? styles.pinDigitoPreenchido : ''
                  }`}
                >
                  {pin.length > i ? '●' : ''}
                </div>
              ))}
            </div>
          </div>

          <TecladoNumerico
            onDigito={digitarPin}
            onApagar={apagarPin}
          />

          <div style={{ marginTop: 24 }}>
            <Botao
              variant="primary"
              fullWidth
              disabled={pin.length !== 4 || carregando}
              onClick={entrar}
            >
              {carregando ? 'Entrando no Vero...' : 'Entrar'}
            </Botao>
          </div>
        </section>
      </div>
    </div>
  );
};

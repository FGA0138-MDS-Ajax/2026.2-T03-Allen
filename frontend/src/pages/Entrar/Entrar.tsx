import { useState } from 'react';
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

  const handleDigitoPin = (d: string) => {
    if (pin.length < 4 && !carregando) {
      setPin((prev) => prev + d);
      if (erro) setErro(null);
    }
  };

  const handleApagarPin = () => {
    if (!carregando) {
      setPin((prev) => prev.slice(0, -1));
      if (erro) setErro(null);
    }
  };

  const handleLimparPin = () => {
    if (!carregando) {
      setPin('');
      if (erro) setErro(null);
    }
  };

  const realizarLogin = async () => {
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
        setErro('Não foi possível entrar. Verifique os dados e tente novamente.');
      }
    } finally {
      setCarregando(false);
    }
  };

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
            Digite seu celular e sua senha de <strong>4 números</strong> para conferir o saldo disponível e anotar gastos.
          </p>

          {erro && (
            <AlertaStatus tipo="erro" role="alert">
              {erro}
            </AlertaStatus>
          )}

          <div style={{ marginBottom: '18px' }}>
            <CampoTexto
              rotulo="Celular com DDD"
              placeholder="(61) 99999-8888"
              type="tel"
              inputMode="numeric"
              maxLength={15}
              value={celular}
              onChange={(e) => {
                setCelular(formatarCelular(e.target.value));
                if (erro) setErro(null);
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <span
              style={{
                display: 'block',
                fontSize: '16px',
                fontWeight: 700,
                color: 'var(--ardosia)',
                marginBottom: '8px',
              }}
            >
              Senha de 4 números (PIN)
            </span>

            <div
              className={styles.pinDisplay}
              aria-label={`PIN: ${pin.length} de 4 dígitos digitados`}
            >
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className={`${styles.pinDigito} ${
                    pin.length > i ? styles.pinDigitoPreenchido : ''
                  }`}
                >
                  {pin.length > i ? '•' : ''}
                </div>
              ))}
            </div>
          </div>

          <TecladoNumerico
            onDigito={handleDigitoPin}
            onApagar={handleApagarPin}
            onLimpar={handleLimparPin}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            <Botao
              variant="primary"
              fullWidth
              disabled={pin.length !== 4 || carregando}
              onClick={realizarLogin}
            >
              {carregando ? 'Entrando...' : 'Entrar'}
            </Botao>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <Botao
                variant="secondary"
                fullWidth
                onClick={() => navegar('/cadastro')}
              >
                Criar nova conta
              </Botao>
              <Botao
                variant="secondary"
                fullWidth
                onClick={() => setErro('Para redefinir o PIN, entre em contato com o suporte ou refaça o cadastro.')}
              >
                Esqueci meu PIN
              </Botao>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

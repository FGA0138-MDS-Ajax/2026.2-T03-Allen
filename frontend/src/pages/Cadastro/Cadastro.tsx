import { useState } from 'react';
import {
  Botao,
  CampoTexto,
  TecladoNumerico,
  AlertaStatus,
  IconVero,
  IconCheck,
  IconLock,
  IconWhatsApp,
} from '../../components';
import { useNavegacao } from '../../router';
import { cadastrarUsuario, ErroApi } from '../../servicos';
import { formatarCelular, validarCelular } from '../../utils/telefone';
import styles from './Cadastro.module.css';

export const Cadastro = () => {
  const { navegar } = useNavegacao();
  const [passo, setPasso] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [carregando, setCarregando] = useState(false);

  // Dados do formulário
  const [nome, setNome] = useState('');
  const [celular, setCelular] = useState('');
  const [codigo, setCodigo] = useState('');
  const [primeiroPin, setPrimeiroPin] = useState('');
  const [segundoPin, setSegundoPin] = useState('');
  const [erro, setErro] = useState<string | null>(null);

  const avancarParaCodigo = () => {
    if (!nome.trim()) {
      setErro('Por favor, informe seu nome.');
      return;
    }
    if (!celular.trim()) {
      setErro('Por favor, informe seu número de celular com DDD.');
      return;
    }
    if (!validarCelular(celular)) {
      setErro(
        'Digite um número de celular válido com DDD (exemplo: (61) 99999-8888).'
      );
      return;
    }
    setErro(null);
    setPasso(2);
  };

  const avancarParaPin = () => {
    if (!codigo.trim()) {
      setErro('Digite o código de verificação recebido.');
      return;
    }
    setErro(null);
    setPasso(3);
  };

  const digitarPin = (d: string) => {
    if (passo === 3) {
      if (primeiroPin.length < 4) {
        setPrimeiroPin((prev) => prev + d);
      }
    } else if (passo === 4) {
      if (segundoPin.length < 4) {
        setSegundoPin((prev) => prev + d);
      }
    }
  };

  const apagarPin = () => {
    if (passo === 3) {
      setPrimeiroPin((prev) => prev.slice(0, -1));
    } else if (passo === 4) {
      setSegundoPin((prev) => prev.slice(0, -1));
    }
  };

  const avancarConfirmacaoPin = () => {
    if (primeiroPin.length !== 4) {
      setErro('O PIN deve conter exatamente 4 números.');
      return;
    }
    setErro(null);
    setPasso(4);
  };

  const finalizarCadastro = async () => {
    if (segundoPin !== primeiroPin) {
      setErro('Os números digitados não conferem. Digite novamente.');
      setSegundoPin('');
      return;
    }

    setCarregando(true);
    setErro(null);

    try {
      await cadastrarUsuario({
        nome: nome.trim(),
        telefone: celular,
        pin: primeiroPin,
      });

      setPasso(5);
    } catch (e) {
      if (e instanceof ErroApi) {
        setErro(e.detalhe);
      } else {
        setErro('Não foi possível realizar o cadastro no Vero. Tente novamente.');
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
      </header>

      <div className={styles.layoutGrid}>
        {/* Painel Informativo de Desktop */}
        <aside className={styles.heroAside} aria-label="Apresentação do Vero">
          <span className={styles.heroBadge}>
            <IconCheck size={18} />
            <span>Seu dinheiro em dia, sem complicação</span>
          </span>

          <h1 className={styles.heroTitle}>
            Controlar o dinheiro não precisa ser coisa de especialista.
          </h1>

          <p className={styles.heroDescription}>
            O Vero ajuda você a saber quanto ainda tem disponível no mês e avisa
            antes de as contas vencerem, pelo celular ou pelo WhatsApp.
          </p>

          <div className={styles.heroPillars}>
            <div className={styles.pillarItem}>
              <div className={styles.pillarIcon} aria-hidden="true">
                <IconCheck size={26} />
              </div>
              <div className={styles.pillarText}>
                <strong>Letras e botões grandes</strong>
                <span>Tudo visível e confortável para ler sem esforço.</span>
              </div>
            </div>

            <div className={styles.pillarItem}>
              <div className={styles.pillarIcon} aria-hidden="true">
                <IconWhatsApp size={26} />
              </div>
              <div className={styles.pillarText}>
                <strong>Sem jargão contábil</strong>
                <span>
                  Linguagem simples: "Gasto", "Entrou dinheiro" e "Saldo".
                </span>
              </div>
            </div>

            <div className={styles.pillarItem}>
              <div className={styles.pillarIcon} aria-hidden="true">
                <IconLock size={26} />
              </div>
              <div className={styles.pillarText}>
                <strong>Seguro e com você no controle</strong>
                <span>Acesso rápido por PIN de 4 números.</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Card do Formulário */}
        <section className={styles.card} aria-live="polite">
          {erro && (
            <AlertaStatus tipo="erro" role="alert">
              {erro}
            </AlertaStatus>
          )}

          {passo === 1 && (
            <>
              <span className={styles.etapaIndicador}>Passo 1 de 3</span>
              <h2 className={styles.titulo}>Criar sua conta no Vero</h2>
              <p className={styles.subtitulo}>
                Digite seu nome ou apelido e o número do seu celular.
              </p>

              <CampoTexto
                rotulo="Seu nome completo"
                placeholder="Ex.: Maria da Silva"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
              />

              <CampoTexto
                rotulo="Número de celular com DDD"
                placeholder="(61) 99999-8888"
                ajuda="Enviaremos uma mensagem de confirmação para este número"
                type="tel"
                inputMode="numeric"
                maxLength={15}
                value={celular}
                onChange={(e) => {
                  setCelular(formatarCelular(e.target.value));
                  if (erro) setErro(null);
                }}
              />

              <div className={styles.botoesAcao}>
                <Botao variant="primary" fullWidth onClick={avancarParaCodigo}>
                  Continuar
                </Botao>
                <Botao
                  variant="secondary"
                  fullWidth
                  onClick={() => navegar('/entrar')}
                >
                  Já tenho conta no Vero
                </Botao>
              </div>
            </>
          )}

          {passo === 2 && (
            <>
              <span className={styles.etapaIndicador}>Passo 2 de 3</span>
              <h2 className={styles.titulo}>Código de confirmação</h2>
              <p className={styles.subtitulo}>
                Digite o código enviado para o número de celular informado.
              </p>

              <CampoTexto
                rotulo="Código de verificação"
                placeholder="000000"
                value={codigo}
                onChange={(e) => setCodigo(e.target.value)}
              />

              <div className={styles.botoesAcao}>
                <Botao variant="primary" fullWidth onClick={avancarParaPin}>
                  Confirmar
                </Botao>
                <Botao
                  variant="secondary"
                  fullWidth
                  onClick={() => setPasso(1)}
                >
                  Voltar e corrigir dados
                </Botao>
              </div>
            </>
          )}

          {passo === 3 && (
            <>
              <span className={styles.etapaIndicador}>Passo 3 de 3</span>
              <h2 className={styles.titulo}>Crie seu PIN numérico</h2>
              <p className={styles.subtitulo}>
                Escolha 4 números fáceis de lembrar para entrar no aplicativo.
              </p>

              <div
                className={styles.pinDisplay}
                aria-label={`PIN: ${primeiroPin.length} de 4 dígitos digitados`}
              >
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`${styles.pinDigito} ${
                      primeiroPin.length > i ? styles.pinDigitoPreenchido : ''
                    }`}
                  >
                    {primeiroPin.length > i ? '•' : ''}
                  </div>
                ))}
              </div>

              <TecladoNumerico
                onDigito={digitarPin}
                onApagar={apagarPin}
                capturarTeclado={true}
              />

              <div className={styles.botoesAcao}>
                <Botao
                  variant="primary"
                  fullWidth
                  disabled={primeiroPin.length !== 4}
                  onClick={avancarConfirmacaoPin}
                >
                  Continuar
                </Botao>
              </div>
            </>
          )}

          {passo === 4 && (
            <>
              <span className={styles.etapaIndicador}>Confirmação</span>
              <h2 className={styles.titulo}>Confirme seu PIN</h2>
              <p className={styles.subtitulo}>
                Digite novamente os 4 números para confirmar.
              </p>

              <div
                className={styles.pinDisplay}
                aria-label={`Confirmação de PIN: ${segundoPin.length} de 4 dígitos digitados`}
              >
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`${styles.pinDigito} ${
                      segundoPin.length > i ? styles.pinDigitoPreenchido : ''
                    }`}
                  >
                    {segundoPin.length > i ? '•' : ''}
                  </div>
                ))}
              </div>

              <TecladoNumerico
                onDigito={digitarPin}
                onApagar={apagarPin}
                capturarTeclado={true}
              />

              <div className={styles.botoesAcao}>
                <Botao
                  variant="primary"
                  fullWidth
                  disabled={segundoPin.length !== 4 || carregando}
                  onClick={finalizarCadastro}
                >
                  {carregando ? 'Salvando cadastro...' : 'Confirmar e salvar'}
                </Botao>
              </div>
            </>
          )}

          {passo === 5 && (
            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  backgroundColor: '#D1FAE5',
                  color: '#065F46',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                aria-hidden="true"
              >
                <IconCheck size={36} />
              </div>

              <h2 className={styles.titulo}>Cadastro concluído!</h2>
              <p className={styles.subtitulo}>
                Sua conta no Vero foi criada com sucesso. Agora você pode falar com o assistente pelo WhatsApp ou acessar o aplicativo.
              </p>

              <div className={styles.botoesAcao} style={{ width: '100%', marginTop: 8 }}>
                <a
                  href={`https://wa.me/${import.meta.env.VITE_WHATSAPP_NUMERO || '5561999998888'}?text=${encodeURIComponent(
                    'Olá! Acabei de criar minha conta no Vero.'
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ textDecoration: 'none' }}
                >
                  <Botao variant="primary" fullWidth>
                    <IconWhatsApp size={22} />
                    <span>Falar com o assistente no WhatsApp</span>
                  </Botao>
                </a>

                <Botao
                  variant="secondary"
                  fullWidth
                  onClick={() => navegar('/entrar')}
                >
                  Entrar no aplicativo
                </Botao>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

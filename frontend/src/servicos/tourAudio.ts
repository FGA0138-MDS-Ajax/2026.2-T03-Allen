/**
 * Tour guiado em áudio do primeiro acesso (US13).
 * Guarda no navegador se a pessoa já ouviu (ou pulou) a explicação.
 */

const CHAVE_TOUR_VISTO = 'vero_tour_audio_visto';

export interface PassoTour {
  titulo: string;
  /** Texto falado em voz alta e exibido como legenda. */
  texto: string;
}

export const PASSOS_TOUR: PassoTour[] = [
  {
    titulo: 'Boas-vindas ao Vero',
    texto:
      'Olá! Vou explicar como usar o Vero. Você pode pausar, repetir ou pular esta explicação a qualquer momento, usando os botões grandes aqui embaixo.',
  },
  {
    titulo: 'Seu saldo do mês',
    texto:
      'Na tela de Início, o número grande mostra quanto dinheiro você ainda tem disponível no mês. A barra colorida mostra quanto você já gastou: verde está tranquilo, amarelo pede atenção e vermelho avisa que o dinheiro está acabando.',
  },
  {
    titulo: 'Botão Ouvir',
    texto:
      'Ao lado do seu saldo fica o botão Ouvir. Toque nele para escutar o valor em voz alta, sem precisar ler.',
  },
  {
    titulo: 'Anotar gasto ou recebimento',
    texto:
      'Para anotar um gasto ou um dinheiro que entrou, toque em Anotar Gasto ou Recebimento, no topo da tela. Digite o valor no teclado grande, escolha a categoria pelo desenho e toque em Salvar. Se errar, você tem dez segundos para desfazer.',
  },
  {
    titulo: 'Extrato',
    texto:
      'No Extrato você vê tudo o que entrou e saiu neste mês, do mais novo para o mais antigo.',
  },
  {
    titulo: 'Contas a pagar',
    texto:
      'Em Contas a Pagar você cadastra contas como luz e água e marca quando já pagou. As contas atrasadas aparecem em vermelho.',
  },
  {
    titulo: 'Anotar pelo WhatsApp',
    texto:
      'Você também pode anotar pelo WhatsApp. É só mandar uma mensagem, como: gastei trinta reais no mercado.',
  },
  {
    titulo: 'Pronto!',
    texto:
      'Pronto! Para ouvir esta explicação de novo, toque no botão Ouvir explicação, no topo da tela.',
  },
];

export const tourJaVisto = (): boolean => {
  try {
    return localStorage.getItem(CHAVE_TOUR_VISTO) === 'true';
  } catch {
    // Sem acesso ao armazenamento: não insiste em abrir o tour a cada tela
    return true;
  }
};

export const marcarTourVisto = (): void => {
  try {
    localStorage.setItem(CHAVE_TOUR_VISTO, 'true');
  } catch {
    // Armazenamento indisponível (aba anônima, bloqueio): segue sem guardar
  }
};

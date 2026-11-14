import { createContext, useContext } from 'react';

interface TourAudioContextType {
  /** Reabre a explicação em áudio (botão "Ouvir explicação"). */
  abrirTour: () => void;
}

export const TourAudioContext = createContext<TourAudioContextType>({
  abrirTour: () => {},
});

export const useTourAudio = () => useContext(TourAudioContext);

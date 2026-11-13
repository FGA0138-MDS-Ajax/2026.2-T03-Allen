import React, { ReactNode, useCallback, useEffect, useState } from 'react';
import { TourAudio } from './TourAudio';
import { TourAudioContext } from './contextoTour';
import { useNavegacao } from '../../router';
import { estaAutenticado } from '../../servicos';
import { marcarTourVisto, tourJaVisto } from '../../servicos/tourAudio';

const ROTAS_PUBLICAS = [
  '/boas-vindas',
  '/bem-vindo',
  '/cadastro',
  '/login',
  '/entrar',
];

/**
 * Abre a explicação em áudio sozinha no primeiro acesso depois do login (US13)
 * e permite reabri-la pelo botão "Ouvir explicação".
 */
export const TourAudioProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { rota } = useNavegacao();
  const [aberto, setAberto] = useState(false);

  const areaLogada = !ROTAS_PUBLICAS.includes(rota) && estaAutenticado();

  useEffect(() => {
    if (areaLogada && !tourJaVisto()) setAberto(true);
  }, [areaLogada]);

  const abrirTour = useCallback(() => setAberto(true), []);

  const fechar = () => {
    marcarTourVisto();
    setAberto(false);
  };

  return (
    <TourAudioContext.Provider value={{ abrirTour }}>
      {children}
      <TourAudio aberto={aberto} onFechar={fechar} />
    </TourAudioContext.Provider>
  );
};

import React from 'react';
import styles from './SeletorCategoria.module.css';
import { Categoria, CATEGORIAS_PADRAO, TipoCategoriaId } from './tipos';
import {
  IconMarket,
  IconPharmacy,
  IconBills,
  IconTransport,
  IconHome,
  IconOther,
} from '../Icones/Icones';

export interface SeletorCategoriaProps {
  categorias?: Categoria[];
  categoriaSelecionada?: string;
  onSelecionar: (id: string) => void;
  desabilitado?: boolean;
}

const MAPA_ICONES: Record<TipoCategoriaId, React.ReactNode> = {
  mercado: <IconMarket size={30} />,
  farmacia: <IconPharmacy size={30} />,
  contas: <IconBills size={30} />,
  transporte: <IconTransport size={30} />,
  casa: <IconHome size={30} />,
  outros: <IconOther size={30} />,
};

export const SeletorCategoria: React.FC<SeletorCategoriaProps> = ({
  categorias = CATEGORIAS_PADRAO,
  categoriaSelecionada,
  onSelecionar,
  desabilitado = false,
}) => {
  return (
    <div
      role="radiogroup"
      aria-label="Selecione a categoria do gasto"
      className={styles.grid}
    >
      {categorias.map((cat) => {
        const selecionado = categoriaSelecionada === cat.id;
        const iconeSvg = MAPA_ICONES[cat.id] || <IconOther size={30} />;

        return (
          <button
            key={cat.id}
            type="button"
            role="radio"
            aria-checked={selecionado}
            disabled={desabilitado}
            onClick={() => onSelecionar(cat.id)}
            className={`${styles.item} ${selecionado ? styles.itemSelecionado : ''}`}
          >
            <span className={styles.icone} aria-hidden="true">
              {iconeSvg}
            </span>
            <span className={styles.nome}>{cat.nome}</span>
          </button>
        );
      })}
    </div>
  );
};

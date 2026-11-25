/**
 * Lista única de categorias, servida pelo back-end (RF09, critério 4).
 * O `codigo` escolhe o ícone; o `id` vai junto do gasto para a API.
 */

import { requisicao } from './api';

export interface CategoriaApi {
  id: number;
  codigo: string;
  nome: string;
}

let emCache: Promise<CategoriaApi[]> | null = null;

/** Busca uma vez por sessão: a lista quase nunca muda. */
export const listarCategorias = (): Promise<CategoriaApi[]> => {
  if (!emCache) {
    emCache = requisicao<CategoriaApi[]>('/api/v1/categorias').catch((erro) => {
      emCache = null; // tenta de novo na próxima vez
      throw erro;
    });
  }
  return emCache;
};

/** Só para os testes. */
export const limparCacheCategorias = (): void => {
  emCache = null;
};

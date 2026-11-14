export type TipoCategoriaId =
  'mercado' | 'farmacia' | 'contas' | 'transporte' | 'casa' | 'outros';

export interface Categoria {
  id: TipoCategoriaId;
  nome: string;
}

export const CATEGORIAS_PADRAO: Categoria[] = [
  { id: 'mercado', nome: 'Mercado' },
  { id: 'farmacia', nome: 'Farmácia' },
  { id: 'contas', nome: 'Contas' },
  { id: 'transporte', nome: 'Transporte' },
  { id: 'casa', nome: 'Casa' },
  { id: 'outros', nome: 'Outros' },
];

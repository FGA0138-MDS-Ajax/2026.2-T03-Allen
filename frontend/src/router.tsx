import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';

interface RouterContextType {
  rota: string;
  navegar: (caminho: string) => void;
}

const RouterContext = createContext<RouterContextType>({
  rota: '/',
  navegar: () => {},
});

export function RouterProvider({ children }: { children: ReactNode }) {
  const [rota, setRota] = useState<string>(
    () => window.location.pathname || '/'
  );

  useEffect(() => {
    const handlePopState = () => {
      setRota(window.location.pathname || '/');
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navegar = (caminho: string) => {
    if (window.location.pathname !== caminho) {
      window.history.pushState({}, '', caminho);
      setRota(caminho);
      window.scrollTo(0, 0);
    }
  };

  return (
    <RouterContext.Provider value={{ rota, navegar }}>
      {children}
    </RouterContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useNavegacao = () => useContext(RouterContext);

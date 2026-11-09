import { RouterProvider, useNavegacao } from './router';
import { BoasVindas } from './pages/BoasVindas/BoasVindas';
import { Cadastro } from './pages/Cadastro/Cadastro';
import { Entrar } from './pages/Entrar/Entrar';
import { Contas } from './pages/Contas/Contas';
import { Inicio } from './pages/Inicio/Inicio';
import { AnotarGasto } from './pages/AnotarGasto/AnotarGasto';
import { Extrato } from './pages/Extrato/Extrato';
import { estaAutenticado } from './servicos';

function ConteudoRotas() {
  const { rota } = useNavegacao();

  switch (rota) {
    case '/boas-vindas':
    case '/bem-vindo':
      return <BoasVindas />;
    case '/cadastro':
      return <Cadastro />;
    case '/login':
    case '/entrar':
      return <Entrar />;
    case '/inicio':
    case '/dashboard':
      return estaAutenticado() ? <Inicio /> : <BoasVindas />;
    case '/extrato':
    case '/movimentacoes':
      return estaAutenticado() ? <Extrato /> : <BoasVindas />;
    case '/anotar-gasto':
    case '/novo-gasto':
      return estaAutenticado() ? <AnotarGasto /> : <BoasVindas />;
    case '/contas':
    case '/':
    default:
      return estaAutenticado() ? <Contas /> : <BoasVindas />;
  }
}

export default function App() {
  return (
    <RouterProvider>
      <main>
        <ConteudoRotas />
      </main>
    </RouterProvider>
  );
}

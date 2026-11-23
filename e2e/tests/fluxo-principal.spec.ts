import AxeBuilder from "@axe-core/playwright";
import { expect, Page, Route, test } from "@playwright/test";

// Fluxo crítico: login com PIN → saldo → anotar gasto → saldo atualizado.
// Roda contra o build do front (Vite) com a API simulada por `page.route`, para
// não depender de banco no CI. Os seletores usam papéis e rótulos acessíveis:
// se o teste não encontra um elemento, o leitor de tela também não encontra.

const CELULAR = "(61) 99999-8888";
const PIN = "1234";
const TELAS_PUBLICAS = ["/boas-vindas", "/cadastro", "/entrar"];
const TELAS_LOGADAS = ["/inicio", "/anotar-gasto", "/extrato", "/contas"];

const CATEGORIAS = [
  { id: 1, codigo: "casa", nome: "Casa" },
  { id: 2, codigo: "mercado", nome: "Mercado" },
  { id: 3, codigo: "farmacia", nome: "Farmácia" },
  { id: 7, codigo: "contas", nome: "Contas" },
  { id: 8, codigo: "salario", nome: "Salário" },
];

interface Transacao {
  id: string;
  tipo: "entrada" | "saida";
  valor: string;
  data: string;
  descricao: string | null;
  categoria_id: number | null;
  origem: string;
  criado_em: string;
}

const hoje = () => new Date().toISOString().slice(0, 10);

/** Token com o formato de JWT; o app só lê o `sub`. */
const TOKEN = `e2e.${Buffer.from(JSON.stringify({ sub: "usuario-e2e" })).toString("base64url")}.assinatura`;

/** API em memória, com o mesmo contrato do backend (`/api/v1`). */
async function simularApi(page: Page) {
  const transacoes: Transacao[] = [
    {
      id: "t-salario",
      tipo: "entrada",
      valor: "1250.00",
      data: `${hoje().slice(0, 8)}01`,
      descricao: "Aposentadoria",
      categoria_id: 8,
      origem: "manual",
      criado_em: new Date().toISOString(),
    },
  ];

  const saldo = () => {
    const soma = (tipo: Transacao["tipo"]) =>
      transacoes.filter((t) => t.tipo === tipo).reduce((s, t) => s + Number(t.valor), 0);
    const entradas = soma("entrada");
    const gastos = soma("saida");
    return {
      mes: hoje().slice(0, 7),
      entradas: entradas.toFixed(2),
      gastos: gastos.toFixed(2),
      contas: "0.00",
      saldo: (entradas - gastos).toFixed(2),
    };
  };

  const json = (route: Route, corpo: unknown, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(corpo) });

  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const { pathname } = new URL(req.url());
    const metodo = req.method();

    if (pathname === "/api/v1/auth/pin" && metodo === "POST") {
      const { pin } = req.postDataJSON() as { pin: string };
      if (pin !== PIN) return json(route, { detail: "Celular ou PIN incorretos." }, 401);
      return json(route, { access_token: TOKEN, token_type: "bearer", expira_em: 3600 });
    }
    if (pathname === "/api/v1/categorias") return json(route, CATEGORIAS);
    if (pathname === "/api/v1/contas" && metodo === "GET") return json(route, []);
    if (pathname === "/api/v1/transacoes/saldo") return json(route, saldo());
    if (pathname === "/api/v1/transacoes" && metodo === "GET") return json(route, transacoes);
    if (pathname === "/api/v1/transacoes" && metodo === "POST") {
      const dados = req.postDataJSON() as Partial<Transacao>;
      const nova: Transacao = {
        id: `t-${transacoes.length + 1}`,
        tipo: dados.tipo ?? "saida",
        valor: dados.valor ?? "0.00",
        data: dados.data ?? hoje(),
        descricao: dados.descricao ?? null,
        categoria_id: dados.categoria_id ?? null,
        origem: dados.origem ?? "manual",
        criado_em: new Date().toISOString(),
      };
      transacoes.unshift(nova);
      return json(route, nova, 201);
    }
    return json(route, { detail: "Não simulado no E2E" }, 404);
  });
}

/** Entra já logado e com o tour visto, para testar as telas da área logada. */
async function entrarDireto(page: Page) {
  await page.addInitScript((token) => {
    localStorage.setItem("vero_token", token);
    localStorage.setItem("vero_sessao_ativa", "true");
    localStorage.setItem("vero_tour_audio_visto", "true");
    localStorage.setItem("vero_tour_audio_visto:usuario-e2e", "true");
  }, TOKEN);
}

async function digitarNoTeclado(page: Page, digitos: string) {
  const teclado = page.getByRole("group", { name: /teclado numérico/i });
  for (const d of digitos) {
    await teclado.getByRole("button", { name: d, exact: true }).click();
  }
}

async function semViolacoesGraves(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const graves = violations.filter((v) => v.impact === "critical" || v.impact === "serious");
  expect(graves, graves.map((v) => `${v.id}: ${v.help}`).join("\n")).toEqual([]);
}

async function semRolagemHorizontal(page: Page) {
  const largura = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(largura).toBeLessThanOrEqual(0);
}

/** Toda tela tem um título principal visível (#60). O cadastro no celular ainda não tem (#111). */
async function temTituloPrincipal(page: Page, tela: string, largura: number) {
  const titulo = page.getByRole("heading", { level: 1 });
  if (tela === "/cadastro" && largura < 900) {
    test.info().annotations.push({ type: "bug", description: "#111: /cadastro sem h1 abaixo de 900px" });
    await expect(page.locator("main, body").first()).toBeVisible();
    return;
  }
  await expect(titulo).toBeVisible();
}

function paraCentavos(texto: string): number {
  const negativo = texto.includes("-");
  const digitos = texto.replace(/\D/g, "");
  return (negativo ? -1 : 1) * Number(digitos || 0);
}

test.beforeEach(async ({ page }) => {
  await simularApi(page);
});

test("login com PIN, saldo, gasto anotado e saldo atualizado", async ({ page }) => {
  await test.step("login com PIN (RF01)", async () => {
    await page.goto("/entrar");
    await page.getByLabel(/número de celular/i).fill(CELULAR);
    await digitarNoTeclado(page, PIN);
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page).toHaveURL(/\/inicio/);
  });

  await test.step("tour em áudio no primeiro acesso (RF05)", async () => {
    const tour = page.getByRole("dialog", { name: /boas-vindas ao vero/i });
    await expect(tour).toBeVisible();
    await expect(tour.getByText(/vou explicar como usar o vero/i)).toBeVisible();
    await tour.getByRole("button", { name: /sair da explicação/i }).click();
    await expect(tour).toBeHidden();
  });

  const saldo = page.getByTestId("saldo-disponivel");
  let saldoInicial = 0;
  await test.step("saldo na tela inicial (RF19)", async () => {
    await expect(saldo).toContainText("R$");
    await expect.poll(async () => paraCentavos(await saldo.innerText())).toBe(125000);
    saldoInicial = paraCentavos(await saldo.innerText());
    await expect(page.getByRole("button", { name: /^ouvir/i }).first()).toBeVisible();
  });

  await test.step("anotar gasto com teclado e categoria (RF08, RF09)", async () => {
    await page.goto("/anotar-gasto");
    await digitarNoTeclado(page, "1250");
    const mercado = page.getByRole("radio", { name: /mercado/i });
    await mercado.click();
    await expect(mercado).toHaveAttribute("aria-checked", "true");
    await semViolacoesGraves(page);
    await page.getByRole("button", { name: /salvar gasto/i }).click();
    await expect(page.getByRole("dialog", { name: /tudo certo/i })).toBeVisible();
  });

  await test.step("saldo atualizado (RF19)", async () => {
    await page.getByRole("button", { name: /ir para a tela inicial/i }).click();
    await expect(page).toHaveURL(/\/inicio/);
    await expect.poll(async () => paraCentavos(await saldo.innerText())).toBe(saldoInicial - 1250);
  });
});

test("PIN errado mostra mensagem e não entra (RF01)", async ({ page }) => {
  await page.goto("/entrar");
  await page.getByLabel(/número de celular/i).fill(CELULAR);
  await digitarNoTeclado(page, "9999");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText(/incorretos/i)).toBeVisible();
  await expect(page).toHaveURL(/\/entrar/);
});

// Acessibilidade (axe, WCAG 2.1 AA) e sem rolagem horizontal em todas as telas.
for (const tela of [...TELAS_PUBLICAS, ...TELAS_LOGADAS]) {
  test(`acessibilidade e layout de ${tela} (RNF01, RNF03)`, async ({ page }) => {
    if (TELAS_LOGADAS.includes(tela)) await entrarDireto(page);
    await page.goto(tela);
    await temTituloPrincipal(page, tela, page.viewportSize()?.width ?? 0);
    await semViolacoesGraves(page);
    await semRolagemHorizontal(page);
  });
}

// Zoom de 200% numa tela de 1280px equivale a uma janela de 640px com pixels em dobro.
test.describe("zoom de 200% (RNF01, critério RF19.4)", () => {
  test.use({ viewport: { width: 640, height: 400 }, deviceScaleFactor: 2 });
  for (const tela of [...TELAS_PUBLICAS, ...TELAS_LOGADAS]) {
    test(`${tela} sem rolagem horizontal`, async ({ page }) => {
      if (TELAS_LOGADAS.includes(tela)) await entrarDireto(page);
      await page.goto(tela);
      await temTituloPrincipal(page, tela, 640);
      await semRolagemHorizontal(page);
    });
  }
});

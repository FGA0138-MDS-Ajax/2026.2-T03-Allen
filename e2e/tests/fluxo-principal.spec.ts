import AxeBuilder from "@axe-core/playwright";
import { expect, Page, test } from "@playwright/test";

// Fluxo crítico da S1: cadastro → login com PIN → registrar gasto → ver saldo.
// Os seletores usam papéis e rótulos acessíveis: se o teste não encontra um
// elemento, o leitor de tela também não encontra.

const PIN = "1234";
// O código de verificação em staging vem de um provedor simulado (nunca SMS real).
const CODIGO_VERIFICACAO = process.env.E2E_CODIGO_VERIFICACAO ?? "000000";

const TELAS = ["/cadastro", "/codigo-sms", "/criar-pin", "/login", "/inicio", "/anotar-gasto"];

function celularFicticio(): string {
  const sufixo = String(Date.now()).slice(-8);
  return `(61) 9${sufixo.slice(0, 4)}-${sufixo.slice(4)}`;
}

async function digitarNoTeclado(page: Page, digitos: string) {
  const teclado = page.getByRole("group", { name: "Teclado numérico" });
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

function paraCentavos(texto: string): number {
  const negativo = texto.includes("-");
  const digitos = texto.replace(/\D/g, "");
  return (negativo ? -1 : 1) * Number(digitos || 0);
}

test("cadastro, login com PIN, registro de gasto e saldo atualizado", async ({ page }) => {
  const celular = celularFicticio();

  await test.step("cadastro por celular (RF03)", async () => {
    await page.goto("/cadastro");
    await semViolacoesGraves(page);
    await semRolagemHorizontal(page);

    await page.getByLabel(/nome/i).fill("Maria Teste");
    await page.getByLabel(/celular/i).fill(celular);
    await expect(page.getByLabel(/e-?mail/i)).toHaveCount(0);
    await page.getByRole("link", { name: "Continuar", exact: true }).click();
  });

  await test.step("código de confirmação (RF03)", async () => {
    await expect(page).toHaveURL(/\/codigo-sms/);
    await page.getByLabel(/código/i).fill(CODIGO_VERIFICACAO);
    await page.getByRole("link", { name: /confirmar código/i }).click();
  });

  await test.step("criação do PIN (RF01)", async () => {
    await expect(page).toHaveURL(/\/criar-pin/);
    await semViolacoesGraves(page);
    await digitarNoTeclado(page, PIN);
    await page.getByRole("button", { name: /confirmar e salvar pin/i }).click();
    await expect(page.getByRole("dialog", { name: /tudo certo/i })).toBeVisible();
  });

  await test.step("login com PIN (RF01)", async () => {
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/celular/i).fill(celular);
    await semViolacoesGraves(page);
    await digitarNoTeclado(page, PIN);
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page).toHaveURL(/\/inicio/);
  });

  const saldo = page.getByTestId("saldo-disponivel");
  let saldoInicial = 0;

  await test.step("saldo na tela inicial (RF19)", async () => {
    await expect(page.getByText(/disponível no mês/i)).toBeVisible();
    await expect(saldo).toContainText("R$");
    saldoInicial = paraCentavos(await saldo.innerText());
    await semViolacoesGraves(page);
    await semRolagemHorizontal(page);
  });

  await test.step("registrar gasto com teclado e categoria (RF08, RF09)", async () => {
    await page.getByRole("link", { name: /anotar gasto/i }).click();
    await expect(page).toHaveURL(/\/anotar-gasto/);

    await digitarNoTeclado(page, "1250");
    await expect(page.getByTestId("valor-digitado")).toHaveText("R$ 12,50");

    const mercado = page.getByRole("button", { name: /mercado/i });
    await mercado.click();
    await expect(mercado).toHaveAttribute("aria-pressed", "true");
    await semViolacoesGraves(page);

    await page.getByRole("button", { name: "Salvar", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Gasto de R$ 12,50 anotado." })).toBeAttached();
    await expect(page.getByRole("dialog", { name: /tudo certo/i })).toBeVisible();
  });

  await test.step("saldo atualizado após o gasto (RF19)", async () => {
    await page.getByRole("link", { name: /ir para a tela inicial/i }).click();
    await expect(page).toHaveURL(/\/inicio/);
    await expect.poll(async () => paraCentavos(await saldo.innerText())).toBe(saldoInicial - 1250);
  });
});

test("valor zero não pode ser salvo (RF08)", async ({ page }) => {
  await page.goto("/anotar-gasto");
  await page.getByRole("button", { name: /mercado/i }).click();
  await expect(page.getByRole("button", { name: "Salvar", exact: true })).toBeDisabled();
  await expect(page.getByText(/digite um valor maior que zero/i)).toBeVisible();
});

test("PIN incompleto mostra mensagem e não entra (RF01)", async ({ page }) => {
  await page.goto("/login");
  await digitarNoTeclado(page, "12");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: /digite os 4 números do pin/i })).toBeVisible();
  await expect(page).toHaveURL(/\/login/);
});

// Acessibilidade de todas as telas: axe (WCAG 2.1 AA) e sem rolagem horizontal.
for (const tela of TELAS) {
  test(`acessibilidade e layout de ${tela} (RNF01, RNF03)`, async ({ page }) => {
    await page.goto(tela);
    await semViolacoesGraves(page);
    await semRolagemHorizontal(page);
  });
}

// Zoom de 200% numa tela de 1280px equivale a uma janela de 640px com pixels em dobro.
test.describe("zoom de 200% (RNF01, critério RF19.4)", () => {
  test.use({ viewport: { width: 640, height: 400 }, deviceScaleFactor: 2 });

  for (const tela of TELAS) {
    test(`${tela} sem rolagem horizontal`, async ({ page }) => {
      await page.goto(tela);
      await semRolagemHorizontal(page);
    });
  }
});

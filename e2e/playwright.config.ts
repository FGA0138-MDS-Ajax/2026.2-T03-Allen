import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:4173",
    locale: "pt-BR",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "celular-360",
      use: { ...devices["Pixel 5"], viewport: { width: 360, height: 800 } },
    },
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_WHATSAPP_NUMERO?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

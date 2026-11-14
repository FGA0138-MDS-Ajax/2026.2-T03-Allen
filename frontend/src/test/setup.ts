import '@testing-library/jest-dom';

// Mock de ResizeObserver para o ambiente jsdom nos testes
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

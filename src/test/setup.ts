import '@testing-library/jest-dom';
import { vi } from 'vitest';

// ── Mock Tauri core (invoke) ──────────────────────────────────────────────────
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockResolvedValue(null),
}));

// ── Mock Tauri app API ────────────────────────────────────────────────────────
vi.mock('@tauri-apps/api/app', () => ({
  getVersion: vi.fn().mockResolvedValue('2.0.0'),
}));

// ── Mock Tauri dialog plugin ──────────────────────────────────────────────────
vi.mock('@tauri-apps/plugin-dialog', () => ({
  save: vi.fn().mockResolvedValue('/mock/path/backup.db'),
  open: vi.fn().mockResolvedValue(null),
}));

// ── Mock Tauri shell plugin ───────────────────────────────────────────────────
vi.mock('@tauri-apps/plugin-shell', () => ({
  open: vi.fn().mockResolvedValue(undefined),
}));

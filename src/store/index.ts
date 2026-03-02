import { create } from 'zustand';
import type { Toast } from '../types';

let toastCounter = 0;

interface AppStore {
  // Low stock badge
  lowStockCount: number;
  setLowStockCount: (n: number) => void;

  // PIX key (cached)
  pixKey: string;
  setPixKey: (k: string) => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (text: string, type?: Toast['type']) => void;
  removeToast: (id: number) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  lowStockCount: 0,
  setLowStockCount: (n) => set({ lowStockCount: n }),

  pixKey: '',
  setPixKey: (k) => set({ pixKey: k }),

  toasts: [],
  addToast: (text, type = 'success') => {
    const id = ++toastCounter;
    set((s) => ({ toasts: [...s.toasts, { id, text, type }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3500);
  },
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

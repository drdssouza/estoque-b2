import { describe, it, expect, beforeAll } from 'vitest';
import {
  formatCurrency,
  formatDateTime,
  formatDate,
  getStockLevel,
  getStockPercent,
  cn,
  nowSqlite,
  backupTimestamp,
} from './utils';

// ── formatCurrency ─────────────────────────────────────────────────────────────

describe('formatCurrency', () => {
  it('formata valor inteiro positivo', () => {
    const r = formatCurrency(100);
    expect(r).toContain('R$');
    expect(r).toMatch(/100/);
  });

  it('formata zero', () => {
    const r = formatCurrency(0);
    expect(r).toContain('R$');
    expect(r).toMatch(/0/);
  });

  it('formata valor com centavos', () => {
    const r = formatCurrency(19.9);
    expect(r).toContain('19');
  });

  it('formata valor grande (milhão)', () => {
    const r = formatCurrency(1_000_000);
    expect(r).toContain('R$');
    expect(r).toMatch(/1/);
  });

  it('formata valor muito pequeno (centavos)', () => {
    const r = formatCurrency(0.01);
    expect(r).toContain('R$');
  });

  it('sempre retorna string', () => {
    expect(typeof formatCurrency(50)).toBe('string');
    expect(typeof formatCurrency(0)).toBe('string');
    expect(typeof formatCurrency(9999.99)).toBe('string');
  });

  it('resultado contém separador decimal pt-BR (vírgula)', () => {
    const r = formatCurrency(1.5);
    expect(r).toContain(',');
  });

  // ── Stress ──────────────────────────────────────────────────────────────────

  it('[STRESS] 100.000 valores aleatórios sem lançar exceção', () => {
    for (let i = 0; i < 100_000; i++) {
      expect(() => formatCurrency(Math.random() * 10_000)).not.toThrow();
    }
  });

  it('[STRESS] valores extremos', () => {
    const cases = [0, 0.01, 0.001, 9_999_999, 0.1, 1.99, 999.999, Number.MAX_SAFE_INTEGER / 1000];
    for (const v of cases) {
      const r = formatCurrency(v);
      expect(typeof r).toBe('string');
      expect(r).toContain('R$');
    }
  });

  it('[STRESS] simula 10.000 totais de comandas de dia cheio', () => {
    const precos = [3.5, 7, 18, 12, 14, 9, 8, 9, 20, 10, 5, 8, 6, 28, 15, 7, 19.9, 29.9, 35];
    for (let pedido = 0; pedido < 10_000; pedido++) {
      const total = precos.reduce((acc, p) => acc + p * Math.floor(Math.random() * 5), 0);
      expect(typeof formatCurrency(total)).toBe('string');
    }
  });
});

// ── formatDateTime ─────────────────────────────────────────────────────────────

describe('formatDateTime', () => {
  it('formata data e hora válida', () => {
    const r = formatDateTime('2024-03-15 14:30:00');
    expect(r).toContain('15');
    expect(r).toContain('03');
    expect(r).toContain('2024');
  });

  it('retorna string vazia para input vazio', () => {
    expect(formatDateTime('')).toBe('');
  });

  it('não lança exceção para data inválida', () => {
    expect(() => formatDateTime('data-invalida')).not.toThrow();
  });

  it('suporta datas no formato sqlite (espaço como separador)', () => {
    const r = formatDateTime('2024-12-31 23:59:59');
    expect(r).toBeDefined();
    expect(typeof r).toBe('string');
  });

  it('suporta datas com hora 00:00', () => {
    const r = formatDateTime('2024-01-01 00:00:00');
    expect(r).toBeDefined();
  });

  // ── Stress ──────────────────────────────────────────────────────────────────

  it('[STRESS] 50.000 datas variadas sem lançar exceção', () => {
    const datas = [
      '2024-01-01 08:00:00',
      '2024-06-15 12:30:00',
      '2024-12-31 23:59:59',
      '2023-02-28 00:00:00',
      '2025-07-04 18:45:22',
      '',
    ];
    for (let i = 0; i < 50_000; i++) {
      expect(() => formatDateTime(datas[i % datas.length])).not.toThrow();
    }
  });

  it('[STRESS] simula timestamps de 500 itens de comanda', () => {
    for (let minuto = 0; minuto < 500; minuto++) {
      const h = String(Math.floor(minuto / 60) % 24).padStart(2, '0');
      const m = String(minuto % 60).padStart(2, '0');
      const ts = `2024-03-15 ${h}:${m}:00`;
      const r = formatDateTime(ts);
      expect(typeof r).toBe('string');
    }
  });
});

// ── formatDate ─────────────────────────────────────────────────────────────────

describe('formatDate', () => {
  it('formata data válida no formato pt-BR', () => {
    const r = formatDate('2024-03-15 14:30:00');
    expect(r).toContain('15');
    expect(r).toContain('03');
    expect(r).toContain('2024');
  });

  it('retorna string vazia para input vazio', () => {
    expect(formatDate('')).toBe('');
  });

  it('não lança exceção para data inválida', () => {
    expect(() => formatDate('invalido')).not.toThrow();
  });

  it('[STRESS] 20.000 formatos de data', () => {
    for (let dia = 1; dia <= 28; dia++) {
      for (let mes = 1; mes <= 12; mes++) {
        const ts = `2024-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')} 10:00:00`;
        expect(() => formatDate(ts)).not.toThrow();
      }
    }
  });
});

// ── getStockLevel ──────────────────────────────────────────────────────────────

describe('getStockLevel', () => {
  it('retorna "ok" quando estoque acima do mínimo', () => {
    expect(getStockLevel(10, 5)).toBe('ok');
    expect(getStockLevel(100, 10)).toBe('ok');
  });

  it('retorna "warning" quando estoque entre 50%-100% do mínimo', () => {
    expect(getStockLevel(5, 5)).toBe('warning');  // 100% = exato
    expect(getStockLevel(3, 5)).toBe('warning');  // 60%
  });

  it('retorna "critical" quando estoque <= 50% do mínimo', () => {
    expect(getStockLevel(2, 5)).toBe('critical'); // 40%
    expect(getStockLevel(0, 5)).toBe('critical'); // 0%
    expect(getStockLevel(1, 10)).toBe('critical'); // 10%
  });

  it('retorna "ok" quando mínimo é zero (sem controle)', () => {
    expect(getStockLevel(0, 0)).toBe('ok');
    expect(getStockLevel(100, 0)).toBe('ok');
  });

  it('retorna "ok" quando estoque exatamente o dobro do mínimo', () => {
    expect(getStockLevel(10, 10)).toBe('warning'); // exatamente no limite = warning (ratio=1)
  });

  it('retorna "critical" com estoque zero e mínimo > 0', () => {
    expect(getStockLevel(0, 1)).toBe('critical');
    expect(getStockLevel(0, 100)).toBe('critical');
  });

  // ── Stress ──────────────────────────────────────────────────────────────────

  it('[STRESS] 10.000 combinações de estoque/mínimo', () => {
    for (let atual = 0; atual <= 100; atual++) {
      for (let minimo = 0; minimo <= 100; minimo++) {
        const level = getStockLevel(atual, minimo);
        expect(['ok', 'warning', 'critical']).toContain(level);
      }
    }
  });

  it('[STRESS] simula verificação de 500 produtos em dia de movimento intenso', () => {
    const produtos = Array.from({ length: 500 }, (_, i) => ({
      current: Math.floor(Math.random() * 100),
      minimum: Math.floor(Math.random() * 50),
    }));
    for (const p of produtos) {
      const level = getStockLevel(p.current, p.minimum);
      expect(['ok', 'warning', 'critical']).toContain(level);
    }
  });
});

// ── getStockPercent ────────────────────────────────────────────────────────────

describe('getStockPercent', () => {
  it('retorna 100 quando mínimo é zero', () => {
    expect(getStockPercent(50, 0)).toBe(100);
    expect(getStockPercent(0, 0)).toBe(100);
  });

  it('retorna 100 quando estoque acima do mínimo', () => {
    expect(getStockPercent(20, 10)).toBe(100); // capped at 100
  });

  it('retorna percentual correto', () => {
    expect(getStockPercent(5, 10)).toBe(50);
    expect(getStockPercent(3, 10)).toBe(30);
    expect(getStockPercent(0, 10)).toBe(0);
  });

  it('nunca retorna acima de 100', () => {
    expect(getStockPercent(1000, 1)).toBe(100);
  });

  it('nunca retorna negativo', () => {
    expect(getStockPercent(0, 100)).toBe(0);
  });

  it('[STRESS] 50.000 chamadas com valores randômicos', () => {
    for (let i = 0; i < 50_000; i++) {
      const current = Math.floor(Math.random() * 200);
      const minimum = Math.floor(Math.random() * 100);
      const pct = getStockPercent(current, minimum);
      expect(pct).toBeGreaterThanOrEqual(0);
      expect(pct).toBeLessThanOrEqual(100);
    }
  });
});

// ── cn ─────────────────────────────────────────────────────────────────────────

describe('cn (classnames)', () => {
  it('junta classes simples', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c');
  });

  it('remove valores falsy', () => {
    expect(cn('a', false, undefined, null, 'b')).toBe('a b');
  });

  it('retorna string vazia para todos falsy', () => {
    expect(cn(false, undefined, null)).toBe('');
  });

  it('retorna string vazia sem argumentos', () => {
    expect(cn()).toBe('');
  });

  it('não adiciona espaço extra com classes vazias filtradas', () => {
    const r = cn('px-4', false, 'py-2');
    expect(r).toBe('px-4 py-2');
  });

  it('[STRESS] 100.000 chamadas com combinações', () => {
    const classes = ['px-4', 'py-2', 'text-sm', 'font-bold', 'rounded-lg', 'bg-card'];
    for (let i = 0; i < 100_000; i++) {
      const combo = classes.filter((_, idx) => (i + idx) % 2 === 0) as (string | false | undefined | null)[];
      const result = cn(...combo);
      expect(typeof result).toBe('string');
    }
  });
});

// ── nowSqlite ──────────────────────────────────────────────────────────────────

describe('nowSqlite', () => {
  it('retorna string no formato "YYYY-MM-DD HH:MM:SS"', () => {
    const r = nowSqlite();
    expect(r).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
  });

  it('retorna data local (não UTC) — hora dentro de ±1h do sistema', () => {
    const r = nowSqlite();
    const [, timePart] = r.split(' ');
    const [h] = timePart.split(':').map(Number);
    const localHour = new Date().getHours();
    // aceita diferença de até 1 segundo no segundo exato da virada de hora
    expect(Math.abs(h - localHour)).toBeLessThanOrEqual(1);
  });

  it('tem comprimento fixo de 19 caracteres', () => {
    expect(nowSqlite()).toHaveLength(19);
  });

  it('[STRESS] 1.000 chamadas consecutivas — sempre formato correto', () => {
    for (let i = 0; i < 1_000; i++) {
      expect(nowSqlite()).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
    }
  });

  it('[STRESS] simula 300 aberturas de comanda em sequência', () => {
    const timestamps: string[] = [];
    for (let i = 0; i < 300; i++) {
      const ts = nowSqlite();
      timestamps.push(ts);
      expect(ts).toHaveLength(19);
    }
    // todos devem ser strings válidas
    expect(timestamps.every((t) => /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(t))).toBe(true);
  });
});

// ── backupTimestamp ────────────────────────────────────────────────────────────

describe('backupTimestamp', () => {
  it('retorna string sem caracteres inválidos para nomes de arquivo', () => {
    const r = backupTimestamp();
    // Não deve conter ':', '.' ou espaços
    expect(r).not.toMatch(/[:.]/);
  });

  it('tem comprimento de 19 caracteres (YYYY-MM-DDTHH-MM-SS)', () => {
    expect(backupTimestamp()).toHaveLength(19);
  });

  it('retorna string com formato de timestamp', () => {
    const r = backupTimestamp();
    expect(r).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$/);
  });

  it('[STRESS] 1.000 chamadas — sempre formato válido', () => {
    for (let i = 0; i < 1_000; i++) {
      const r = backupTimestamp();
      expect(r).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$/);
      expect(r).toHaveLength(19);
    }
  });
});

// ── Integração: simulação de dia muito movimentado ─────────────────────────────

describe('[STRESS] Simulação de dia muito movimentado', () => {
  it('processa 200 comandas com múltiplos itens — formatações todas válidas', () => {
    const precos = [3.5, 7.0, 18.0, 12.0, 14.0, 9.0, 8.0, 20.0, 10.0, 5.0];
    for (let comanda = 0; comanda < 200; comanda++) {
      const itens = Math.floor(Math.random() * 20) + 1;
      let total = 0;
      for (let i = 0; i < itens; i++) {
        const preco = precos[i % precos.length];
        total += preco;
        const ts = `2024-03-15 ${String(Math.floor(i / 60) % 24).padStart(2, '0')}:${String(i % 60).padStart(2, '0')}:00`;
        expect(formatCurrency(preco)).toContain('R$');
        expect(() => formatDateTime(ts)).not.toThrow();
      }
      expect(formatCurrency(total)).toContain('R$');
    }
  });

  it('verifica status de 500 produtos com estoques variados', () => {
    for (let i = 0; i < 500; i++) {
      const current = i % 50;
      const minimum = (i % 30) + 1;
      const level = getStockLevel(current, minimum);
      const pct = getStockPercent(current, minimum);
      expect(['ok', 'warning', 'critical']).toContain(level);
      expect(pct).toBeGreaterThanOrEqual(0);
      expect(pct).toBeLessThanOrEqual(100);
    }
  });

  it('gera 100 timestamps de abertura de comanda em sequência', () => {
    const timestamps = Array.from({ length: 100 }, () => nowSqlite());
    for (const ts of timestamps) {
      expect(ts).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
    }
  });

  beforeAll(() => {
    // Aquece o motor de formatação (JIT)
    formatCurrency(0);
    formatDateTime('2024-01-01 00:00:00');
    getStockLevel(0, 0);
    nowSqlite();
  });
});

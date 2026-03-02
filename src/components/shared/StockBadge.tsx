import React from 'react';
import { getStockLevel, getStockPercent } from '../../lib/utils';
import { cn } from '../../lib/utils';

interface StockBadgeProps {
  current: number;
  minimum: number;
  showText?: boolean;
}

export function StockBadge({ current, minimum, showText = false }: StockBadgeProps) {
  const level = getStockLevel(current, minimum);
  const pct = getStockPercent(current, minimum);

  const styles = {
    ok: 'bg-primary-subtle text-primary-light border-primary/20',
    warning: 'bg-warning-subtle text-warning border-warning/20',
    critical: 'bg-danger-subtle text-danger border-danger/20',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-sm font-semibold border',
        styles[level]
      )}
    >
      {current}
      {showText && minimum > 0 && (
        <span className="text-xs font-normal opacity-70">/ {minimum} ({pct}%)</span>
      )}
    </span>
  );
}

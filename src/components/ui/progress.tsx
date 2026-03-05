import React from 'react';
import { cn } from '../../lib/utils';

interface ProgressProps {
  value: number; // 0-100
  className?: string;
  color?: 'green' | 'yellow' | 'red' | 'blue';
}

const colors = {
  green: 'bg-primary',
  yellow: 'bg-warning',
  red: 'bg-danger',
  blue: 'bg-info',
};

export function Progress({ value, className, color = 'green' }: ProgressProps) {
  return (
    <div
      className={cn(
        'w-full h-1.5 bg-white/10 rounded-full overflow-hidden',
        className
      )}
    >
      <div
        className={cn('h-full rounded-full transition-all duration-500', colors[color])}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

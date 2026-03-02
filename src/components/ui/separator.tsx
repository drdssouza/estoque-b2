import React from 'react';
import { cn } from '../../lib/utils';

interface SeparatorProps {
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

export function Separator({ className, orientation = 'horizontal' }: SeparatorProps) {
  return (
    <div
      className={cn(
        'bg-border',
        orientation === 'horizontal' ? 'h-px w-full' : 'w-px h-full',
        className
      )}
    />
  );
}

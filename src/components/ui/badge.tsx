import React from 'react';
import { cn } from '../../lib/utils';

type BadgeVariant = 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'gray';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

const variants: Record<BadgeVariant, string> = {
  green: 'bg-primary-subtle text-primary-light border border-primary/20',
  red: 'bg-danger-subtle text-danger border border-danger/20',
  yellow: 'bg-warning-subtle text-warning border border-warning/20',
  blue: 'bg-info-subtle text-info border border-info/20',
  purple: 'bg-purple-subtle text-purple border border-purple/20',
  gray: 'bg-white/5 text-muted border border-border',
};

const dotColors: Record<BadgeVariant, string> = {
  green: 'bg-primary',
  red: 'bg-danger',
  yellow: 'bg-warning',
  blue: 'bg-info',
  purple: 'bg-purple',
  gray: 'bg-muted',
};

export function Badge({ variant = 'gray', dot, children, className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold',
        variants[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} />
      )}
      {children}
    </span>
  );
}

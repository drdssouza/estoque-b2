import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  noPad?: boolean;
}

export function Card({ className, noPad, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'bg-card border border-border rounded-xl',
        !noPad && 'p-5',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('text-sm font-semibold text-muted uppercase tracking-wider', className)}
      {...props}
    >
      {children}
    </h3>
  );
}

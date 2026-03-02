import React from 'react';
import { cn } from '../../lib/utils';

type Variant = 'primary' | 'danger' | 'ghost' | 'secondary' | 'warning' | 'info' | 'purple';
type Size = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

const variants: Record<Variant, string> = {
  primary:
    'bg-primary hover:bg-primary-dark text-black font-semibold shadow-[0_0_12px_rgba(34,197,94,0.3)] hover:shadow-[0_0_18px_rgba(34,197,94,0.45)]',
  danger:
    'bg-danger hover:bg-danger-dark text-white',
  ghost:
    'bg-transparent hover:bg-white/5 text-muted hover:text-white border border-border',
  secondary:
    'bg-card hover:bg-card-hover text-white border border-border',
  warning:
    'bg-warning hover:bg-amber-600 text-black font-semibold',
  info:
    'bg-info hover:bg-blue-600 text-white',
  purple:
    'bg-purple hover:bg-violet-600 text-white',
};

const sizes: Record<Size, string> = {
  xs: 'px-2.5 py-1 text-xs h-7 rounded',
  sm: 'px-3 py-1.5 text-xs h-8 rounded-md',
  md: 'px-4 py-2 text-sm h-9 rounded-md',
  lg: 'px-5 py-2.5 text-sm h-10 rounded-lg',
};

export function Button({
  variant = 'secondary',
  size = 'md',
  isLoading,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-1.5 font-medium transition-all duration-150',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children}
    </button>
  );
}

import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
function Input({ label, error, leftIcon, className, id, ...props }, ref) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-muted uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none">
            {leftIcon}
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full h-10 rounded-lg border border-border bg-input px-3 text-sm text-white placeholder:text-muted',
            'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40',
            'transition-colors duration-150',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            !!leftIcon && 'pl-9',
            error && 'border-danger focus:border-danger focus:ring-danger/40',
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
});

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ label, className, id, ...props }: TextareaProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-muted uppercase tracking-wider">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={cn(
          'w-full rounded-lg border border-border bg-input px-3 py-2.5 text-sm text-white placeholder:text-muted',
          'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40',
          'transition-colors duration-150 resize-none',
          className
        )}
        {...props}
      />
    </div>
  );
}

import React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export function Select({ label, options, className, id, ...props }: SelectProps) {
  const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-muted uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          className={cn(
            'w-full h-10 rounded-lg border border-border bg-input pl-3 pr-8 text-sm text-white',
            'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40',
            'transition-colors duration-150 appearance-none cursor-pointer',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-card text-white">
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
        />
      </div>
    </div>
  );
}

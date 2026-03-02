import { Dialog } from '../ui/dialog';
import { Button } from '../ui/button';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmLabel?: string;
  isLoading?: boolean;
  variant?: 'danger' | 'warning';
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Confirmar ação',
  message,
  confirmLabel = 'Confirmar',
  isLoading,
  variant = 'danger',
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} size="sm">
      <div className="flex flex-col items-center gap-4 text-center">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            variant === 'danger' ? 'bg-danger-subtle' : 'bg-warning-subtle'
          }`}
        >
          <AlertTriangle
            size={22}
            className={variant === 'danger' ? 'text-danger' : 'text-warning'}
          />
        </div>

        <div>
          <p className="text-base font-semibold text-white">{title}</p>
          <p className="text-sm text-muted mt-1">{message}</p>
        </div>

        <div className="flex gap-3 w-full">
          <Button
            variant="ghost"
            className="flex-1"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancelar
          </Button>
          <Button
            variant={variant}
            className="flex-1"
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

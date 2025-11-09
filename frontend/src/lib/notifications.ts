
import { toast } from 'sonner';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export interface NotificationOptions {
  title: string;
  message: string;
  type?: NotificationType;
  duration?: number;
}

export function showNotification({ title, message, type = 'info', duration }: NotificationOptions) {
  const options = {
    description: message,
    duration,
  };

  switch (type) {
    case 'success':
      toast.success(title, options);
      break;
    case 'error':
      toast.error(title, options);
      break;
    case 'warning':
      toast.warning(title, options);
      break;
    default:
      toast.info(title, options);
      break;
  }
}

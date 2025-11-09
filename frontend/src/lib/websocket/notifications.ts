
import { toast } from 'sonner';

export interface NotificationPayload {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export function handleNotification(payload: NotificationPayload) {
  switch (payload.type) {
    case 'info':
      toast.info(payload.title, { description: payload.message });
      break;
    case 'success':
      toast.success(payload.title, { description: payload.message });
      break;
    case 'warning':
      toast.warning(payload.title, { description: payload.message });
      break;
    case 'error':
      toast.error(payload.title, { description: payload.message });
      break;
    default:
      toast(payload.title, { description: payload.message });
      break;
  }
}


import { useOnlineStatus } from '../../hooks/useOnlineStatus';

export function ConnectionStatus() {
  const isOnline = useOnlineStatus();

  if (!isOnline) {
    return <div>Offline</div>;
  }

  return <div>Connected</div>;
}

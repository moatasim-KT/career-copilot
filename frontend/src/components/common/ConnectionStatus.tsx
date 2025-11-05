
import { useOnlineStatus } from '../../hooks/useOnlineStatus';
import { useWebSocket } from '../../hooks/useWebSocket';

export function ConnectionStatus() {
  const isOnline = useOnlineStatus();
  const { connectionStatus } = useWebSocket(); // Assuming useWebSocket provides connectionStatus

  if (!isOnline) {
    return <div>Offline</div>;
  }

  switch (connectionStatus) {
    case 'connecting':
      return <div>Connecting...</div>;
    case 'open':
      return <div>Connected</div>;
    case 'closed':
      return <div>Disconnected</div>;
    default:
      return null;
  }
}

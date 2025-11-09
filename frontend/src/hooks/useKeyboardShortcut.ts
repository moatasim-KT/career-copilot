
import React from 'react';

export function useKeyboardShortcut(
  callback: () => void,
  key: string,
  metaKey = true,
) {
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === key && (metaKey ? e.metaKey || e.ctrlKey : true)) {
        e.preventDefault();
        callback();
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [callback, key, metaKey]);
}

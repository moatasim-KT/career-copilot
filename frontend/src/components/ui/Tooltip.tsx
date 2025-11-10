
import React, { useState, useRef } from 'react';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  maxWidth?: number;
}

export default function Tooltip({ content, children, position = 'top', delay = 100, maxWidth = 240 }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowPosition = {
    top: 'bottom-0 left-1/2 -translate-x-1/2',
    bottom: 'top-0 left-1/2 -translate-x-1/2 rotate-180',
    left: 'right-0 top-1/2 -translate-y-1/2 -rotate-90',
    right: 'left-0 top-1/2 -translate-y-1/2 rotate-90',
  };

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => setVisible(true), delay);
  };
  const hideTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(false);
  };

  return (
    <div className="relative inline-block" onMouseEnter={showTooltip} onMouseLeave={hideTooltip}>
      {children}
      {visible && (
        <div
          className={`absolute z-10 px-3 py-2 text-sm font-medium text-white glass rounded-lg shadow-lg ${positionClasses[position]}`}
          style={{ maxWidth }}
        >
          {content}
          <span
            className={`absolute w-3 h-3 glass rotate-45 ${arrowPosition[position]}`}
            style={{ boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
          />
        </div>
      )}
    </div>
  );
}

import React from 'react';

interface TimelineEvent {
  id: string;
  date: string;
  description: string;
  icon?: React.ReactNode;
  color?: string;
}

interface ApplicationTimelineProps {
  events: TimelineEvent[];
}

export function ApplicationTimeline({ events }: ApplicationTimelineProps) {
  return (
    <div className="relative border-l border-gray-200 dark:border-gray-700 ml-4">
      {events.map((event) => (
        <div key={event.id} className="mb-8 flex items-start">
          <div className={`flex items-center justify-center w-8 h-8 rounded-full ring-8 ring-white dark:ring-gray-900 bg-${event.color || 'blue'}-100 dark:bg-${event.color || 'blue'}-900 text-${event.color || 'blue'}-800 dark:text-${event.color || 'blue'}-300 flex-shrink-0`}>
            {event.icon || (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"></path></svg>
            )}
          </div>
          <div className="ml-6">
            <h3 className="flex items-center mb-1 text-lg font-semibold text-gray-900 dark:text-white">
              {event.description}
            </h3>
            <time className="block mb-2 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
              {event.date}
            </time>
          </div>
        </div>
      ))}
    </div>
  );
}

import React from 'react';

interface Application {
  id: string;
  title: string;
  company: string;
  status: string;
}

interface Column {
  id: string;
  title: string;
  applicationIds: string[];
}

interface KanbanBoardProps {
  initialApplications: Application[];
  initialColumns: Column[];
}

export function KanbanBoard({ initialApplications, initialColumns }: KanbanBoardProps) {
  return (
    <div className="p-4">
      <h1>Kanban Board (Simplified)</h1>
      {initialColumns.map((column) => (
        <div key={column.id} className="border p-2 m-2">
          <h2>{column.title}</h2>
          {column.applicationIds.map((appId) => {
            const app = initialApplications.find(a => a.id === appId);
            return app ? <p key={app.id}>{app.title} - {app.company}</p> : null;
          })}
        </div>
      ))}
    </div>
  );
}
'use client';

import React, { useEffect, useState } from 'react';

import { DocumentUpload } from '@/components/features/DocumentUpload';
import { InterviewPreparation, InterviewQuestion } from '@/components/features/InterviewPreparation';
import { NotesAndReminders } from '@/components/features/NotesAndReminders';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { ApplicationTimeline } from '@/components/ui/ApplicationTimeline';
import { ApplicationsService, type ApplicationResponse } from '@/lib/api/client';

interface Column {
  id: string;
  title: string;
  applicationIds: (string | number)[];
}

const dummyTimelineEvents = [
  { id: '1', date: '2023-01-15', description: 'Applied for Frontend Developer at Tech Solutions', color: 'blue' },
  { id: '2', date: '2023-01-20', description: 'Interview scheduled with Tech Solutions', color: 'purple' },
  { id: '3', date: '2023-02-01', description: 'Offer received from Cloud Services', color: 'green' },
  { id: '4', date: '2023-02-05', description: 'Accepted offer from Cloud Services', color: 'green' },
];

const dummyInterviewQuestions: InterviewQuestion[] = [
  {
    id: '1',
    question: 'Tell me about a time you failed.',
    type: 'behavioral',
    tips: [
      'Choose a real failure, not a disguised success.',
      'Focus on what you learned and how you applied it.',
      'Keep it concise and professional.',
    ],
  },
  {
    id: '2',
    question: 'Explain closures in JavaScript.',
    type: 'technical',
    tips: [
      'Define what a closure is.',
      'Provide a simple code example.',
      'Explain its practical uses (e.g., data privacy, currying).',
    ],
  },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [columns, setColumns] = useState<Column[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showTimeline, setShowTimeline] = useState(false);
  const [showInterviewPrep, setShowInterviewPrep] = useState(false);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [showNotesAndReminders, setShowNotesAndReminders] = useState(false);

  useEffect(() => {
    const loadApplications = async () => {
      setIsLoading(true);
      try {
        const response = await ApplicationsService.getApplicationsApiV1ApplicationsGet();
        setApplications(response);
        // This is a simplified column generation. A real implementation
        // would likely involve more sophisticated logic.
        const columns: Column[] = [
          { id: 'applied', title: 'Applied', applicationIds: response.filter(a => a.status === 'Applied').map(a => a.id) },
          { id: 'interviewing', title: 'Interviewing', applicationIds: response.filter(a => a.status === 'Interviewing').map(a => a.id) },
          { id: 'offer', title: 'Offer', applicationIds: response.filter(a => a.status === 'Offer').map(a => a.id) },
          { id: 'rejected', title: 'Rejected', applicationIds: response.filter(a => a.status === 'Rejected').map(a => a.id) },
        ];
        setColumns(columns);
      } catch (err) {
        setError('Failed to load applications');
      } finally {
        setIsLoading(false);
      }
    };

    loadApplications();
  }, []);

  const dummyDocuments = [
    { id: 'doc1', name: 'Resume.pdf', url: '#', type: 'pdf', uploadedAt: '2023-10-26' },
    { id: 'doc2', name: 'CoverLetter.docx', url: '#', type: 'docx', uploadedAt: '2023-10-25' },
  ];

  const handleDocumentUpload = (file: File) => {
    console.log('Uploading file:', file.name);
    // In a real app, you'd handle file upload to a backend here
    // For now, just add a dummy document
    const newDoc = {
      id: `doc${Math.random()}`,
      name: file.name,
      url: '#',
      type: file.type,
      uploadedAt: new Date().toISOString().split('T')[0],
    };
    // This would typically update a state or call an API
    alert(`Dummy upload of ${file.name} successful!`);
  };

  const handleDocumentDelete = (id: string) => {
    console.log('Deleting document:', id);
    // In a real app, you'd handle file deletion from a backend here
    alert(`Dummy deletion of ${id} successful!`);
  };

  const [notes, setNotes] = useState([
    { id: 'note1', content: 'Follow up with HR on Friday.', createdAt: '2023-11-01' },
    { id: 'note2', content: 'Research company culture.', createdAt: '2023-10-30' },
  ]);

  const [reminders, setReminders] = useState([
    { id: 'rem1', content: 'Send thank you note', dueDate: '2023-11-07', isCompleted: false },
    { id: 'rem2', content: 'Prepare for technical interview', dueDate: '2023-11-10', isCompleted: false },
  ]);

  const handleAddNote = (content: string) => {
    setNotes(prev => [...prev, { id: `note${Date.now()}`, content, createdAt: new Date().toISOString().split('T')[0] }]);
  };

  const handleDeleteNote = (id: string) => {
    setNotes(prev => prev.filter(note => note.id !== id));
  };

  const handleUpdateNote = (id: string, content: string) => {
    setNotes(prev => prev.map(note => (note.id === id ? { ...note, content } : note)));
  };

  const handleAddReminder = (content: string, dueDate: string) => {
    setReminders(prev => [...prev, { id: `rem${Date.now()}`, content, dueDate, isCompleted: false }]);
  };

  const handleDeleteReminder = (id: string) => {
    setReminders(prev => prev.filter(rem => rem.id !== id));
  };

  const handleToggleReminder = (id: string) => {
    setReminders(prev => prev.map(rem => (rem.id === id ? { ...rem, isCompleted: !rem.isCompleted } : rem)));
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Applications Management</h1>
        <div className="flex space-x-4">
          <button
            onClick={() => {
              setShowTimeline(false);
              setShowInterviewPrep(false);
              setShowDocumentUpload(prev => !prev);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            {showDocumentUpload ? 'View Applications' : 'Document Management'}
          </button>
          <button
            onClick={() => {
              setShowTimeline(false);
              setShowInterviewPrep(false);
              setShowDocumentUpload(false);
              setShowNotesAndReminders(prev => !prev);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            {showNotesAndReminders ? 'View Applications' : 'Notes & Reminders'}
          </button>
          <button
            onClick={() => {
              setShowDocumentUpload(false);
              setShowInterviewPrep(false);
              setShowTimeline(prev => !prev);
              setShowNotesAndReminders(false);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            {showTimeline ? 'View Kanban Board' : 'View Timeline'}
          </button>
          <button
            onClick={() => {
              setShowDocumentUpload(false);
              setShowTimeline(false);
              setShowInterviewPrep(prev => !prev);
              setShowNotesAndReminders(false);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            {showInterviewPrep ? 'View Applications' : 'Interview Prep'}
          </button>
        </div>
      </div>

      {showNotesAndReminders ? (
        <NotesAndReminders
          initialNotes={notes}
          initialReminders={reminders}
          onAddNote={handleAddNote}
          onDeleteNote={handleDeleteNote}
          onUpdateNote={handleUpdateNote}
          onAddReminder={handleAddReminder}
          onDeleteReminder={handleDeleteReminder}
          onToggleReminder={handleToggleReminder}
        />
      ) : showDocumentUpload ? (
        <DocumentUpload
          documents={dummyDocuments}
          onUpload={handleDocumentUpload}
          onDelete={handleDocumentDelete}
        />
      ) : showInterviewPrep ? (
        <InterviewPreparation questions={dummyInterviewQuestions} />
      ) : showTimeline ? (
        <ApplicationTimeline events={dummyTimelineEvents} />
      ) : (
        isLoading ? (
          <div>Loading...</div>
        ) : error ? (
          <div>{error}</div>
        ) : (
          <KanbanBoard
            initialApplications={applications}
            initialColumns={columns}
          />
        )
      )}
    </div>
  );
}
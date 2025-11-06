import { Plus, Edit, Trash2, Bell } from 'lucide-react';
import React, { useState } from 'react';

interface Note {
  id: string;
  content: string;
  createdAt: string;
}

interface Reminder {
  id: string;
  content: string;
  dueDate: string;
  isCompleted: boolean;
}

interface NotesAndRemindersProps {
  initialNotes: Note[];
  initialReminders: Reminder[];
  onAddNote: (content: string) => void;
  onDeleteNote: (id: string) => void;
  onUpdateNote: (id: string, content: string) => void;
  onAddReminder: (content: string, dueDate: string) => void;
  onDeleteReminder: (id: string) => void;
  onToggleReminder: (id: string) => void;
}

export function NotesAndReminders({
  initialNotes,
  initialReminders,
  onAddNote,
  onDeleteNote,
  onUpdateNote,
  onAddReminder,
  onDeleteReminder,
  onToggleReminder,
}: NotesAndRemindersProps) {
  const [newNoteContent, setNewNoteContent] = useState('');
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editingNoteContent, setEditingNoteContent] = useState('');

  const [newReminderContent, setNewReminderContent] = useState('');
  const [newReminderDueDate, setNewReminderDueDate] = useState('');

  const handleAddNote = () => {
    if (newNoteContent.trim()) {
      onAddNote(newNoteContent);
      setNewNoteContent('');
    }
  };

  const handleUpdateNote = (id: string) => {
    if (editingNoteContent.trim()) {
      onUpdateNote(id, editingNoteContent);
      setEditingNoteId(null);
      setEditingNoteContent('');
    }
  };

  const handleAddReminder = () => {
    if (newReminderContent.trim() && newReminderDueDate.trim()) {
      onAddReminder(newReminderContent, newReminderDueDate);
      setNewReminderContent('');
      setNewReminderDueDate('');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Notes Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Notes</h2>
        <div className="space-y-4">
          {initialNotes.map(note => (
            <div key={note.id} className="border border-gray-200 rounded-md p-4">
              {editingNoteId === note.id ? (
                <div className="flex flex-col space-y-2">
                  <textarea
                    value={editingNoteContent}
                    onChange={(e) => setEditingNoteContent(e.target.value)}
                    className="w-full p-2 border rounded-md"
                    rows={3}
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => handleUpdateNote(note.id)}
                      className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingNoteId(null)}
                      className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-800">{note.content}</p>
                    <p className="text-xs text-gray-500 mt-1">{note.createdAt}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        setEditingNoteId(note.id);
                        setEditingNoteContent(note.content);
                      }}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onDeleteNote(note.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}

          <div className="flex space-x-2">
            <textarea
              value={newNoteContent}
              onChange={(e) => setNewNoteContent(e.target.value)}
              placeholder="Add a new note..."
              className="flex-grow p-2 border border-gray-300 rounded-md"
              rows={3}
            />
            <button onClick={handleAddNote} className="px-4 py-2 bg-blue-600 text-white rounded-md">
              <Plus className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Reminders Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Reminders</h2>
        <div className="space-y-4">
          {initialReminders.map(reminder => (
            <div key={reminder.id} className="flex items-center justify-between border border-gray-200 rounded-md p-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={reminder.isCompleted}
                  onChange={() => onToggleReminder(reminder.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
                />
                <div>
                  <p className={`text-gray-800 ${reminder.isCompleted ? 'line-through text-gray-500' : ''}`}>{reminder.content}</p>
                  <p className="text-xs text-gray-500 mt-1">Due: {reminder.dueDate}</p>
                </div>
              </div>
              <button onClick={() => onDeleteReminder(reminder.id)} className="text-red-600 hover:text-red-800">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}

          <div className="flex flex-col space-y-2">
            <input
              type="text"
              value={newReminderContent}
              onChange={(e) => setNewReminderContent(e.target.value)}
              placeholder="Add a new reminder..."
              className="p-2 border border-gray-300 rounded-md"
            />
            <input
              type="date"
              value={newReminderDueDate}
              onChange={(e) => setNewReminderDueDate(e.target.value)}
              className="p-2 border border-gray-300 rounded-md"
            />
            <button onClick={handleAddReminder} className="px-4 py-2 bg-blue-600 text-white rounded-md flex items-center justify-center space-x-2">
              <Bell className="h-5 w-5" />
              <span>Add Reminder</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

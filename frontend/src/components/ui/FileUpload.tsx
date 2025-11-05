'use client';

import { Upload } from 'lucide-react';
import { useState, type Dispatch, type SetStateAction, type ChangeEventHandler } from 'react';

import { apiClient } from '@/lib/api';

interface FileUploadProps {
  onUploadSuccess: Dispatch<SetStateAction<unknown>>;
}

interface FileUploadContentProps {
  file: File | null;
  uploading: boolean;
  error: string | null;
  success: string | null;
  onFileChange: ChangeEventHandler<HTMLInputElement>;
  onUploadClick: () => void;
}

function FileUploadContent({ file, uploading, error, success, onFileChange, onUploadClick }: FileUploadContentProps) {
  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors">
      <input
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={onFileChange}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload" className="flex flex-col items-center justify-center space-y-2">
        <Upload className="w-12 h-12 text-gray-400" />
        <p className="text-sm text-gray-600">{file ? file.name : 'Click to upload or drag and drop'}</p>
        <p className="text-xs text-gray-500">PDF, DOCX, DOC, or TXT (MAX. 5MB)</p>
      </label>
      {file && (
        <button
          onClick={onUploadClick}
          disabled={uploading}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-400 flex items-center gap-2 mx-auto"
        >
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploading...' : 'Upload Resume'}
        </button>
      )}
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      {success && <p className="text-green-600 text-sm mt-2">{success}</p>}
    </div>
  );
}

function createFileChangeHandler(
  setFile: Dispatch<SetStateAction<File | null>>,
  setError: Dispatch<SetStateAction<string | null>>,
  setSuccess: Dispatch<SetStateAction<string | null>>,
) {
  return (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(null);
    }
  };
}

function createUploadHandler(args: {
  fileRef: () => File | null;
  setUploading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
  setSuccess: Dispatch<SetStateAction<string | null>>;
  setFile: Dispatch<SetStateAction<File | null>>;
  onUploadSuccess: Dispatch<SetStateAction<unknown>>;
}) {
  const { fileRef, setUploading, setError, setSuccess, setFile, onUploadSuccess } = args;
  return async () => {
    const file = fileRef();
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiClient.uploadResume(file);
      if (response.error) {
        setError(response.error);
        setSuccess(null);
      } else if (response.data) {
        onUploadSuccess(response.data as unknown);
        setSuccess('Resume uploaded successfully. Parsing will continue in the background.');
        setFile(null);
      }
    } catch {
      setError('An unknown error occurred');
      setSuccess(null);
    } finally {
      setUploading(false);
    }
  };
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileChange = createFileChangeHandler(setFile, setError, setSuccess);
  const handleUpload = createUploadHandler({
    fileRef: () => file,
    setUploading,
    setError,
    setSuccess,
    setFile,
    onUploadSuccess,
  });

  return (
    <FileUploadContent
      file={file}
      uploading={uploading}
      error={error}
      success={success}
      onFileChange={handleFileChange}
      onUploadClick={handleUpload}
    />
  );
}
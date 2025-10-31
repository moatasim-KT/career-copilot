'use client';

import { Upload } from 'lucide-react';
import { useState } from 'react';

import { apiClient } from '@/lib/api';

interface FileUploadProps {
  onUploadSuccess: (data: any) => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadResume(file);
      if (response.error) {
        setError(response.error);
      } else {
        onUploadSuccess(response.data);
      }
    } catch (err) {
      setError('An unknown error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors">
      <input type="file" onChange={handleFileChange} className="hidden" id="file-upload" />
      <label htmlFor="file-upload" className="flex flex-col items-center justify-center space-y-2">
        <Upload className="w-12 h-12 text-gray-400" />
        <p className="text-sm text-gray-600">{file ? file.name : 'Click to upload or drag and drop'}</p>
        <p className="text-xs text-gray-500">PDF, DOCX, or TXT (MAX. 5MB)</p>
      </label>
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md disabled:bg-gray-400 flex items-center gap-2 mx-auto"
        >
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploading...' : 'Upload Resume'}
        </button>
      )}
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
}
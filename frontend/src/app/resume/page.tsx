'use client';

import { useState } from 'react';
import FileUpload2 from '@/components/ui/FileUpload2';
import { logger } from '@/lib/logger';

function ResumePage() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const handleFileChange = (files: File[]) => {
    setUploadedFiles(files);
    logger.log('Files selected:', files);
    // Handle file selection, e.g., upload to server
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Upload Your Resume</h1>
      <FileUpload2
        value={uploadedFiles}
        onChange={handleFileChange}
        accept=".pdf,.doc,.docx"
        maxFiles={1}
        helperText="Upload your resume in PDF, DOC, or DOCX format"
      />
    </div>
  );
}

export default ResumePage;

'use client';

import FileUpload from '@/components/ui/FileUpload';
import { logger } from '@/lib/logger';

function ResumePage() {
  const handleUploadSuccess = (data: any) => {
    logger.log('Upload successful:', data);
    // Handle success, e.g., show a success message or update user profile
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Upload Your Resume</h1>
      <FileUpload onUploadSuccess={handleUploadSuccess} />
    </div>
  );
}

export default ResumePage;

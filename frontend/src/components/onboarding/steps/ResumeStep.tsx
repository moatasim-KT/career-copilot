
import React, { useState } from 'react';
import { FileUpload } from '@/components/ui/FileUpload';
import apiClient from '@/lib/api/client';
import { toast }from 'react-hot-toast';

interface ResumeStepProps {
  data: {
    resume?: File;
  };
  onChange: (data: any) => void;
}

const ResumeStep: React.FC<ResumeStepProps> = ({ data, onChange }) => {
  const [isParsing, setIsParsing] = useState(false);

  const handleResumeUpload = async (file: File) => {
    onChange({ resume: file });
    setIsParsing(true);
    try {
      const formData = new FormData();
      formData.append('resume', file);
      const response = await apiClient.post('/resume/parse', formData);
      
      if (response.data?.skills) {
        onChange({ skills: response.data.skills });
        toast.success('Resume parsed and skills updated!');
      }
    } catch (error) {
      toast.error('Failed to parse resume. Please try again.');
      console.error('Resume parsing failed:', error);
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold">Upload Your Resume</h2>
      <p className="mt-2 text-gray-600">
        We can parse your resume to auto-fill your skills.
      </p>
      <div className="mt-8">
        <FileUpload
          label="Upload your resume (PDF or DOCX)"
          onUpload={handleResumeUpload}
          disabled={isParsing}
        />
        {isParsing && <p className="mt-4 text-center">Parsing your resume...</p>}
      </div>
    </div>
  );
};

export default ResumeStep;

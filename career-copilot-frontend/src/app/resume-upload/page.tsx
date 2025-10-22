
'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '@/components/AuthProvider';
import { useNotification } from '@/components/NotificationProvider';

export default function ResumeUploadPage() {
  const { token } = useAuth();
  const { showNotification } = useNotification();
  const [file, setFile] = useState<File | null>(null);
  const [parsingStatus, setParsingStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const uploadedFile = acceptedFiles[0];
      setFile(uploadedFile);
      setParsingStatus(`Uploading ${uploadedFile.name}...`);
      // Simulate upload and parsing
      simulateFileUploadAndParsing(uploadedFile);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  });

  const simulateFileUploadAndParsing = (uploadedFile: File) => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 100) {
          clearInterval(interval);
          setParsingStatus('Parsing complete!');
          showNotification({ message: 'Resume uploaded and parsed successfully!', type: 'success' });
          return 100;
        }
        return prevProgress + 10;
      });
    }, 200);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Resume Upload & Content Generation</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Upload Your Resume</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}`}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop the files here ...</p>
          ) : (
            <p>Drag 'n' drop your resume here, or click to select files (PDF, DOCX, TXT)</p>
          )}
        </div>
        {file && (
          <div className="mt-4">
            <p className="font-medium">Selected file: {file.name}</p>
            <p className="text-sm text-gray-600">Status: {parsingStatus}</p>
            <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
              <div
                className="bg-green-600 h-2.5 rounded-full"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Generate Content</h2>
        {/* Content Generation Forms will go here */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Cover Letter Generator</h3>
          <textarea
            className="w-full p-2 border rounded-md mb-4"
            rows={5}
            placeholder="Paste job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          ></textarea>
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
            onClick={handleGenerateCoverLetter}
          >
            Generate Cover Letter
          </button>
        </div>
        <div className="bg-white shadow-md rounded-lg p-6 mt-4">
          <h3 className="text-xl font-semibold mb-4">Tailored Resume Generator</h3>
          <textarea
            className="w-full p-2 border rounded-md mb-4"
            rows={5}
            placeholder="Paste job description for resume tailoring..."
            value={resumeJobDescription}
            onChange={(e) => setResumeJobDescription(e.target.value)}
          ></textarea>
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
            onClick={handleGenerateTailoredResume}
          >
            Generate Tailored Resume
          </button>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4">Generated Content Preview</h2>
        {/* Content Preview and Editing will go here */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <p>Preview of generated content will appear here.</p>
        </div>
      </section>
    </div>
  );
}

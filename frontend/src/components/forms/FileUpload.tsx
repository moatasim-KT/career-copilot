/**
 * File Upload Component with Drag-and-Drop and Preview
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import React, { useState, useRef, useCallback, ChangeEvent, DragEvent } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface UploadedFile {
    id: string;
    file: File;
    preview?: string;
    progress?: number;
    status: 'pending' | 'uploading' | 'success' | 'error';
    error?: string;
}

interface FileUploadProps {
    accept?: string;
    multiple?: boolean;
    maxSize?: number; // in bytes
    maxFiles?: number;
    onUpload: (files: File[]) => Promise<void> | void;
    onRemove?: (fileId: string) => void;
    className?: string;
    disabled?: boolean;
    showPreview?: boolean;
}

// ============================================================================
// File Upload Component
// ============================================================================

export function FileUpload({
    accept,
    multiple = false,
    maxSize = 10 * 1024 * 1024, // 10MB default
    maxFiles = 10,
    onUpload,
    onRemove,
    className = '',
    disabled = false,
    showPreview = true,
}: FileUploadProps) {
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Format file size for display
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${Math.round(bytes / Math.pow(k, i) * 100) / 100} ${sizes[i]}`;
    };

    // Validate file
    const validateFile = (file: File): string | null => {
        if (maxSize && file.size > maxSize) {
            return `File size exceeds ${formatFileSize(maxSize)}`;
        }

        if (accept) {
            const acceptedTypes = accept.split(',').map(t => t.trim());
            const fileExtension = `.${file.name.split('.').pop()}`;
            const fileMimeType = file.type;

            const isAccepted = acceptedTypes.some(type => {
                if (type.startsWith('.')) {
                    return fileExtension.toLowerCase() === type.toLowerCase();
                }
                if (type.endsWith('/*')) {
                    return fileMimeType.startsWith(type.replace('/*', ''));
                }
                return fileMimeType === type;
            });

            if (!isAccepted) {
                return `File type not accepted. Accepted types: ${accept}`;
            }
        }

        return null;
    };

    // Create file preview
    const createPreview = (file: File): Promise<string | undefined> => {
        return new Promise((resolve) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result as string);
                reader.readAsDataURL(file);
            } else {
                resolve(undefined);
            }
        });
    };

    // Process files
    const processFiles = useCallback(async (fileList: FileList | File[]) => {
        const filesArray = Array.from(fileList);

        // Check max files limit
        if (!multiple && filesArray.length > 1) {
            setError('Only one file is allowed');
            return;
        }

        if (files.length + filesArray.length > maxFiles) {
            setError(`Maximum ${maxFiles} files allowed`);
            return;
        }

        setError(null);

        // Validate and process files
        const uploadedFiles: UploadedFile[] = [];

        for (const file of filesArray) {
            const validationError = validateFile(file);

            if (validationError) {
                setError(validationError);
                continue;
            }

            const preview = showPreview ? await createPreview(file) : undefined;

            uploadedFiles.push({
                id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                file,
                preview,
                status: 'pending',
            });
        }

        if (uploadedFiles.length > 0) {
            setFiles(prev => [...prev, ...uploadedFiles]);

            // Trigger upload
            try {
                await onUpload(uploadedFiles.map(f => f.file));

                // Mark as success
                setFiles(prev =>
                    prev.map(f =>
                        uploadedFiles.find(uf => uf.id === f.id)
                            ? { ...f, status: 'success' as const }
                            : f,
                    ),
                );
            } catch (err) {
                // Mark as error
                setFiles(prev =>
                    prev.map(f =>
                        uploadedFiles.find(uf => uf.id === f.id)
                            ? { ...f, status: 'error' as const, error: err instanceof Error ? err.message : 'Upload failed' }
                            : f,
                    ),
                );
            }
        }
    }, [files.length, maxFiles, multiple, onUpload, showPreview]);

    // Handle file input change
    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files) {
            processFiles(files);
        }
        // Reset input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Handle drag events
    const handleDragEnter = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setIsDragging(true);
        }
    };

    const handleDragLeave = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        if (disabled) return;

        const files = e.dataTransfer.files;
        if (files) {
            processFiles(files);
        }
    };

    // Handle file removal
    const handleRemove = (fileId: string) => {
        setFiles(prev => prev.filter(f => f.id !== fileId));
        onRemove?.(fileId);
    };

    // Open file dialog
    const openFileDialog = () => {
        if (!disabled && fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    return (
        <div className={`file-upload ${className}`}>
            {/* Drop Zone */}
            <div
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={openFileDialog}
                className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={accept}
                    multiple={multiple}
                    onChange={handleFileChange}
                    className="hidden"
                    disabled={disabled}
                />

                <div className="flex flex-col items-center">
                    <svg
                        className={`w-12 h-12 mb-4 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                    </svg>

                    <p className="text-lg font-medium text-gray-700 mb-2">
                        {isDragging ? 'Drop files here' : 'Drag & drop files here'}
                    </p>

                    <p className="text-sm text-gray-500 mb-4">
                        or click to browse
                    </p>

                    {accept && (
                        <p className="text-xs text-gray-400">
                            Accepted formats: {accept}
                        </p>
                    )}

                    {maxSize && (
                        <p className="text-xs text-gray-400">
                            Max size: {formatFileSize(maxSize)}
                        </p>
                    )}
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            {/* File List */}
            {files.length > 0 && (
                <div className="mt-6 space-y-3">
                    <h3 className="text-sm font-medium text-gray-700">
                        Uploaded Files ({files.length})
                    </h3>

                    <AnimatePresence>
                        {files.map((file) => (
                            <motion.div
                                key={file.id}
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, x: -100 }}
                                className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg"
                            >
                                {/* Preview */}
                                {file.preview && (
                                    <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-gray-100">
                                        <img
                                            src={file.preview}
                                            alt={file.file.name}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                )}

                                {/* File Icon (if no preview) */}
                                {!file.preview && (
                                    <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center">
                                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                )}

                                {/* File Info */}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 truncate">
                                        {file.file.name}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {formatFileSize(file.file.size)}
                                    </p>

                                    {/* Status */}
                                    <div className="mt-1">
                                        {file.status === 'success' && (
                                            <span className="text-xs text-green-600 flex items-center">
                                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                                Uploaded
                                            </span>
                                        )}

                                        {file.status === 'error' && (
                                            <span className="text-xs text-red-600">
                                                {file.error || 'Upload failed'}
                                            </span>
                                        )}

                                        {file.status === 'uploading' && (
                                            <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                                                <div
                                                    className="bg-blue-600 h-1.5 rounded-full transition-all"
                                                    style={{ width: `${file.progress || 0}%` }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Remove Button */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleRemove(file.id);
                                    }}
                                    className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 transition-colors"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}

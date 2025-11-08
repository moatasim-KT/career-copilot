'use client';

import { forwardRef, useRef, useState } from 'react';
import { X, UploadCloud, Image as ImageIcon, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FileUpload2Props {
    label?: string;
    value?: File[];
    onChange?: (files: File[]) => void;
    accept?: string;
    multiple?: boolean;
    maxFiles?: number;
    maxSizeMB?: number;
    preview?: boolean;
    error?: string;
    helperText?: string;
    required?: boolean;
    disabled?: boolean;
    className?: string;
}

function isImage(file: File) {
    return file.type.startsWith('image/');
}

export const FileUpload2 = forwardRef<HTMLDivElement, FileUpload2Props>(
    (
        {
            label,
            value = [],
            onChange,
            accept,
            multiple = false,
            maxFiles,
            maxSizeMB,
            preview = true,
            error,
            helperText,
            required = false,
            disabled = false,
            className,
        },
        ref,
    ) => {
        const inputRef = useRef<HTMLInputElement>(null);
        const [dragActive, setDragActive] = useState(false);

        const handleFiles = (files: FileList | null) => {
            if (!files) return;
            let fileArr = Array.from(files);
            if (maxFiles) fileArr = fileArr.slice(0, maxFiles);
            if (maxSizeMB) fileArr = fileArr.filter(f => f.size <= maxSizeMB * 1024 * 1024);
            onChange?.(fileArr);
        };

        const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            setDragActive(false);
            if (disabled) return;
            handleFiles(e.dataTransfer.files);
        };

        const handleRemove = (idx: number) => {
            if (disabled) return;
            const newFiles = value.filter((_, i) => i !== idx);
            onChange?.(newFiles);
        };

        const message = error || helperText;
        const messageColor = error ? 'text-error-600' : 'text-neutral-500';

        return (
            <div ref={ref} className={cn('w-full', className)}>
                {label && (
                    <label className="mb-1.5 block text-sm font-medium text-neutral-700">
                        {label}
                        {required && <span className="ml-1 text-error-500">*</span>}
                    </label>
                )}
                <div
                    className={cn(
                        'relative flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-6 transition-all',
                        dragActive ? 'border-primary-500 bg-primary-50' : 'border-neutral-300 bg-neutral-50',
                        disabled && 'opacity-50 cursor-not-allowed',
                        error && 'border-error-500',
                    )}
                    onDragOver={e => {
                        e.preventDefault();
                        setDragActive(true);
                    }}
                    onDragLeave={e => {
                        e.preventDefault();
                        setDragActive(false);
                    }}
                    onDrop={handleDrop}
                    onClick={() => !disabled && inputRef.current?.click()}
                >
                    <UploadCloud className="h-8 w-8 text-primary-400 mb-2" />
                    <p className="text-sm text-neutral-600 mb-1">Drag & drop files here or <span className="text-primary-600 underline cursor-pointer">browse</span></p>
                    <input
                        ref={inputRef}
                        type="file"
                        accept={accept}
                        multiple={multiple}
                        className="hidden"
                        disabled={disabled}
                        onChange={e => handleFiles(e.target.files)}
                    />
                    {maxFiles && <p className="text-xs text-neutral-400">Max {maxFiles} file(s)</p>}
                    {maxSizeMB && <p className="text-xs text-neutral-400">Max size: {maxSizeMB}MB each</p>}
                </div>
                {/* File previews */}
                {preview && value.length > 0 && (
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                        {value.map((file, idx) => (
                            <div key={idx} className="relative flex items-center gap-3 p-3 border rounded-lg bg-white shadow-sm">
                                {isImage(file) ? (
                                    <img
                                        src={URL.createObjectURL(file)}
                                        alt={file.name}
                                        className="w-16 h-16 object-cover rounded-md border"
                                    />
                                ) : (
                                    <div className="w-16 h-16 flex items-center justify-center bg-neutral-100 rounded-md border">
                                        <FileText className="h-8 w-8 text-neutral-400" />
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">{file.name}</p>
                                    <p className="text-xs text-neutral-400 truncate">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleRemove(idx)}
                                    className="absolute top-2 right-2 text-neutral-400 hover:text-error-500"
                                    tabIndex={-1}
                                >
                                    <X className="h-4 w-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
                {message && <p className={cn('mt-1.5 text-sm', messageColor)}>{message}</p>}
            </div>
        );
    },
);

FileUpload2.displayName = 'FileUpload2';

export default FileUpload2;

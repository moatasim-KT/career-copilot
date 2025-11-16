/**
 * LazyRichTextEditor
 * 
 * Lazy-loaded wrapper for rich text editor components.
 * This component uses dynamic import to code-split heavy editor libraries.
 * 
 * Note: This is a placeholder for future rich text editor integration.
 * Common editors like TipTap, Slate, or Draft.js can be integrated here.
 */

'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Rich text editor skeleton
function RichTextEditorSkeleton() {
  return (
    <div className="w-full border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden animate-pulse">
      {/* Toolbar */}
      <div className="bg-neutral-100 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 p-2">
        <div className="flex items-center space-x-2">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="w-8 h-8 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          ))}
        </div>
      </div>
      
      {/* Editor content area */}
      <div className="p-4 min-h-[200px] space-y-3">
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full"></div>
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6"></div>
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-4/6"></div>
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full"></div>
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4"></div>
      </div>
    </div>
  );
}

// Placeholder for future rich text editor
// When implementing, replace this with actual editor import:
// const RichTextEditor = dynamic(() => import('@tiptap/react'), { ... });

interface LazyRichTextEditorProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

/**
 * Placeholder component for rich text editor.
 * Replace with actual editor implementation when needed.
 */
function RichTextEditorPlaceholder({
  value,
  onChange,
  placeholder = 'Start typing...',
  className = '',
  disabled = false,
}: LazyRichTextEditorProps) {
  return (
    <div className={`w-full border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden ${className}`}>
      {/* Simple toolbar placeholder */}
      <div className="bg-neutral-100 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 p-2">
        <div className="flex items-center space-x-2 text-neutral-400 dark:text-neutral-500 text-sm">
          <span>Rich text editor (to be implemented)</span>
        </div>
      </div>
      
      {/* Simple textarea fallback */}
      <textarea
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full p-4 min-h-[200px] bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none resize-none"
      />
    </div>
  );
}

// Lazy load rich text editor (currently using placeholder)
const RichTextEditor = dynamic(
  () => Promise.resolve({ default: RichTextEditorPlaceholder }),
  {
    loading: () => <RichTextEditorSkeleton />,
    ssr: false, // Rich text editors are client-side only
  },
);

export default function LazyRichTextEditor(props: LazyRichTextEditorProps) {
  return (
    <Suspense fallback={<RichTextEditorSkeleton />}>
      <RichTextEditor {...props} />
    </Suspense>
  );
}

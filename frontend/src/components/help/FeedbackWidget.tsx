/**
 * Feedback Widget Component
 * 
 * A floating feedback button that opens a modal for users to submit feedback.
 * Can be placed in the footer or as a floating action button.
 * 
 * Features:
 * - Rating system (1-5 stars)
 * - Comment field
 * - Optional screenshot capture
 * - Category selection
 * - Thank you message after submission
 * - Accessible and keyboard-friendly
 * 
 * Usage:
 * ```tsx
 * <FeedbackWidget />
 * ```
 */

'use client';

import {
  MessageSquare,
  Star,
  Camera,
  Send,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { useState, useRef } from 'react';

import { Modal2 } from '@/components/ui/Modal2';
import { logger } from '@/lib/logger';
import { m, AnimatePresence } from '@/lib/motion';
import { cn } from '@/lib/utils';

interface FeedbackData {
  rating: number;
  category: string;
  comment: string;
  screenshot?: string;
  url: string;
  userAgent: string;
  timestamp: string;
}

const categories = [
  { id: 'bug', label: 'Bug Report', emoji: '🐛' },
  { id: 'feature', label: 'Feature Request', emoji: '💡' },
  { id: 'improvement', label: 'Improvement', emoji: '✨' },
  { id: 'question', label: 'Question', emoji: '❓' },
  { id: 'other', label: 'Other', emoji: '💬' },
];

export interface FeedbackWidgetProps {
  /**
   * Position of the floating button
   */
  position?: 'bottom-right' | 'bottom-left' | 'inline';

  /**
   * Custom className for the button
   */
  className?: string;

  /**
   * Callback when feedback is submitted
   */
  onSubmit?: (feedback: FeedbackData) => Promise<void>;

  /**
   * Whether to show the screenshot option
   */
  enableScreenshot?: boolean;
}

export function FeedbackWidget({
  position = 'bottom-right',
  className,
  onSubmit,
  enableScreenshot = true,
}: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [category, setCategory] = useState('');
  const [comment, setComment] = useState('');
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleOpen = () => {
    setIsOpen(true);
    // Reset form
    setRating(0);
    setCategory('');
    setComment('');
    setScreenshot(null);
    setIsSubmitted(false);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleScreenshotCapture = async () => {
    // In a real implementation, this would use a library like html2canvas
    // For now, we'll just open the file picker
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setScreenshot(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!rating || !category || !comment.trim()) {
      return;
    }

    setIsSubmitting(true);

    const feedbackData: FeedbackData = {
      rating,
      category,
      comment: comment.trim(),
      screenshot: screenshot || undefined,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    try {
      if (onSubmit) {
        await onSubmit(feedbackData);
      } else {
        // Default: Send to API endpoint
        await fetch('/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(feedbackData),
        });
      }

      setIsSubmitted(true);

      // Auto-close after 2 seconds
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (error) {
      logger.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isFormValid = rating > 0 && category && comment.trim().length > 0;

  const positionStyles = {
    'bottom-right': 'fixed bottom-6 right-6 z-40',
    'bottom-left': 'fixed bottom-6 left-6 z-40',
    'inline': '',
  };

  return (
    <>
      {/* Floating Button */}
      <m.button
        onClick={handleOpen}
        className={cn(
          positionStyles[position],
          'flex items-center gap-2 px-4 py-3 rounded-full',
          'bg-primary-600 hover:bg-primary-700',
          'text-white font-medium',
          'shadow-lg hover:shadow-xl',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          className,
        )}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Send feedback"
      >
        <MessageSquare className="h-5 w-5" />
        <span className="hidden sm:inline">Feedback</span>
      </m.button>

      {/* Feedback Modal */}
      <Modal2
        open={isOpen}
        onClose={handleClose}
        title={isSubmitted ? 'Thank You!' : 'Send Feedback'}
        size="md"
      >
        <AnimatePresence mode="wait">
          {isSubmitted ? (
            // Success State
            <m.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="py-8 text-center"
            >
              <m.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              >
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              </m.div>
              <h3 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                Feedback Received!
              </h3>
              <p className="text-neutral-600 dark:text-neutral-400">
                Thank you for helping us improve Career Copilot.
              </p>
            </m.div>
          ) : (
            // Feedback Form
            <m.form
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onSubmit={handleSubmit}
              className="space-y-6"
            >
              {/* Rating */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  How would you rate your experience? *
                </label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setRating(value)}
                      onMouseEnter={() => setHoveredRating(value)}
                      onMouseLeave={() => setHoveredRating(0)}
                      className={cn(
                        'p-1 rounded transition-transform',
                        'hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary-500',
                      )}
                      aria-label={`Rate ${value} stars`}
                    >
                      <Star
                        className={cn(
                          'h-8 w-8 transition-colors',
                          (hoveredRating || rating) >= value
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-neutral-300 dark:text-neutral-600',
                        )}
                      />
                    </button>
                  ))}
                  {rating > 0 && (
                    <span className="ml-2 text-sm text-neutral-600 dark:text-neutral-400">
                      {rating === 5 && '🎉 Excellent!'}
                      {rating === 4 && '😊 Great!'}
                      {rating === 3 && '🙂 Good'}
                      {rating === 2 && '😕 Could be better'}
                      {rating === 1 && '😞 Needs improvement'}
                    </span>
                  )}
                </div>
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  What type of feedback is this? *
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {categories.map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setCategory(cat.id)}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg',
                        'text-sm font-medium transition-colors',
                        'border-2',
                        category === cat.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                          : 'border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 hover:border-neutral-300 dark:hover:border-neutral-600',
                      )}
                    >
                      <span>{cat.emoji}</span>
                      <span>{cat.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Comment */}
              <div>
                <label
                  htmlFor="feedback-comment"
                  className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2"
                >
                  Tell us more *
                </label>
                <textarea
                  id="feedback-comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={4}
                  placeholder="Share your thoughts, suggestions, or report an issue..."
                  className={cn(
                    'w-full px-3 py-2 rounded-lg',
                    'bg-white dark:bg-neutral-800',
                    'border border-neutral-300 dark:border-neutral-600',
                    'text-neutral-900 dark:text-neutral-100',
                    'placeholder-neutral-500 dark:placeholder-neutral-400',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500',
                    'resize-none',
                  )}
                  required
                />
                <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
                  {comment.length}/500 characters
                </p>
              </div>

              {/* Screenshot */}
              {enableScreenshot && (
                <div>
                  <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Screenshot (optional)
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={handleScreenshotCapture}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-lg',
                        'text-sm font-medium',
                        'bg-neutral-100 dark:bg-neutral-800',
                        'text-neutral-700 dark:text-neutral-300',
                        'hover:bg-neutral-200 dark:hover:bg-neutral-700',
                        'transition-colors',
                      )}
                    >
                      <Camera className="h-4 w-4" />
                      {screenshot ? 'Change Screenshot' : 'Add Screenshot'}
                    </button>
                    {screenshot && (
                      <button
                        type="button"
                        onClick={() => setScreenshot(null)}
                        className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  {screenshot && (
                    <div className="mt-3">
                      <img
                        src={screenshot}
                        alt="Screenshot preview"
                        className="max-w-full h-auto rounded-lg border border-neutral-200 dark:border-neutral-700"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-200 dark:border-neutral-700">
                <button
                  type="button"
                  onClick={handleClose}
                  className={cn(
                    'px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'text-neutral-700 dark:text-neutral-300',
                    'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                    'transition-colors',
                  )}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!isFormValid || isSubmitting}
                  className={cn(
                    'flex items-center gap-2 px-6 py-2 rounded-lg',
                    'text-sm font-medium text-white',
                    'bg-primary-600 hover:bg-primary-700',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  )}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Send Feedback
                    </>
                  )}
                </button>
              </div>
            </m.form>
          )}
        </AnimatePresence>
      </Modal2>
    </>
  );
}

/**
 * Inline Feedback Button
 * 
 * A simpler inline version for use in footers or settings pages
 */
export interface InlineFeedbackButtonProps {
  className?: string;
  onSubmit?: (feedback: FeedbackData) => Promise<void>;
}

export function InlineFeedbackButton({ className, onSubmit }: InlineFeedbackButtonProps) {
  return (
    <FeedbackWidget
      position="inline"
      className={cn(
        'relative',
        'bg-transparent hover:bg-neutral-100 dark:hover:bg-neutral-800',
        'text-neutral-700 dark:text-neutral-300',
        'shadow-none',
        className,
      )}
      onSubmit={onSubmit}
    />
  );
}

/**
 * Feedback Link
 * 
 * A simple text link that opens the feedback modal
 */
export interface FeedbackLinkProps {
  children?: React.ReactNode;
  className?: string;
  onSubmit?: (feedback: FeedbackData) => Promise<void>;
}

export function FeedbackLink({ children = 'Send Feedback', className, onSubmit }: FeedbackLinkProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'text-sm font-medium',
          'text-primary-600 hover:text-primary-700',
          'dark:text-primary-400 dark:hover:text-primary-300',
          'transition-colors',
          className,
        )}
      >
        {children}
      </button>

      <Modal2
        open={isOpen}
        onClose={() => setIsOpen(false)}
        title="Send Feedback"
        size="md"
      >
        <FeedbackWidget
          position="inline"
          onSubmit={onSubmit}
        />
      </Modal2>
    </>
  );
}

/**
 * Hook to manage feedback widget state
 */
export function useFeedbackWidget() {
  const [isOpen, setIsOpen] = useState(false);

  const openFeedback = () => setIsOpen(true);
  const closeFeedback = () => setIsOpen(false);

  return {
    isOpen,
    openFeedback,
    closeFeedback,
  };
}

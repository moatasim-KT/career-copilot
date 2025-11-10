/**
 * PushNotificationPrompt Component
 * Prompts user to enable push notifications with benefits explanation
 */

'use client';

import { Bell, X, Check, Zap, Clock, TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import {
  isPushNotificationSupported,
  getNotificationPermission,
  requestNotificationPermission,
  subscribeToPushNotifications,
  sendSubscriptionToBackend,
  hasUserDismissedPermission,
  markPermissionDismissed,
} from '@/lib/pushNotifications';
import { logger } from '@/lib/logger';
import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';

interface PushNotificationPromptProps {
  userId?: string;
  vapidPublicKey?: string;
  onPermissionGranted?: () => void;
  onPermissionDenied?: () => void;
}

export default function PushNotificationPrompt({
  userId = '1',
  vapidPublicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '',
  onPermissionGranted,
  onPermissionDenied,
}: PushNotificationPromptProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if we should show the prompt
    const shouldShow = () => {
      // Don't show if not supported
      if (!isPushNotificationSupported()) {
        return false;
      }

      // Don't show if user already dismissed
      if (hasUserDismissedPermission()) {
        return false;
      }

      // Don't show if permission already granted or denied
      const permission = getNotificationPermission();
      if (permission.granted || permission.denied) {
        return false;
      }

      return true;
    };

    // Show prompt after a delay (don't be too aggressive)
    const timer = setTimeout(() => {
      if (shouldShow()) {
        setIsVisible(true);
      }
    }, 5000); // Show after 5 seconds

    return () => clearTimeout(timer);
  }, []);

  const handleEnable = async () => {
    setIsLoading(true);

    try {
      // Request permission
      const permission = await requestNotificationPermission();

      if (permission === 'granted') {
        logger.info('Push notification permission granted');

        // Subscribe to push notifications
        if (vapidPublicKey) {
          const subscription = await subscribeToPushNotifications(vapidPublicKey);
          
          // Send subscription to backend
          await sendSubscriptionToBackend(subscription, userId);
        }

        setIsVisible(false);
        onPermissionGranted?.();
      } else {
        logger.warn('Push notification permission denied');
        setIsVisible(false);
        onPermissionDenied?.();
      }
    } catch (error) {
      logger.error('Error enabling push notifications:', error);
      setIsVisible(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDismiss = () => {
    markPermissionDismissed();
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className="fixed bottom-4 right-4 z-50 max-w-md"
      >
        <Card2 className="p-6 shadow-2xl border-2 border-primary-200 dark:border-primary-800">
          {/* Close Button */}
          <button
            onClick={handleDismiss}
            className="absolute top-3 right-3 p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400 transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Icon */}
          <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4">
            <Bell className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>

          {/* Title */}
          <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-2">
            Stay Updated with Push Notifications
          </h3>

          {/* Description */}
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
            Get instant alerts for important updates and never miss an opportunity.
          </p>

          {/* Benefits */}
          <div className="space-y-2 mb-6">
            <div className="flex items-start gap-2">
              <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Instant Job Matches
                </p>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Be the first to know when jobs match your profile
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Zap className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Application Updates
                </p>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Get notified when your application status changes
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Interview Reminders
                </p>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Never miss an interview with timely reminders
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Smart Recommendations
                </p>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Receive personalized job recommendations
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button2
              variant="primary"
              onClick={handleEnable}
              loading={isLoading}
              disabled={isLoading}
              className="flex-1"
            >
              Enable Notifications
            </Button2>
            <Button2
              variant="outline"
              onClick={handleDismiss}
              disabled={isLoading}
            >
              Not Now
            </Button2>
          </div>

          {/* Privacy Note */}
          <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-3 text-center">
            You can change this anytime in settings
          </p>
        </Card2>
      </motion.div>
    </AnimatePresence>
  );
}

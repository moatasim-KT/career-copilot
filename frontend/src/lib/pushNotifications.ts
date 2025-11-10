/**
 * Push Notifications Service
 * Handles browser push notification permissions and subscriptions
 */

import { logger } from './logger';

export interface PushNotificationPermission {
  granted: boolean;
  denied: boolean;
  prompt: boolean;
}

/**
 * Check if push notifications are supported
 */
export function isPushNotificationSupported(): boolean {
  return (
    'Notification' in window &&
    'serviceWorker' in navigator &&
    'PushManager' in window
  );
}

/**
 * Get current notification permission status
 */
export function getNotificationPermission(): PushNotificationPermission {
  if (!isPushNotificationSupported()) {
    return { granted: false, denied: true, prompt: false };
  }

  const permission = Notification.permission;
  return {
    granted: permission === 'granted',
    denied: permission === 'denied',
    prompt: permission === 'default',
  };
}

/**
 * Request notification permission from user
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!isPushNotificationSupported()) {
    throw new Error('Push notifications are not supported in this browser');
  }

  try {
    const permission = await Notification.requestPermission();
    logger.info('Notification permission:', permission);
    return permission;
  } catch (error) {
    logger.error('Error requesting notification permission:', error);
    throw error;
  }
}

/**
 * Register service worker for push notifications
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration> {
  if (!('serviceWorker' in navigator)) {
    throw new Error('Service workers are not supported in this browser');
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });
    
    logger.info('Service worker registered:', registration);
    
    // Wait for service worker to be ready
    await navigator.serviceWorker.ready;
    
    return registration;
  } catch (error) {
    logger.error('Error registering service worker:', error);
    throw error;
  }
}

/**
 * Subscribe to push notifications
 */
export async function subscribeToPushNotifications(
  vapidPublicKey: string
): Promise<PushSubscription> {
  if (!isPushNotificationSupported()) {
    throw new Error('Push notifications are not supported');
  }

  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    throw new Error('Notification permission not granted');
  }

  try {
    const registration = await registerServiceWorker();
    
    // Check if already subscribed
    let subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      logger.info('Already subscribed to push notifications');
      return subscription;
    }

    // Subscribe to push notifications
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });

    logger.info('Subscribed to push notifications:', subscription);
    return subscription;
  } catch (error) {
    logger.error('Error subscribing to push notifications:', error);
    throw error;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPushNotifications(): Promise<boolean> {
  if (!isPushNotificationSupported()) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      const success = await subscription.unsubscribe();
      logger.info('Unsubscribed from push notifications:', success);
      return success;
    }

    return false;
  } catch (error) {
    logger.error('Error unsubscribing from push notifications:', error);
    return false;
  }
}

/**
 * Get current push subscription
 */
export async function getPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushNotificationSupported()) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription;
  } catch (error) {
    logger.error('Error getting push subscription:', error);
    return null;
  }
}

/**
 * Send push subscription to backend
 */
export async function sendSubscriptionToBackend(
  subscription: PushSubscription,
  userId: string
): Promise<void> {
  try {
    const response = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        subscription: subscription.toJSON(),
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send subscription to backend');
    }

    logger.info('Subscription sent to backend');
  } catch (error) {
    logger.error('Error sending subscription to backend:', error);
    throw error;
  }
}

/**
 * Show a test notification
 */
export async function showTestNotification(): Promise<void> {
  if (!isPushNotificationSupported()) {
    throw new Error('Notifications are not supported');
  }

  const permission = getNotificationPermission();
  if (!permission.granted) {
    throw new Error('Notification permission not granted');
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    
    await registration.showNotification('Test Notification', {
      body: 'This is a test notification from Career Copilot',
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      tag: 'test-notification',
      requireInteraction: false,
      actions: [
        {
          action: 'view',
          title: 'View',
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
        },
      ],
    });

    logger.info('Test notification shown');
  } catch (error) {
    logger.error('Error showing test notification:', error);
    throw error;
  }
}

/**
 * Convert VAPID key from base64 to Uint8Array
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}

/**
 * Handle notification click event
 */
export function setupNotificationClickHandler(): void {
  if (!('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'notification-click') {
      const { action, url } = event.data;
      
      logger.info('Notification clicked:', { action, url });

      if (url) {
        window.open(url, '_blank');
      }
    }
  });
}

/**
 * Check if user has previously dismissed permission request
 */
export function hasUserDismissedPermission(): boolean {
  return localStorage.getItem('push-permission-dismissed') === 'true';
}

/**
 * Mark that user has dismissed permission request
 */
export function markPermissionDismissed(): void {
  localStorage.setItem('push-permission-dismissed', 'true');
}

/**
 * Clear permission dismissed flag
 */
export function clearPermissionDismissed(): void {
  localStorage.removeItem('push-permission-dismissed');
}

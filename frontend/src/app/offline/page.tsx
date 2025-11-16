/**
 * Offline Page
 * 
 * Displayed when the user is offline and tries to access a page
 * that isn't cached by the service worker
 */

import OfflinePageContent from '@/components/pages/OfflinePageContent';

export const metadata = {
    title: 'You are offline - Career Copilot',
    description: 'This page requires an internet connection',
};

export default function OfflinePage() {
    return <OfflinePageContent />;
}

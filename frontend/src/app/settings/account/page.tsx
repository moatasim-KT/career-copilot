/**
 * Account Settings Page
 * 
 * Allows users to manage account security:
 * - Change password
 * - Two-factor authentication (future)
 * - Connected accounts (LinkedIn, Google)
 * - Active sessions
 * - Log out all devices
 */

'use client';

import { useState } from 'react';
import {
  Key,
  Shield,
  Link as LinkIcon,
  Monitor,
  LogOut,
  Save,
  Eye,
  EyeOff,
  Check,
  X,
} from 'lucide-react';
import { motion } from 'framer-motion';

import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import Input2 from '@/components/ui/Input2';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';

interface Session {
  id: string;
  device: string;
  location: string;
  lastActive: string;
  current: boolean;
}

const mockSessions: Session[] = [
  {
    id: '1',
    device: 'Chrome on macOS',
    location: 'San Francisco, CA',
    lastActive: 'Active now',
    current: true,
  },
  {
    id: '2',
    device: 'Safari on iPhone',
    location: 'San Francisco, CA',
    lastActive: '2 hours ago',
    current: false,
  },
  {
    id: '3',
    device: 'Firefox on Windows',
    location: 'New York, NY',
    lastActive: '1 day ago',
    current: false,
  },
];

interface ConnectedAccount {
  id: string;
  provider: 'google' | 'linkedin' | 'github';
  email: string;
  connected: boolean;
}

const connectedAccounts: ConnectedAccount[] = [
  { id: '1', provider: 'google', email: 'john.doe@gmail.com', connected: false },
  { id: '2', provider: 'linkedin', email: 'john.doe@linkedin.com', connected: false },
  { id: '3', provider: 'github', email: 'johndoe@github.com', connected: false },
];

export default function AccountSettingsPage() {
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [sessions, setSessions] = useState<Session[]>(mockSessions);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>(connectedAccounts);

  const passwordStrength = (password: string): { strength: number; label: string; color: string } => {
    if (!password) return { strength: 0, label: '', color: '' };
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;

    if (strength <= 2) return { strength, label: 'Weak', color: 'text-red-600 dark:text-red-400' };
    if (strength <= 3) return { strength, label: 'Fair', color: 'text-yellow-600 dark:text-yellow-400' };
    if (strength <= 4) return { strength, label: 'Good', color: 'text-blue-600 dark:text-blue-400' };
    return { strength, label: 'Strong', color: 'text-green-600 dark:text-green-400' };
  };

  const handlePasswordChange = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    setIsChangingPassword(true);

    try {
      await apiClient.user.changePassword(
        passwordData.currentPassword,
        passwordData.newPassword
      );

      // Reset form
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      // Show success message
      console.log('Password changed successfully');
    } catch (error) {
      console.error('Failed to change password:', error);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleLogoutSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    console.log('Logged out session:', sessionId);
  };

  const handleLogoutAllDevices = () => {
    if (confirm('Are you sure you want to log out of all devices? You will need to log in again.')) {
      setSessions(prev => prev.filter(s => s.current));
      console.log('Logged out of all devices');
    }
  };

  const handleConnectAccount = (accountId: string) => {
    setAccounts(prev =>
      prev.map(acc =>
        acc.id === accountId ? { ...acc, connected: !acc.connected } : acc
      )
    );
  };

  const strength = passwordStrength(passwordData.newPassword);
  const passwordsMatch = passwordData.newPassword && passwordData.newPassword === passwordData.confirmPassword;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Account Settings
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Manage your account security and authentication
        </p>
      </div>

      {/* Change Password */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
            <Key className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Change Password
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Update your password to keep your account secure
            </p>
          </div>
        </div>

        <div className="space-y-4 pl-16">
          {/* Current Password */}
          <div>
            <label htmlFor="currentPassword" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Current Password
            </label>
            <div className="relative">
              <Input2
                id="currentPassword"
                type={showPasswords.current ? 'text' : 'password'}
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                placeholder="Enter current password"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
              >
                {showPasswords.current ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              New Password
            </label>
            <div className="relative">
              <Input2
                id="newPassword"
                type={showPasswords.new ? 'text' : 'password'}
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                placeholder="Enter new password"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
              >
                {showPasswords.new ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {passwordData.newPassword && (
              <div className="mt-2">
                <div className="flex items-center gap-2 mb-1">
                  <div className="flex-1 h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(strength.strength / 5) * 100}%` }}
                      className={cn(
                        'h-full transition-colors',
                        strength.strength <= 2 && 'bg-red-500',
                        strength.strength === 3 && 'bg-yellow-500',
                        strength.strength === 4 && 'bg-blue-500',
                        strength.strength === 5 && 'bg-green-500'
                      )}
                    />
                  </div>
                  <span className={cn('text-xs font-medium', strength.color)}>
                    {strength.label}
                  </span>
                </div>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Use at least 8 characters with a mix of letters, numbers, and symbols
                </p>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Confirm New Password
            </label>
            <div className="relative">
              <Input2
                id="confirmPassword"
                type={showPasswords.confirm ? 'text' : 'password'}
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                placeholder="Confirm new password"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
              >
                {showPasswords.confirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              {passwordData.confirmPassword && (
                <div className="absolute right-10 top-1/2 -translate-y-1/2">
                  {passwordsMatch ? (
                    <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                  ) : (
                    <X className="w-4 h-4 text-red-600 dark:text-red-400" />
                  )}
                </div>
              )}
            </div>
          </div>

          <Button2
            variant="primary"
            onClick={handlePasswordChange}
            disabled={
              !passwordData.currentPassword ||
              !passwordData.newPassword ||
              !passwordsMatch ||
              isChangingPassword
            }
            loading={isChangingPassword}
          >
            <Save className="w-4 h-4 mr-2" />
            {isChangingPassword ? 'Changing...' : 'Change Password'}
          </Button2>
        </div>
      </Card2>

      {/* Two-Factor Authentication */}
      <Card2 className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
              <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                Two-Factor Authentication
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Add an extra layer of security to your account (Coming Soon)
              </p>
            </div>
          </div>
          <Button2 variant="outline" size="sm" disabled>
            Enable 2FA
          </Button2>
        </div>
      </Card2>

      {/* Connected Accounts */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
            <LinkIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Connected Accounts
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Link your accounts for easier sign-in and data import
            </p>
          </div>
        </div>

        <div className="space-y-3 pl-16">
          {accounts.map(account => (
            <div
              key={account.id}
              className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center',
                  account.provider === 'google' && 'bg-red-100 dark:bg-red-900/30',
                  account.provider === 'linkedin' && 'bg-blue-100 dark:bg-blue-900/30',
                  account.provider === 'github' && 'bg-neutral-100 dark:bg-neutral-800'
                )}>
                  <span className="text-lg font-bold">
                    {account.provider === 'google' && 'G'}
                    {account.provider === 'linkedin' && 'in'}
                    {account.provider === 'github' && 'GH'}
                  </span>
                </div>
                <div>
                  <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 capitalize">
                    {account.provider}
                  </div>
                  <div className="text-xs text-neutral-600 dark:text-neutral-400">
                    {account.connected ? account.email : 'Not connected'}
                  </div>
                </div>
              </div>
              <Button2
                variant={account.connected ? 'outline' : 'primary'}
                size="sm"
                onClick={() => handleConnectAccount(account.id)}
              >
                {account.connected ? 'Disconnect' : 'Connect'}
              </Button2>
            </div>
          ))}
        </div>
      </Card2>

      {/* Active Sessions */}
      <Card2 className="p-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center flex-shrink-0">
              <Monitor className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                Active Sessions
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Manage devices where you're currently logged in
              </p>
            </div>
          </div>
          <Button2
            variant="outline"
            size="sm"
            onClick={handleLogoutAllDevices}
          >
            <LogOut className="w-4 h-4 mr-2" />
            Log out all
          </Button2>
        </div>

        <div className="space-y-3 pl-16">
          {sessions.map(session => (
            <div
              key={session.id}
              className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <Monitor className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                <div>
                  <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    {session.device}
                    {session.current && (
                      <span className="ml-2 text-xs text-green-600 dark:text-green-400 font-normal">
                        (Current)
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-neutral-600 dark:text-neutral-400">
                    {session.location} • {session.lastActive}
                  </div>
                </div>
              </div>
              {!session.current && (
                <Button2
                  variant="ghost"
                  size="sm"
                  onClick={() => handleLogoutSession(session.id)}
                >
                  <LogOut className="w-4 h-4" />
                </Button2>
              )}
            </div>
          ))}
        </div>
      </Card2>
    </div>
  );
}

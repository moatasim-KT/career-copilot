/**
 * Data Settings Page
 * 
 * Allows users to manage their data:
 * - Export data (links to task 20.5)
 * - Delete specific data types (applications, jobs)
 * - Delete account with confirmation
 * - 30-day grace period before permanent deletion
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  Download,
  Trash2,
  AlertTriangle,
  Database,
  FileText,
  Briefcase,
  Upload,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { useState, useRef } from 'react';

import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import Input2 from '@/components/ui/Input2';
import { logger } from '@/lib/logger';

interface DeleteConfirmation {
  type: 'applications' | 'jobs' | 'account' | null;
  email: string;
  confirmText: string;
}

interface RestoreData {
  profile?: any;
  applications?: any[];
  jobs?: any[];
  preferences?: any;
}

interface RestorePreview {
  profile: boolean;
  applications: number;
  jobs: number;
  preferences: boolean;
}

export default function DataSettingsPage() {
  const [deleteConfirmation, setDeleteConfirmation] = useState<DeleteConfirmation>({
    type: null,
    email: '',
    confirmText: '',
  });
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteAccount, setShowDeleteAccount] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [restoreData, setRestoreData] = useState<RestoreData | null>(null);
  const [restorePreview, setRestorePreview] = useState<RestorePreview | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [restoreSuccess, setRestoreSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const userEmail = 'john.doe@example.com'; // In production, get from auth context

  const handleExportData = async (type: 'all' | 'applications' | 'jobs') => {
    logger.info('Exporting data:', type);
    // In production, this would call the export API from task 20.5
    // await apiClient.data.export(type);
  };

  const handleRestoreClick = () => {
    setShowRestoreModal(true);
    setRestoreError(null);
    setRestoreSuccess(false);
  };

  const handleFileSelect = async (file: File) => {
    setRestoreFile(file);
    setRestoreError(null);

    try {
      const text = await file.text();
      const data: RestoreData = JSON.parse(text);

      // Validate the backup file structure
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid backup file format');
      }

      setRestoreData(data);

      // Generate preview
      const preview: RestorePreview = {
        profile: !!data.profile,
        applications: data.applications?.length || 0,
        jobs: data.jobs?.length || 0,
        preferences: !!data.preferences,
      };

      setRestorePreview(preview);
    } catch (error) {
      logger.error('Failed to parse backup file:', error);
      setRestoreError('Invalid backup file. Please select a valid JSON backup file.');
      setRestoreFile(null);
      setRestoreData(null);
      setRestorePreview(null);
    }
  };

  const handleRestore = async () => {
    if (!restoreData) return;

    setIsRestoring(true);
    setRestoreError(null);

    try {
      // In production, this would call the restore API
      // await apiClient.data.restore(restoreData);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      logger.info('Restoring data:', restoreData);

      setRestoreSuccess(true);

      // Reset after success
      setTimeout(() => {
        setShowRestoreModal(false);
        setRestoreFile(null);
        setRestoreData(null);
        setRestorePreview(null);
        setRestoreSuccess(false);
      }, 2000);
    } catch (error) {
      logger.error('Failed to restore data:', error);
      setRestoreError('Failed to restore data. Please try again.');
    } finally {
      setIsRestoring(false);
    }
  };

  const handleDeleteData = async (type: 'applications' | 'jobs') => {
    setDeleteConfirmation({ type, email: '', confirmText: '' });
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmation.type) return;

    setIsDeleting(true);

    try {
      if (deleteConfirmation.type === 'account') {
        // Delete account
        // await apiClient.user.deleteAccount();
        logger.info('Account deletion initiated');
      } else {
        // Delete specific data type
        // await apiClient.data.delete(deleteConfirmation.type);
        logger.info('Deleted data:', deleteConfirmation.type);
      }

      setDeleteConfirmation({ type: null, email: '', confirmText: '' });
      setShowDeleteAccount(false);
    } catch (error) {
      logger.error('Failed to delete data:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const canConfirmDelete =
    deleteConfirmation.type === 'account'
      ? deleteConfirmation.email === userEmail
      : deleteConfirmation.confirmText.toLowerCase() === 'delete';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Data Management
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Export, manage, or delete your data
        </p>
      </div>

      {/* Export Data */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
            <Download className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Export Your Data
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Download a copy of your data in JSON format
            </p>
          </div>
        </div>

        <div className="space-y-3 pl-16">
          <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  All Data
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Complete backup of your profile, applications, and saved jobs
                </div>
              </div>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => handleExportData('all')}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button2>
          </div>

          <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Applications Only
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Export all your job applications
                </div>
              </div>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => handleExportData('applications')}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button2>
          </div>

          <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Briefcase className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Saved Jobs Only
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Export all your saved job listings
                </div>
              </div>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => handleExportData('jobs')}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button2>
          </div>
        </div>
      </Card2>

      {/* Restore from Backup */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
            <Upload className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Restore from Backup
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Upload a backup file to restore your data
            </p>
          </div>
        </div>

        <div className="pl-16">
          <div className="p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
                <div>
                  <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    Upload Backup File
                  </div>
                  <div className="text-xs text-neutral-600 dark:text-neutral-400">
                    Restore your profile, applications, and saved jobs from a backup
                  </div>
                </div>
              </div>
              <Button2
                variant="outline"
                size="sm"
                onClick={handleRestoreClick}
              >
                <Upload className="w-4 h-4 mr-2" />
                Restore
              </Button2>
            </div>
          </div>
        </div>
      </Card2>

      {/* Delete Specific Data */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center flex-shrink-0">
            <Trash2 className="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Delete Specific Data
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Permanently delete specific types of data
            </p>
          </div>
        </div>

        <div className="space-y-3 pl-16">
          <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  All Applications
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Delete all your job applications
                </div>
              </div>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => handleDeleteData('applications')}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button2>
          </div>

          <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Briefcase className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  All Saved Jobs
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Delete all your saved job listings
                </div>
              </div>
            </div>
            <Button2
              variant="outline"
              size="sm"
              onClick={() => handleDeleteData('jobs')}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button2>
          </div>
        </div>
      </Card2>

      {/* Delete Account */}
      <Card2 className="p-6 border-red-200 dark:border-red-800">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Delete Account
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Permanently delete your account and all associated data
            </p>

            {!showDeleteAccount ? (
              <Button2
                variant="destructive"
                size="sm"
                onClick={() => setShowDeleteAccount(true)}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Account
              </Button2>
            ) : (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4"
              >
                <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-red-900 dark:text-red-100">
                      <p className="font-semibold mb-2">Warning: This action cannot be undone</p>
                      <ul className="list-disc list-inside space-y-1 text-red-800 dark:text-red-200">
                        <li>All your data will be permanently deleted</li>
                        <li>You will have a 30-day grace period to cancel</li>
                        <li>After 30 days, deletion is irreversible</li>
                        <li>You will be logged out immediately</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmEmail" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                    Type your email address to confirm: <span className="font-mono text-primary-600 dark:text-primary-400">{userEmail}</span>
                  </label>
                  <Input2
                    id="confirmEmail"
                    type="email"
                    value={deleteConfirmation.email}
                    onChange={(e) => setDeleteConfirmation(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="your.email@example.com"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <Button2
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setShowDeleteAccount(false);
                      setDeleteConfirmation({ type: null, email: '', confirmText: '' });
                    }}
                  >
                    Cancel
                  </Button2>
                  <Button2
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      setDeleteConfirmation(prev => ({ ...prev, type: 'account' }));
                      handleConfirmDelete();
                    }}
                    disabled={deleteConfirmation.email !== userEmail || isDeleting}
                    loading={isDeleting}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {isDeleting ? 'Deleting...' : 'Delete My Account'}
                  </Button2>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </Card2>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteConfirmation.type && deleteConfirmation.type !== 'account' && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
              onClick={() => setDeleteConfirmation({ type: null, email: '', confirmText: '' })}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white dark:bg-neutral-900 rounded-lg shadow-xl max-w-md w-full p-6"
              >
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                    <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                      Delete {deleteConfirmation.type === 'applications' ? 'Applications' : 'Saved Jobs'}?
                    </h3>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      This action cannot be undone. All your {deleteConfirmation.type} will be permanently deleted.
                    </p>
                  </div>
                </div>

                <div className="mb-6">
                  <label htmlFor="confirmText" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                    Type <span className="font-mono text-red-600 dark:text-red-400">DELETE</span> to confirm
                  </label>
                  <Input2
                    id="confirmText"
                    value={deleteConfirmation.confirmText}
                    onChange={(e) => setDeleteConfirmation(prev => ({ ...prev, confirmText: e.target.value }))}
                    placeholder="DELETE"
                  />
                </div>

                <div className="flex items-center justify-end gap-3">
                  <Button2
                    variant="outline"
                    onClick={() => setDeleteConfirmation({ type: null, email: '', confirmText: '' })}
                    disabled={isDeleting}
                  >
                    Cancel
                  </Button2>
                  <Button2
                    variant="destructive"
                    onClick={handleConfirmDelete}
                    disabled={!canConfirmDelete || isDeleting}
                    loading={isDeleting}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button2>
                </div>
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Restore Modal */}
      <AnimatePresence>
        {showRestoreModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
              onClick={() => {
                if (!isRestoring) {
                  setShowRestoreModal(false);
                  setRestoreFile(null);
                  setRestoreData(null);
                  setRestorePreview(null);
                  setRestoreError(null);
                }
              }}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white dark:bg-neutral-900 rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
              >
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
                    <Upload className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                      Restore from Backup
                    </h3>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      Upload a backup file to restore your data
                    </p>
                  </div>
                </div>

                {/* File Upload */}
                {!restoreFile && (
                  <div
                    className="border-2 border-dashed border-neutral-300 dark:border-neutral-700 rounded-lg p-12 text-center hover:border-green-500 dark:hover:border-green-400 transition-colors cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-12 w-12 text-neutral-400 dark:text-neutral-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                      Upload Backup File
                    </h3>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
                      Drag and drop your backup file here, or click to browse
                    </p>
                    <Button2 variant="outline" size="sm">
                      <FileText className="h-4 w-4 mr-2" />
                      Select File
                    </Button2>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".json"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleFileSelect(file);
                        }
                      }}
                    />
                  </div>
                )}

                {/* File Info and Preview */}
                {restoreFile && restorePreview && !restoreSuccess && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    <div className="p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <FileText className="h-5 w-5 text-green-500" />
                          <div>
                            <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                              {restoreFile.name}
                            </p>
                            <p className="text-xs text-neutral-600 dark:text-neutral-400">
                              {(restoreFile.size / 1024).toFixed(2)} KB
                            </p>
                          </div>
                        </div>
                        <Button2
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setRestoreFile(null);
                            setRestoreData(null);
                            setRestorePreview(null);
                            if (fileInputRef.current) {
                              fileInputRef.current.value = '';
                            }
                          }}
                          disabled={isRestoring}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button2>
                      </div>

                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                          Preview - What will be restored:
                        </h4>
                        <div className="space-y-2">
                          {restorePreview.profile && (
                            <div className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span>Profile information</span>
                            </div>
                          )}
                          {restorePreview.applications > 0 && (
                            <div className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span>{restorePreview.applications} application(s)</span>
                            </div>
                          )}
                          {restorePreview.jobs > 0 && (
                            <div className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span>{restorePreview.jobs} saved job(s)</span>
                            </div>
                          )}
                          {restorePreview.preferences && (
                            <div className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span>User preferences</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-yellow-900 dark:text-yellow-100">
                          <p className="font-semibold mb-1">Important</p>
                          <ul className="list-disc list-inside space-y-1 text-yellow-800 dark:text-yellow-200">
                            <li>Existing data will be merged with restored data</li>
                            <li>Duplicate entries may be created</li>
                            <li>This action cannot be undone</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Success Message */}
                {restoreSuccess && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-8"
                  >
                    <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                      Restore Complete!
                    </h3>
                    <p className="text-neutral-600 dark:text-neutral-400">
                      Your data has been successfully restored
                    </p>
                  </motion.div>
                )}

                {/* Error Message */}
                {restoreError && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="flex items-center gap-3">
                      <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                      <p className="text-sm text-red-800 dark:text-red-200">{restoreError}</p>
                    </div>
                  </div>
                )}

                {/* Actions */}
                {!restoreSuccess && (
                  <div className="flex items-center justify-end gap-3 mt-6">
                    <Button2
                      variant="outline"
                      onClick={() => {
                        setShowRestoreModal(false);
                        setRestoreFile(null);
                        setRestoreData(null);
                        setRestorePreview(null);
                        setRestoreError(null);
                      }}
                      disabled={isRestoring}
                    >
                      Cancel
                    </Button2>
                    {restoreFile && restorePreview && (
                      <Button2
                        onClick={handleRestore}
                        disabled={isRestoring}
                        loading={isRestoring}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {isRestoring ? 'Restoring...' : 'Restore Data'}
                      </Button2>
                    )}
                  </div>
                )}
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

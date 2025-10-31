'use client';

import { useState, useEffect } from 'react';

import { apiClient, UserProfile } from '@/lib/api';
import { logger } from '@/lib/logger';

import Card from '../ui/Card';
import FileUpload from '../ui/FileUpload';

export default function ProfilePage() {
  const [profile, setProfile] = useState<Partial<UserProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      const response = await apiClient.getUserProfile();
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setProfile(response.data);
      }
      setLoading(false);
    };
    fetchProfile();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
  };

  const handleUploadSuccess = (data: any) => {
    // Handle resume upload success
    logger.log('Upload successful:', data);
  };

  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const response = await apiClient.updateUserProfile(profile);
    if (response.error) {
      setError(response.error);
      setSuccessMessage(null);
    } else {
      setSuccessMessage('Profile updated successfully!');
      setError(null);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">User Information</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
            <input
              type="text"
              name="full_name"
              id="full_name"
              value={profile.full_name || ''}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              id="email"
              value={profile.email || ''}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="experience_level" className="block text-sm font-medium text-gray-700">Experience Level</label>
            <input
              type="text"
              name="experience_level"
              id="experience_level"
              value={profile.experience_level || ''}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700">Preferred Location</label>
            <input
              type="text"
              name="location"
              id="location"
              value={profile.location || ''}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="skills" className="block text-sm font-medium text-gray-700">Skills (comma-separated)</label>
            <input
              type="text"
              name="skills"
              id="skills"
              value={profile.skills?.join(', ') || ''}
              onChange={(e) => setProfile(prev => ({ ...prev, skills: e.target.value.split(',').map(s => s.trim()) }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded-md">Save Profile</button>
          {successMessage && <p className="text-green-500 text-sm mt-2">{successMessage}</p>}
        </form>
      </Card>
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Upload Resume</h2>
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      </Card>
    </div>
  );
}
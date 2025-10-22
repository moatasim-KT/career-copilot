'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getUserProfile, updateUserProfile } from '@/lib/profile';
import { allPossibleSkills, allPossibleLocations } from '@/lib/constants';

interface UserProfileData {
  id: number;
  username: string;
  email: string;
  skills: string[];
  preferred_locations: string[];
  experience_level: 'junior' | 'mid' | 'senior';
  daily_application_goal: number;
}

export default function ProfilePage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedExperience, setSelectedExperience] = useState<'junior' | 'mid' | 'senior'>('mid');
  const [dailyApplicationGoal, setDailyApplicationGoal] = useState(10);

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  useEffect(() => {
    if (token) {
      const fetchProfile = async () => {
        setLoading(true);
        const response = await getUserProfile(token);
        if (response.error) {
          setError(response.error);
          // If token is invalid, redirect to login
          if (response.error.includes('Invalid authentication token') || response.error.includes('Authentication required')) {
            localStorage.removeItem('auth_token');
            router.push('/login');
          }
        } else {
          setProfile(response);
          setSelectedSkills(response.skills || []);
          setSelectedLocations(response.preferred_locations || []);
          setSelectedExperience(response.experience_level || 'mid');
          setDailyApplicationGoal(response.daily_application_goal || 10);
        }
        setLoading(false);
      };
      fetchProfile();
    }
  }, [token, router]);

  const handleUpdateProfile = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);

    const updatedData = {
      skills: selectedSkills,
      preferred_locations: selectedLocations,
      experience_level: selectedExperience,
      daily_application_goal: dailyApplicationGoal,
    };

    const response = await updateUserProfile(token, updatedData);
    if (response.error) {
      setError(response.error);
    } else {
      setProfile(response);
      setIsEditing(false);
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  if (!profile) {
    return <div className="min-h-screen flex items-center justify-center">No profile data found.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">User Profile</h1>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Account Information</h2>
        <p><strong>Username:</strong> {profile.username}</p>
        <p><strong>Email:</strong> {profile.email}</p>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Professional Details</h2>
        {!isEditing ? (
          <div>
            <p><strong>Skills:</strong> {profile.skills?.join(', ') || 'N/A'}</p>
            <p><strong>Preferred Locations:</strong> {profile.preferred_locations?.join(', ') || 'N/A'}</p>
            <p><strong>Experience Level:</strong> {profile.experience_level || 'N/A'}</p>
            <p><strong>Daily Application Goal:</strong> {profile.daily_application_goal || 'N/A'}</p>
            <button
              onClick={() => setIsEditing(true)}
              className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              Edit Profile
            </button>
          </div>
        ) : (
          <div>
            <div className="mb-4">
              <label htmlFor="skills" className="block text-gray-700 text-sm font-bold mb-2">Skills</label>
              <select
                id="skills"
                multiple
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
                value={selectedSkills}
                onChange={(e) => setSelectedSkills(Array.from(e.target.options).filter(option => option.selected).map(option => option.value))}
              >
                {allPossibleSkills.map((skill) => (
                  <option key={skill} value={skill}>{skill}</option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label htmlFor="locations" className="block text-gray-700 text-sm font-bold mb-2">Preferred Locations</label>
              <select
                id="locations"
                multiple
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
                value={selectedLocations}
                onChange={(e) => setSelectedLocations(Array.from(e.target.options).filter(option => option.selected).map(option => option.value))}
              >
                {allPossibleLocations.map((location) => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label htmlFor="experience" className="block text-gray-700 text-sm font-bold mb-2">Experience Level</label>
              <select
                id="experience"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                value={selectedExperience}
                onChange={(e) => setSelectedExperience(e.target.value as 'junior' | 'mid' | 'senior')}
              >
                <option value="junior">Junior</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
              </select>
            </div>
            <div className="mb-4">
              <label htmlFor="dailyGoal" className="block text-gray-700 text-sm font-bold mb-2">Daily Application Goal</label>
              <input
                type="number"
                id="dailyGoal"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                value={dailyApplicationGoal}
                onChange={(e) => setDailyApplicationGoal(parseInt(e.target.value))}
                min="1"
                max="50"
              />
            </div>
            {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setIsEditing(false)}
                className="mt-4 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateProfile}
                className="mt-4 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
